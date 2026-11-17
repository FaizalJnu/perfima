"use strict";

// Browser UI for Perfima. It talks to the API on the same origin.
// Amounts travel as decimal strings ("12.50") and are summed here as integer cents, never as floats.

const HEARTBEAT_MS = 30000;
const TREND_MONTHS = 12;
// three extra months so even the oldest charted month has a 3 month average to compare against
const TREND_FETCH_MONTHS = TREND_MONTHS + 3;
const TOP_CATEGORIES = 3;
const NEW_CATEGORY = "__new__";
const TOKEN_KEY = "perfima.token";
const TABS = ["add", "history", "insights"];

const state = {
  mode: null,            // "local" (desktop launcher) or "server" (login with a password)
  token: null,
  categories: [],
  transactions: [],
  justAdded: new Set(),
  trend: null,
  trendStale: true,
  selectedMonth: null,
  tab: "add",
  editingId: null,
  historyMonth: null,
  historyCategory: "",
  defaultDate: null,
  heartbeatTimer: null,
};

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

// ---------- DOM helpers

const $ = (selector) => document.querySelector(selector);
const SVG_NS = "http://www.w3.org/2000/svg";

function append(node, children) {
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : String(child));
  }
  return node;
}

function h(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (key in node) node[key] = value;
    else node.setAttribute(key, value === true ? "" : value);
  }
  return append(node, children);
}

function svg(tag, attrs = {}, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined) continue;
    if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value);
  }
  return append(node, children);
}

// ---------- money and dates

function toCents(value) {
  const text = String(value).trim();
  if (/e/i.test(text)) return Math.round(Number(text) * 100);
  const negative = text.startsWith("-");
  const [whole, fraction = ""] = text.replace(/^[-+]/, "").split(".");
  const cents = Number(whole || "0") * 100 + Number((fraction + "00").slice(0, 2));
  return negative ? -cents : cents;
}

const moneyFormat = new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const compactFormat = new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 });

const formatCents = (cents) => moneyFormat.format(cents / 100);
const formatMoney = (value) => formatCents(toCents(value));

// Accepts "12", "12.5", "12,50" or "1,200.50" and returns a decimal string the API accepts, or null
function parseAmount(input, { allowZero = false } = {}) {
  let text = input.replace(/\s/g, "");
  text = text.includes(".") ? text.replace(/,/g, "") : text.replace(",", ".");
  if (!/^\d{1,10}(\.\d{1,2})?$/.test(text)) return null;
  if (!allowZero && toCents(text) === 0) return null;
  return text;
}

const pad = (n) => String(n).padStart(2, "0");

function todayISO() {
  const now = new Date();
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

const currentMonthKey = () => todayISO().slice(0, 7);

function parseISODate(iso) {
  const [year, month, day = 1] = iso.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function formatDay(iso) {
  const date = parseISODate(iso);
  const options = { day: "numeric", month: "short" };
  if (date.getFullYear() !== new Date().getFullYear()) options.year = "numeric";
  return date.toLocaleDateString(undefined, options);
}

const monthLong = (key) => parseISODate(key).toLocaleDateString(undefined, { month: "long", year: "numeric" });
const monthShort = (key) => parseISODate(key).toLocaleDateString(undefined, { month: "short" });

// ---------- API

async function api(path, { method = "GET", body, form, raw = false, auth = true } = {}, retry = true) {
  const headers = {};
  if (auth && state.token) headers.Authorization = `Bearer ${state.token}`;
  let payload;
  if (form) {
    payload = new URLSearchParams(form);
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(path, { method, headers, body: payload });
  } catch {
    showBanner("Can't reach Perfima. If you closed it, start it again and reload this page.");
    throw new ApiError(0, "Perfima is not reachable");
  }
  hideBanner(true);

  if (auth && response.status === 401) {
    // local tokens are free to renew, a server login has to be repeated
    if (state.mode === "local" && retry) {
      await startLocalSession();
      return api(path, { method, body, form, raw, auth }, false);
    }
    if (state.mode === "server") showLogin("Your session expired, please log in again.");
  }

  if (!response.ok) {
    let message = response.statusText || `Request failed (${response.status})`;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail)) message = data.detail.map((d) => d.msg).join(", ");
    } catch {
      // not JSON, keep the status text
    }
    throw new ApiError(response.status, message);
  }
  return raw ? response : response.json();
}

async function startLocalSession() {
  const data = await api("/local/session", { method: "POST", auth: false });
  state.token = data.access_token;
}

async function loadCategories() {
  state.categories = await api("/categories/");
}

async function loadTransactions() {
  state.transactions = await api("/transactions/");
  state.trendStale = true;
}

async function loadTrend() {
  state.trend = await api(`/reports/trend?months=${TREND_FETCH_MONTHS}`);
  state.trendStale = false;
}

function readStoredToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function storeToken(token) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // storage blocked, the token just won't survive a reload
  }
}

// ---------- banner and errors

let bannerTimer = null;
let bannerSticky = false;

function showBanner(message, { sticky = true } = {}) {
  const banner = $("#banner");
  banner.textContent = message;
  banner.hidden = false;
  bannerSticky = sticky;
  clearTimeout(bannerTimer);
  if (!sticky) bannerTimer = setTimeout(() => { banner.hidden = true; }, 6000);
}

function hideBanner(onlySticky = false) {
  if (onlySticky && !bannerSticky) return;
  $("#banner").hidden = true;
  bannerSticky = false;
}

function showError(error) {
  if (error instanceof ApiError && (error.status === 0 || (error.status === 401 && state.mode === "server"))) return;
  showBanner(error.message || String(error), { sticky: false });
}

// ---------- screens and tabs

function showScreen(id) {
  for (const screen of ["boot", "login", "stopped", "app"]) $(`#${screen}`).hidden = screen !== id;
  $("#tabs").hidden = id !== "app";
  $("#quit").hidden = !(id === "app" && state.mode === "local");
  $("#logout").hidden = !(id === "app" && state.mode === "server");
}

function switchTab(tab) {
  if (!TABS.includes(tab)) tab = "add";
  state.tab = tab;
  for (const name of TABS) {
    $(`#tab-${name}`).hidden = name !== tab;
    $(`#tab-btn-${name}`).setAttribute("aria-selected", String(name === tab));
  }
  if (location.hash !== `#${tab}`) history.replaceState(null, "", `#${tab}`);
  if (tab === "add") $("#add-amount").focus();
  if (tab === "insights") renderInsights();
}

function renderAll() {
  renderAddTab();
  renderHistory();
  if (state.tab === "insights") renderInsights();
}

async function refreshTransactions() {
  await loadTransactions();
  renderAll();
}

// ---------- shared pieces

function categoryOptions(selected, { allowNew = false, includeAll = false } = {}) {
  const names = state.categories.map((c) => c.name);
  if (selected && !includeAll && !names.includes(selected)) names.push(selected);
  const options = names.map((name) => h("option", { value: name, textContent: name, selected: name === selected }));
  if (includeAll) options.unshift(h("option", { value: "", textContent: "All categories", selected: !selected }));
  if (allowNew) options.push(h("option", { value: NEW_CATEGORY, textContent: "+ New category…" }));
  return options;
}

// Destructive buttons need a second click within 3 seconds
function confirmButton(label, action) {
  const button = h("button", { type: "button", class: "small ghost danger", textContent: label });
  let timer = null;
  const disarm = () => {
    button.classList.remove("armed");
    button.textContent = label;
  };
  button.addEventListener("click", async () => {
    if (!button.classList.contains("armed")) {
      button.classList.add("armed");
      button.textContent = "Sure?";
      timer = setTimeout(disarm, 3000);
      return;
    }
    clearTimeout(timer);
    button.disabled = true;
    try {
      await action();
    } catch (error) {
      button.disabled = false;
      disarm();
      showError(error);
    }
  });
  return button;
}

function entryItem(transaction) {
  const item = h("li");
  item.append(state.editingId === transaction.id ? editRow(transaction) : entryRow(transaction));
  return item;
}

function entryRow(t) {
  const income = t.transaction_type === "credit";
  const select = h("select", {
    class: "entry-cat",
    "aria-label": "Category",
    onchange: () => recategorize(t, select),
  }, categoryOptions(t.category));

  return h("div", { class: "entry" },
    h("span", { class: "entry-date", textContent: formatDay(t.date) }),
    h("span", {
      class: t.description ? "entry-desc" : "entry-desc none",
      textContent: t.description || "No description",
      title: t.description || "",
    }),
    select,
    h("span", {
      class: income ? "entry-amount income" : "entry-amount",
      textContent: (income ? "+" : "") + formatMoney(t.amount),
    }),
    h("span", { class: "entry-actions" },
      h("button", { type: "button", class: "small ghost", textContent: "Edit", onclick: () => startEdit(t.id) }),
      confirmButton("Delete", () => deleteTransaction(t.id)),
    ),
  );
}

function editRow(t) {
  const form = h("form", { class: "entry editing", novalidate: true },
    h("input", { type: "date", name: "date", value: t.date, required: true, "aria-label": "Date" }),
    h("input", { name: "description", value: t.description, placeholder: "Description", "aria-label": "Description" }),
    h("select", { name: "category", "aria-label": "Category" }, categoryOptions(t.category)),
    h("span", { class: "edit-amount" },
      h("select", { name: "transaction_type", "aria-label": "Type" },
        h("option", { value: "debit", textContent: "−", title: "Expense", selected: t.transaction_type === "debit" }),
        h("option", { value: "credit", textContent: "+", title: "Income", selected: t.transaction_type === "credit" }),
      ),
      h("input", { name: "amount", value: t.amount, inputMode: "decimal", required: true, "aria-label": "Amount" }),
    ),
    h("span", { class: "entry-actions" },
      h("button", { type: "submit", class: "small primary", textContent: "Save" }),
      h("button", { type: "button", class: "small ghost", textContent: "Cancel", onclick: cancelEdit }),
    ),
  );
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    saveEdit(t, form);
  });
  form.addEventListener("keydown", (event) => {
    if (event.key === "Escape") cancelEdit();
  });
  return form;
}

function renderEntryList(list, transactions, emptyText) {
  list.replaceChildren(
    ...(transactions.length
      ? transactions.map(entryItem)
      : [h("li", { class: "empty", textContent: emptyText })]),
  );
  const editing = list.querySelector(".entry.editing input[name=amount]");
  if (editing) editing.focus();
}

// ---------- transaction actions

async function recategorize(transaction, select) {
  const previous = transaction.category;
  try {
    const updated = await api(`/transactions/${transaction.id}`, { method: "PUT", body: { category: select.value } });
    Object.assign(transaction, updated);
    state.trendStale = true;
    renderAll();
  } catch (error) {
    select.value = previous;
    showError(error);
  }
}

function startEdit(id) {
  state.editingId = id;
  renderAll();
}

function cancelEdit() {
  state.editingId = null;
  renderAll();
}

async function saveEdit(transaction, form) {
  const fields = form.elements;
  const amount = parseAmount(fields.amount.value);
  if (!amount) {
    showBanner("Enter an amount like 12.50", { sticky: false });
    fields.amount.focus();
    return;
  }
  if (!fields.date.value) {
    showBanner("Pick a date", { sticky: false });
    fields.date.focus();
    return;
  }
  const body = {
    amount,
    date: fields.date.value,
    description: fields.description.value.trim(),
    category: fields.category.value,
    transaction_type: fields.transaction_type.value,
  };
  try {
    await api(`/transactions/${transaction.id}`, { method: "PUT", body });
    state.editingId = null;
    await refreshTransactions();
  } catch (error) {
    showError(error);
  }
}

async function deleteTransaction(id) {
  await api(`/transactions/${id}`, { method: "DELETE" });
  state.justAdded.delete(id);
  if (state.editingId === id) state.editingId = null;
  await refreshTransactions();
}

// ---------- Add tab

function fillAddCategories(selected) {
  const select = $("#add-category");
  const creating = select.value === NEW_CATEGORY && !$("#new-category").hidden;
  const current = selected ?? (creating ? select.dataset.previous : select.value);
  const fallback = state.categories.length ? state.categories[0].name : "";
  const value = state.categories.some((c) => c.name === current) ? current : fallback;
  select.replaceChildren(...categoryOptions(value, { allowNew: true }));
  select.dataset.previous = value;
  if (creating && selected === undefined) select.value = NEW_CATEGORY;
}

function renderAddTab() {
  fillAddCategories();
  const today = todayISO();
  const recent = state.transactions.filter((t) => t.date === today || state.justAdded.has(t.id));
  renderEntryList($("#recent-list"), recent, "Nothing entered today yet.");

  const spentToday = state.transactions
    .filter((t) => t.date === today && t.transaction_type === "debit")
    .reduce((sum, t) => sum + toCents(t.amount), 0);
  $("#today-total").textContent = spentToday ? `Spent today: ${formatCents(spentToday)}` : "";
}

function resetDefaultDate() {
  const input = $("#add-date");
  const today = todayISO();
  // only move the date forward if the user hasn't picked one themselves
  if (!input.value || input.value === state.defaultDate) input.value = today;
  state.defaultDate = today;
}

async function submitEntry(event) {
  event.preventDefault();
  const form = event.target;
  const fields = form.elements;
  const error = $("#add-error");
  error.textContent = "";
  $("#add-status").textContent = "";

  const amount = parseAmount(fields.amount.value);
  if (!amount) {
    error.textContent = "Enter an amount like 12.50";
    fields.amount.focus();
    return;
  }
  const category = fields.category.value;
  if (!category || category === NEW_CATEGORY) {
    error.textContent = "Pick a category";
    fields.category.focus();
    return;
  }
  const body = {
    amount,
    category,
    description: fields.description.value.trim(),
    date: fields.date.value || todayISO(),
    transaction_type: fields.type.value,
  };

  const submit = form.querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    const created = await api("/transactions/", { method: "POST", body });
    state.justAdded.add(created.id);
    fields.amount.value = "";
    fields.description.value = "";
    $("#add-status").textContent = `Added ${formatMoney(created.amount)} to ${created.category}`;
    await refreshTransactions();
    fields.amount.focus();
  } catch (err) {
    error.textContent = err.message;
  } finally {
    submit.disabled = false;
  }
}

function openNewCategory() {
  $("#new-category").hidden = false;
  const input = $("#new-category-name");
  input.value = "";
  input.focus();
}

function closeNewCategory() {
  $("#new-category").hidden = true;
  const select = $("#add-category");
  if (select.value === NEW_CATEGORY) select.value = select.dataset.previous || "";
}

async function createCategory() {
  const name = $("#new-category-name").value.trim();
  if (!name) {
    $("#new-category-name").focus();
    return;
  }
  try {
    if (!state.categories.some((c) => c.name === name)) {
      const created = await api("/categories/", { method: "POST", body: { name } });
      state.categories.push(created);
    }
    $("#new-category").hidden = true;
    fillAddCategories(name);
    renderHistory();
    $("#add-amount").focus();
  } catch (error) {
    $("#add-error").textContent = error.message;
  }
}

// ---------- History tab

function renderHistory() {
  if (state.historyMonth === null) state.historyMonth = currentMonthKey();

  const months = new Set(state.transactions.map((t) => t.date.slice(0, 7)));
  months.add(currentMonthKey());
  if (state.historyMonth) months.add(state.historyMonth);
  const monthSelect = $("#history-month");
  monthSelect.replaceChildren(
    h("option", { value: "", textContent: "All months", selected: !state.historyMonth }),
    ...[...months].sort().reverse().map((key) =>
      h("option", { value: key, textContent: monthLong(key), selected: key === state.historyMonth })),
  );

  if (state.historyCategory && !state.categories.some((c) => c.name === state.historyCategory)) {
    state.historyCategory = "";
  }
  $("#history-category").replaceChildren(...categoryOptions(state.historyCategory, { includeAll: true }));

  const shown = state.transactions.filter((t) =>
    (!state.historyMonth || t.date.startsWith(state.historyMonth)) &&
    (!state.historyCategory || t.category === state.historyCategory));

  let spent = 0;
  let income = 0;
  for (const t of shown) {
    if (t.transaction_type === "credit") income += toCents(t.amount);
    else spent += toCents(t.amount);
  }
  $("#history-totals").replaceChildren(
    h("span", {}, "Spent ", h("strong", { textContent: formatCents(spent) })),
    h("span", {}, "Income ", h("strong", { textContent: formatCents(income) })),
    h("span", { textContent: `${shown.length} ${shown.length === 1 ? "entry" : "entries"}` }),
  );

  const where = state.historyMonth ? ` in ${monthLong(state.historyMonth)}` : "";
  renderEntryList($("#history-list"), shown, `No entries${where}.`);
}

async function exportCsv() {
  try {
    const response = await api("/transactions/export.csv", { raw: true });
    const url = URL.createObjectURL(await response.blob());
    const link = h("a", { href: url, download: `perfima-${todayISO()}.csv` });
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (error) {
    showError(error);
  }
}

// ---------- Insights tab

const spentIn = (month, name) => {
  const entry = month.categories.find((c) => c.name === name);
  return entry ? toCents(entry.spent) : 0;
};

const totalBudgetCents = () =>
  state.categories.reduce((sum, c) => sum + (c.monthly_budget == null ? 0 : toCents(c.monthly_budget)), 0);

async function renderInsights() {
  try {
    if (state.trendStale || !state.trend) await loadTrend();
  } catch (error) {
    showError(error);
    return;
  }
  const shown = state.trend.slice(-TREND_MONTHS);
  if (!shown.some((m) => m.month === state.selectedMonth)) state.selectedMonth = shown[shown.length - 1].month;
  renderChart(shown);
  renderMonthDetail();
}

function niceStep(raw) {
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const fraction = raw / magnitude;
  const nice = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 2.5 ? 2.5 : fraction <= 5 ? 5 : 10;
  return nice * magnitude;
}

function selectMonth(key) {
  state.selectedMonth = key;
  renderChart(state.trend.slice(-TREND_MONTHS));
  renderMonthDetail();
}

function renderChart(months) {
  const width = 720;
  const height = 250;
  const pad = { left: 52, right: 14, top: 14, bottom: 38 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;

  const budget = totalBudgetCents();
  // an empty year still gets a readable 0 to 10 axis
  const peak = Math.max(1000, budget,...months.map((m) => Math.max(toCents(m.expenses), toCents(m.income))));
  const step = niceStep(peak / 4);
  const topValue = Math.ceil(peak / step) * step;
  const y = (cents) => pad.top + plotHeight - (cents / topValue) * plotHeight;
  const band = plotWidth / months.length;

  const chart = svg("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "group",
    "aria-label": "Monthly expenses and income",
  });

  for (let value = 0; value <= topValue + 0.5; value += step) {
    chart.append(
      svg("line", { class: value === 0 ? "baseline" : "grid", x1: pad.left, x2: width - pad.right, y1: y(value), y2: y(value) }),
      svg("text", { x: pad.left - 8, y: y(value) + 4, "text-anchor": "end" }, compactFormat.format(value / 100)),
    );
  }

  months.forEach((month, index) => {
    const expenses = toCents(month.expenses);
    const income = toCents(month.income);
    const x = pad.left + index * band;
    const barHeight = expenses > 0 ? Math.max(1, y(0) - y(expenses)) : 0;
    const label = `${monthLong(month.month)}: spent ${formatCents(expenses)}, income ${formatCents(income)}`;
    const showYear = index === 0 || month.month.endsWith("-01");

    const group = svg("g", {
      class: month.month === state.selectedMonth ? "month selected" : "month",
      tabindex: 0,
      role: "button",
      "aria-label": label,
      "aria-pressed": String(month.month === state.selectedMonth),
      onclick: () => selectMonth(month.month),
      onkeydown: (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectMonth(month.month);
        }
      },
    },
      svg("title", {}, label),
      svg("rect", { class: "hit", x, y: pad.top, width: band, height: plotHeight + pad.bottom - 4, rx: 4 }),
      svg("rect", { class: "bar", x: x + band * 0.2, y: y(0) - barHeight, width: band * 0.6, height: barHeight, rx: 2 }),
      svg("text", { class: "label", x: x + band / 2, y: height - pad.bottom + 16, "text-anchor": "middle" }, monthShort(month.month)),
      showYear && svg("text", { x: x + band / 2, y: height - pad.bottom + 30, "text-anchor": "middle" }, month.month.slice(0, 4)),
    );
    chart.append(group);
  });

  if (budget > 0) {
    chart.append(svg("line", { class: "budget-line", x1: pad.left, x2: width - pad.right, y1: y(budget), y2: y(budget) }));
  }
  $("#legend-budget").hidden = budget === 0;

  const points = months.map((m, i) => `${pad.left + i * band + band / 2},${y(toCents(m.income))}`);
  chart.append(svg("polyline", { class: "income-line", points: points.join(" ") }));
  months.forEach((m, i) => {
    chart.append(svg("circle", { class: "income-dot", cx: pad.left + i * band + band / 2, cy: y(toCents(m.income)), r: 3 }));
  });

  $("#trend-chart").replaceChildren(chart);
}

function stat(label, value, { negative = false, note = "", noteClass = "" } = {}) {
  return h("div", { class: "stat" },
    h("div", { class: "label", textContent: label }),
    h("div", { class: negative ? "value negative" : "value", textContent: value }),
    note && h("div", { class: `note ${noteClass}`, textContent: note }),
  );
}

function renderMonthDetail() {
  const index = state.trend.findIndex((m) => m.month === state.selectedMonth);
  const month = state.trend[index];
  const previous = state.trend.slice(Math.max(0, index - 3), index);

  $("#detail-title").textContent = monthLong(month.month);

  const rows = state.categories.map((category) => {
    const spent = spentIn(month, category.name);
    const budget = category.monthly_budget == null ? null : toCents(category.monthly_budget);
    const average = previous.length
      ? previous.reduce((sum, m) => sum + spentIn(m, category.name), 0) / previous.length
      : null;
    return { category, spent, budget, average };
  });
  const active = rows
    .filter((r) => r.spent > 0 || r.budget !== null)
    .sort((a, b) => b.spent - a.spent || a.category.name.localeCompare(b.category.name));
  const idle = rows.filter((r) => !active.includes(r));
  const top = new Set(active.filter((r) => r.spent > 0).slice(0, TOP_CATEGORIES).map((r) => r.category.id));

  const expenses = toCents(month.expenses);
  const income = toCents(month.income);
  const net = income - expenses;
  const budgeted = rows.filter((r) => r.budget !== null);
  const budgetTotal = budgeted.reduce((sum, r) => sum + r.budget, 0);
  const overCount = budgeted.filter((r) => r.spent > r.budget).length;
  $("#detail-stats").replaceChildren(
    stat("Spent", formatCents(expenses)),
    stat("Income", formatCents(income)),
    stat("Net", (net > 0 ? "+" : "") + formatCents(net), { negative: net < 0 }),
    budgeted.length
      ? stat("Budgeted", formatCents(budgetTotal), {
        note: overCount ? `${overCount} ${overCount === 1 ? "category" : "categories"} over` : "All within budget",
        noteClass: overCount ? "over" : "",
      })
      : stat("Budgeted", "None set", { note: "Set budgets below" }),
  );

  $("#breakdown").replaceChildren(
    ...(active.length
      ? active.map((r) => breakdownRow(r, top.has(r.category.id)))
      : [h("li", { class: "empty muted", textContent: "Nothing spent this month." })]),
  );

  const idleDetails = $("#breakdown-idle");
  idleDetails.hidden = idle.length === 0;
  idleDetails.querySelector("summary").textContent =
    `${idle.length} more ${idle.length === 1 ? "category" : "categories"} with no spending or budget`;
  $("#breakdown-idle-list").replaceChildren(...idle.map((r) => breakdownRow(r, false)));
}

function changeCell(spent, average) {
  if (average === null || (average === 0 && spent === 0)) return h("span", { class: "bd-change", textContent: "—" });
  if (average === 0) return h("span", { class: "bd-change up", textContent: "new" });
  const percent = Math.round(((spent - average) / average) * 100);
  const title = `3 month average: ${formatCents(Math.round(average))}`;
  if (percent === 0) return h("span", { class: "bd-change", textContent: "same", title });
  return h("span", {
    class: percent > 0 ? "bd-change up" : "bd-change down",
    textContent: `${percent > 0 ? "+" : "−"}${Math.abs(percent)}%`,
    title,
  });
}

function breakdownRow({ category, spent, budget, average }, isTop) {
  const budgetCell = h("div", { class: "bd-budget" });
  const showBudget = () => {
    if (budget === null) {
      budgetCell.replaceChildren(
        h("button", { type: "button", class: "link-button", textContent: "Set budget", onclick: editBudget }),
      );
      return;
    }
    const over = spent > budget;
    const fill = h("div", { class: "meter-fill" });
    fill.style.width = `${budget === 0 ? 100 : Math.min(100, (spent / budget) * 100)}%`;
    budgetCell.replaceChildren(
      h("div", { class: over ? "meter over" : "meter" }, fill),
      h("div", { class: "budget-line-text" },
        h("button", {
          type: "button",
          class: "link-button",
          textContent: `of ${formatCents(budget)}`,
          title: "Change budget",
          onclick: editBudget,
        }),
        over
          ? h("span", { class: "over", textContent: `${formatCents(spent - budget)} over` })
          : h("span", { textContent: `${formatCents(budget - spent)} left` }),
      ),
    );
  };

  function editBudget() {
    const input = h("input", {
      class: "budget-input",
      inputMode: "decimal",
      value: budget === null ? "" : (budget / 100).toFixed(2),
      placeholder: "No budget",
      "aria-label": `Monthly budget for ${category.name}`,
    });
    let done = false;
    const save = async () => {
      if (done) return;
      const text = input.value.trim();
      const amount = text === "" ? null : parseAmount(text, { allowZero: true });
      if (text !== "" && amount === null) {
        showBanner("Enter a budget like 400 or leave it empty to remove it", { sticky: false });
        input.focus();
        return;
      }
      done = true;
      try {
        const updated = await api(`/categories/${category.id}`, { method: "PUT", body: { monthly_budget: amount } });
        Object.assign(category, updated);
        renderInsights();
      } catch (error) {
        done = false;
        showError(error);
      }
    };
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        save();
      } else if (event.key === "Escape") {
        done = true;
        showBudget();
      }
    });
    input.addEventListener("blur", save);
    budgetCell.replaceChildren(input, h("span", { class: "muted small-print", textContent: "Enter to save, empty to remove" }));
    input.focus();
    input.select();
  }

  showBudget();
  return h("li", { class: isTop ? "breakdown-row top" : "breakdown-row" },
    h("span", { class: "bd-name" },
      h("span", { class: "name", textContent: category.name, title: category.name }),
      isTop && h("span", { class: "badge", textContent: "Top" }),
    ),
    h("span", { class: "bd-spent", textContent: formatCents(spent) }),
    budgetCell,
    changeCell(spent, average),
  );
}

// ---------- session, heartbeat, quit

function showLogin(message = "") {
  state.token = null;
  storeToken(null);
  $("#login-error").textContent = message;
  showScreen("login");
  $("#login-form").elements.username.focus();
}

async function submitLogin(event) {
  event.preventDefault();
  const fields = event.target.elements;
  $("#login-error").textContent = "";
  try {
    const data = await api("/login", {
      method: "POST",
      form: { username: fields.username.value, password: fields.password.value },
      auth: false,
    });
    state.token = data.access_token;
    storeToken(state.token);
    fields.password.value = "";
    await enterApp();
  } catch (error) {
    $("#login-error").textContent = error.message;
  }
}

function heartbeat() {
  if (state.heartbeatTimer === null) return;
  api("/local/heartbeat", { method: "POST" }).catch(() => {});
}

async function quit() {
  clearInterval(state.heartbeatTimer);
  state.heartbeatTimer = null;
  try {
    await api("/local/shutdown", { method: "POST" });
  } catch {
    // already gone
  }
  hideBanner();
  showScreen("stopped");
}

async function enterApp() {
  try {
    await Promise.all([loadCategories(), loadTransactions()]);
  } catch (error) {
    if (state.mode === "server" && error.status === 401) return;
    $("#boot-message").textContent = `Could not load your data: ${error.message}`;
    showScreen("boot");
    return;
  }
  if (state.mode === "local" && state.heartbeatTimer === null) {
    state.heartbeatTimer = setInterval(heartbeat, HEARTBEAT_MS);
  }
  resetDefaultDate();
  showScreen("app");
  renderAll();
  switchTab(location.hash.slice(1));
}

async function boot() {
  try {
    await startLocalSession();
    state.mode = "local";
  } catch (error) {
    if (error.status === 404) {
      state.mode = "server";
    } else {
      $("#boot-message").textContent = error.status === 0
        ? "Can't reach Perfima. Start it again, then reload this page."
        : `Perfima could not start a session: ${error.message}`;
      return;
    }
  }

  if (state.mode === "server") {
    state.token = readStoredToken();
    if (!state.token) {
      showLogin();
      return;
    }
  }
  await enterApp();
}

function bindEvents() {
  for (const button of document.querySelectorAll("#tabs [data-tab]")) {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  }
  $("#tabs").addEventListener("keydown", (event) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    const next = (TABS.indexOf(state.tab) + (event.key === "ArrowRight" ? 1 : TABS.length - 1)) % TABS.length;
    switchTab(TABS[next]);
    $(`#tab-btn-${TABS[next]}`).focus();
  });

  $("#add-form").addEventListener("submit", submitEntry);
  $("#add-category").addEventListener("change", (event) => {
    if (event.target.value === NEW_CATEGORY) {
      openNewCategory();
    } else {
      event.target.dataset.previous = event.target.value;
      $("#new-category").hidden = true;
    }
  });
  $("#new-category-name").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      createCategory();
    } else if (event.key === "Escape") {
      closeNewCategory();
    }
  });
  $("#new-category-save").addEventListener("click", createCategory);
  $("#new-category-cancel").addEventListener("click", closeNewCategory);

  $("#history-month").addEventListener("change", (event) => {
    state.historyMonth = event.target.value;
    state.editingId = null;
    renderHistory();
  });
  $("#history-category").addEventListener("change", (event) => {
    state.historyCategory = event.target.value;
    state.editingId = null;
    renderHistory();
  });
  $("#export-csv").addEventListener("click", exportCsv);

  $("#login-form").addEventListener("submit", submitLogin);
  $("#logout").addEventListener("click", () => showLogin());
  $("#quit").addEventListener("click", quit);

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) return;
    heartbeat();
    if (!$("#app").hidden) resetDefaultDate();
  });
}

bindEvents();
boot();
