from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from calendar import monthrange
from decimal import Decimal
from sqlalchemy import func, extract
from perfima.models import Transaction, Category, SavingsGoal, TransactionType
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64
import logging

logger = logging.getLogger(__name__)

def get_last_year_date_range():
    today = datetime.utcnow().date()
    one_year_ago = today - timedelta(days=365)
    return one_year_ago, today


# Calendar year when a year is given, otherwise the last 365 days
def get_year_date_range(year: int = None):
    if year is None:
        return get_last_year_date_range()
    return date(year, 1, 1), date(year, 12, 31)


def get_monthly_report(db: Session, user_id: int, year: int, month: int):
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    return get_report(db, user_id, start_date, end_date)

def get_yearly_report(db: Session, user_id: int, year: int = None):
    start_date, end_date = get_year_date_range(year)
    logger.info(f"Generating yearly report for user {user_id} from {start_date} to {end_date}")
    return get_report(db, user_id, start_date, end_date)


def get_monthly_category_report(db: Session, user_id: int, year: int, month: int):
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    return get_category_report(db, user_id, start_date, end_date)


# Use dynamic date range for category-based yearly report
def get_yearly_category_report(db: Session, user_id: int, year: int = None):
    start_date, end_date = get_year_date_range(year)
    logger.info(f"Generating yearly category report for user {user_id} from {start_date} to {end_date}")
    return get_category_report(db, user_id, start_date, end_date)


def shift_month(year: int, month: int, delta: int):
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


# Income, expenses and spending per category for each of the last `months` months, oldest first.
# Months without transactions are still returned so charts get a continuous axis.
def get_monthly_trend(db: Session, user_id: int, months: int = 12, today: date = None):
    today = today or date.today()
    start_year, start_month = shift_month(today.year, today.month, -(months - 1))
    start_date = date(start_year, start_month, 1)
    end_date = date(today.year, today.month, monthrange(today.year, today.month)[1])

    year = extract("year", Transaction.date)
    month = extract("month", Transaction.date)
    rows = db.query(
        year, month, Transaction.category_id, Transaction.transaction_type, func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == user_id,
        Transaction.date.between(start_date, end_date)
    ).group_by(year, month, Transaction.category_id, Transaction.transaction_type).all()

    categories = {c.id: c for c in db.query(Category).filter(Category.user_id == user_id).all()}
    budgeted_ids = {c.id for c in categories.values() if c.monthly_budget is not None}

    trend = {}
    for offset in range(months):
        y, m = shift_month(start_year, start_month, offset)
        trend[(y, m)] = {"month": f"{y:04d}-{m:02d}", "income": Decimal("0.00"), "expenses": Decimal("0.00"), "spent": {}}

    # postgres returns EXTRACT as a numeric, sqlite as an integer
    for row_year, row_month, category_id, transaction_type, total in rows:
        entry = trend[(int(row_year), int(row_month))]
        total = total or Decimal("0.00")
        if transaction_type == TransactionType.credit:
            entry["income"] += total
        else:
            entry["expenses"] += total
            entry["spent"][category_id] = entry["spent"].get(category_id, Decimal("0.00")) + total

    # categories with a budget are listed even in months nothing was spent on them
    result = []
    for entry in trend.values():
        spent = entry.pop("spent")
        entry["categories"] = sorted(
            (
                {"name": categories[i].name, "spent": spent.get(i, Decimal("0.00")), "budget": categories[i].monthly_budget}
                for i in (set(spent) | budgeted_ids) if i in categories
            ),
            key=lambda c: (-c["spent"], c["name"])
        )
        result.append(entry)

    logger.info(f"Monthly trend for user {user_id} from {start_date} to {end_date}: {len(rows)} groups")
    return result


def get_report(db: Session, user_id: int, start_date: date, end_date: date):
    income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == 'credit',
        Transaction.date.between(start_date, end_date)
    ).scalar() or Decimal("0.00")

    expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == 'debit',
        Transaction.date.between(start_date, end_date)
    ).scalar() or Decimal("0.00")

    saving_categories = db.query(SavingsGoal.category_id).filter(SavingsGoal.user_id == user_id).distinct()
    savings = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.category_id.in_(saving_categories),
        Transaction.transaction_type == 'credit',
        Transaction.date.between(start_date, end_date)
    ).scalar() or Decimal("0.00")

    logger.info(f"Report for user {user_id}: Income: {income}, Expenses: {expenses}, Savings: {savings}")
    
    return {
        "income": income,
        "expenses": expenses,
        "savings": savings,
        "net": income - expenses,
        "start_date": start_date,
        "end_date": end_date
    }


def get_category_report(db: Session, user_id: int, start_date: date, end_date: date):
    category_report = db.query(
        Category.name,
        func.sum(Transaction.amount).filter(Transaction.transaction_type == 'credit').label('income'),
        func.sum(Transaction.amount).filter(Transaction.transaction_type == 'debit').label('expense')
    ).join(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date.between(start_date, end_date)
    ).group_by(Category.id).all()

    logger.info(f"Category report for user {user_id} between {start_date} and {end_date}: {len(category_report)} categories found.")

    total_income, total_expense, total_savings = Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
    category_response = {}

    saving_category_ids = {cat_id[0] for cat_id in db.query(SavingsGoal.category_id).filter(SavingsGoal.user_id == user_id).distinct()}

    for category in category_report:
        income = category[1] if category[1] is not None else Decimal("0.00")
        expense = category[2] if category[2] is not None else Decimal("0.00")
        total_income += income
        total_expense += expense

        if category[0] in saving_category_ids:
            total_savings += income

        category_response[category[0]] = {
            "income": income,
            "expenses": expense
        }

    income_chart = genPi([cat[0] for cat in category_report if cat[1]], [cat[1] for cat in category_report if cat[1]], "Income by Category")
    expense_chart = genPi([cat[0] for cat in category_report if cat[2]], [cat[2] for cat in category_report if cat[2]], "Expense by Category")
    summary_chart = genPi(["Income", "Expense", "Savings"], [total_income, total_expense, total_savings], "Financial Summary")

    logger.info(f"Generated charts for user {user_id}")

    return {
        "category_report": category_response,
        "total_income": total_income,
        "total_expense": total_expense,
        "total_savings": total_savings,
        "net": (total_income - total_expense),
        "start_date": start_date,
        "end_date": end_date,
        "income_chart": income_chart,
        "expense_chart": expense_chart,
        "summary_chart": summary_chart
    }


def get_saving_categories(db: Session, user_id: int):
    saving_categories = [category.name for category in db.query(Category).join(SavingsGoal).filter(SavingsGoal.user_id == user_id).all()]
    logger.info(f"Retrieved {len(saving_categories)} saving categories for user {user_id}")
    return saving_categories

# Get Pi charts
def genPi(labels, sizes, title):
    # matplotlib works in floats, which is fine for drawing a chart
    sizes = [float(size) for size in sizes]
    plt.figure(figsize=(10, 10))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title(title)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    image_png = buffer.getvalue()
    graphic = base64.b64encode(image_png).decode('utf-8')

    plt.close()

    return graphic
