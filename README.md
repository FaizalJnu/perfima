# PERFIMA

## Overview

This project is a personal finance manager built with **Python** using **FastAPI** for the API layer and **SQLAlchemy** for the ORM. It runs on **SQLite** or **PostgreSQL**. Users can manage their accounts, track transactions, set category budgets and savings goals, and see where their money goes month by month.

It can be used in two ways:

- **Desktop app**: a single executable that starts the API on your machine and opens a browser UI. No account, no setup, the data stays in a local SQLite file.
- **Server**: the plain API (plus the same UI with a login form), run directly or with Docker Compose against Postgres.

---

## Features

### 1. **User Management**
   - **Registration and Login**: Users can register and log into the system with unique credentials.
   - **User Profile**: Each user has a personal profile with details like name, email, and password.
   - **Security**: Passwords are securely hashed, and the system issues secure JWT tokens for authentication.

### 2. **Transaction Management**
   - **Add Transactions**: Users can add financial transactions including:
     - Amount
     - Date
     - Category (e.g., Food, Rent, Entertainment)
     - Description
   - **View, Update, and Delete Transactions**: Users can view all their transactions, update transaction details, or delete transactions as needed.
   - **CSV Export**: The full transaction history can be downloaded as a CSV file.
   - Amounts are stored as exact decimals (2 decimal places), never as floats.

### 3. **Category Management**
   - **Custom Categories**: Users can create custom categories to organize their financial transactions.
   - **Monthly Budgets**: Each category can have an optional monthly budget.
   - **View and Manage Categories**: Users can view, update, and delete categories for easier financial tracking.

### 4. **Savings Goals**
   - **Set Savings Goals**: Users can create savings goals by defining:
     - Target amount
     - Category
   - **Track Progress**: The system automatically tracks progress towards these goals based on the user's income in that category.

### 5. **Reports**
   - **Monthly and Yearly Reports**: The system generates monthly and yearly financial reports to show:
     - Income
     - Expenses
     - Savings
   - **Monthly Trend**: Income, expenses and spending per category for each of the last N months, with budgets alongside.
   - **Visual Representations**: Reports include pie charts of spending by category.

### 6. **Browser UI**
   - **Add**: enter an expense or income in a few keystrokes (Enter submits), with today's entries listed below.
   - **History**: filter by month and category, re-categorize, edit or delete entries, export to CSV.
   - **Insights**: a 12 month chart of expenses and income. Pick a month to see spending per category against its budget and against the average of the 3 months before. Budgets can be edited in place.
   - Plain HTML, CSS and JavaScript with no build step and no external requests, so it works offline.

### 7. **Data Persistence**
   - **Database**: All user data, transactions, categories, and savings goals are persisted with SQLAlchemy in SQLite (default) or PostgreSQL.

### 8. **Tracing**
   - Optional OpenTelemetry tracing of requests and SQL queries, exported over OTLP (e.g. to Jaeger).

---

## Tech Stack

- **Backend Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: SQLite or PostgreSQL
- **Authentication**: OAuth2 with JWT tokens
- **Tracing**: OpenTelemetry
- **Desktop build**: PyInstaller
- **Python Version**: 3.12

---

## Desktop App

### Using it

Run the executable (`perfima`, or `perfima.exe` on Windows). It starts Perfima in the background and opens it in your browser at `http://127.0.0.1:8765/app/`. If Perfima is already running, it just opens the browser again.

- Enter the day's expenses and close the tab, or press **Quit**. After about 2 minutes without an open tab, Perfima stops by itself.
- Your data is kept between runs in:
  - Linux: `$XDG_DATA_HOME/perfima` (usually `~/.local/share/perfima`)
  - macOS: `~/Library/Application Support/perfima`
  - Windows: `%APPDATA%\perfima`
- That folder holds `perfima.db` (the SQLite database), `secret_key` and a matplotlib font cache. Back up `perfima.db` to keep your history.

The executable keeps a console window open with the server log. Closing it also stops Perfima.

### Running it from source

Commands are run from the directory that contains `perfima/`, because the code imports itself as the `perfima` package.

```bash
pip install -r perfima/requirements.txt
python perfima/desktop.py
```

### Building the executable

PyInstaller builds for the platform it runs on, so build on each OS you want an executable for.

```bash
pip install -r perfima/requirements-build.txt
pyinstaller perfima/perfima.spec
```

The result is a single file in `dist/` (`dist/perfima` or `dist\perfima.exe`).

---

## Installation (server)

1. Clone the repository into a folder named `perfima`:

   ```bash
   git clone https://github.com/FaizalJnu/perfima.git
   ```

2. Create a virtual environment next to it and activate it:

   ```bash
   python3.12 -m venv env
   source env/bin/activate  # On Windows use `env\Scripts\activate`
   ```

3. Install the dependencies:

   ```bash
   pip install -r perfima/requirements.txt
   ```

4. Run the application from the directory that contains `perfima/`:

   ```bash
   uvicorn perfima.main:app --reload
   ```

5. Access the FastAPI Swagger documentation at `http://127.0.0.1:8000/docs`, or the UI at `http://127.0.0.1:8000/app/` (log in with a user created through `/signup`).

### Docker Compose

Runs the API against Postgres, with Jaeger collecting traces:

```bash
cd perfima
cp .env.example .env   # then set SECRET_KEY and the Postgres password
docker compose up --build
```

- API and Swagger docs: `http://localhost:8000/docs`
- UI: `http://localhost:8000/app/`
- Jaeger UI (traces of requests and their SQL queries): `http://localhost:16686`

---

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./main.db` | Database to use. `postgresql://…` URLs use the psycopg 3 driver. |
| `SECRET_KEY` | development value | Signs login tokens. Set it to a long random string in any real deployment. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `300` | Token lifetime. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | unset | Turns on tracing and sends spans to this OTLP/HTTP endpoint, e.g. `http://localhost:4318`. |
| `OTEL_SERVICE_NAME` | `perfima` | Service name shown in the tracing backend. |
| `PERFIMA_LOCAL_MODE` | unset | `1` enables the single user `/local` endpoints. The desktop launcher sets it, don't set it on a server. |
| `TEST_DATABASE_URL` | `sqlite:///./test.db` | Database used by the tests. |

The desktop launcher sets `DATABASE_URL`, `SECRET_KEY` and `PERFIMA_LOCAL_MODE` itself.

---

## Running Tests

From the directory that contains `perfima/`:

```bash
PYTHONPATH=. pytest perfima/tests
```

To run them against Postgres (for example the Docker Compose one), point `TEST_DATABASE_URL` at a separate database. The tests drop and recreate every table, so never point it at real data:

```bash
docker compose -f perfima/docker-compose.yml exec db createdb -U perfima perfima_test
TEST_DATABASE_URL=postgresql+psycopg://perfima:perfima@localhost:5432/perfima_test PYTHONPATH=. pytest perfima/tests
```

GitHub Actions runs the suite on every push and pull request, once on SQLite and once on Postgres.

---

## API Endpoints

### **User Management**

- **POST** `/signup`: Register a new user.
- **POST** `/login`: Login a user and get access token.
- **GET** `/users/me`: The logged in user.

### **Transaction Management**

- **POST** `/transactions`: Add a new transaction.
- **GET** `/transactions`: Get a list of all transactions, newest first.
- **GET** `/transactions/export.csv`: Download all transactions as CSV.
- **PUT** `/transactions/{id}`: Update a specific transaction.
- **DELETE** `/transactions/{id}`: Delete a specific transaction.

### **Category Management**

- **POST** `/categories`: Create a new category.
- **GET** `/categories`: List all categories.
- **PUT** `/categories/{id}`: Update a specific category, including its monthly budget.
- **DELETE** `/categories/{id}`: Delete a specific category.

### **Savings Goals**

- **POST** `/savings_goal`: Set a new savings goal.
- **GET** `/savings_goal`: Get all savings goals.
- **PUT** `/savings_goal/{id}`: Update a specific savings goal.
- **DELETE** `/savings_goal/{id}`: Delete a specific savings goal.

### **Reports**

- **GET** `/reports/monthly/{year}/{month}`: Income, expenses and savings for a month.
- **GET** `/reports/yearly/{year}`: The same for a calendar year.
- **GET** `/reports/category/monthly/{year}/{month}`, `/reports/category/yearly/{year}`: Spending by category.
- **GET** `/reports/trend?months=12`: Month by month income, expenses and category spending with budgets.

### **Desktop mode** (only with `PERFIMA_LOCAL_MODE=1`, only on localhost)

- **POST** `/local/session`: Token for the single local user, created with default categories on first use.
- **POST** `/local/heartbeat`: Sent by the open UI so the launcher knows it is still in use.
- **POST** `/local/shutdown`: Stops the desktop app.

---

## Database Schema

- **Users**: Stores user data such as `username`, `email`, `hashed_password`, and personal details.
- **Transactions**: Stores transactions with fields like `amount`, `date`, `category`, and `description`.
- **Categories**: Stores user-defined categories for transactions, with an optional `monthly_budget`.
- **Savings Goals**: Stores savings goals including `target` and `progress`.

---

## Future Improvements

- Add user notifications for goal progress.
- Show and manage savings goals in the UI.
- Add database migrations (Alembic) so schema changes keep existing data.
- Add filtering, sorting and pagination to transaction listings on the server.
- Recurring transactions such as rent and salary.

---
