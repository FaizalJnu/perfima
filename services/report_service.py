from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from calendar import monthrange
from sqlalchemy import func
from models import Transaction, Category, SavingsGoal
import matplotlib.pyplot as plt
import io
import base64
import logging

logger = logging.getLogger(__name__)

def get_last_year_date_range():
    today = datetime.utcnow().date()
    one_year_ago = today - timedelta(days=365)
    return one_year_ago, today


def get_monthly_report(db: Session, user_id: int, year: int, month: int):
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    return get_report(db, user_id, start_date, end_date)

def get_yearly_report(db: Session, user_id: int):
    start_date, end_date = get_last_year_date_range()
    logger.info(f"Generating yearly report for user {user_id} from {start_date} to {end_date}")
    return get_report(db, user_id, start_date, end_date)


def get_monthly_category_report(db: Session, user_id: int, year: int, month: int):
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    return get_category_report(db, user_id, start_date, end_date)


# Use dynamic date range for category-based yearly report
def get_yearly_category_report(db: Session, user_id: int):
    start_date, end_date = get_last_year_date_range()
    logger.info(f"Generating yearly category report for user {user_id} from {start_date} to {end_date}")
    return get_category_report(db, user_id, start_date, end_date)


def get_report(db: Session, user_id: int, start_date: date, end_date: date):
    income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == 'credit',
        Transaction.date.between(start_date, end_date)
    ).scalar() or 0

    expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == 'debit',
        Transaction.date.between(start_date, end_date)
    ).scalar() or 0

    saving_categories = db.query(SavingsGoal.category_id).filter(SavingsGoal.user_id == user_id).distinct()
    savings = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.category_id.in_(saving_categories),
        Transaction.transaction_type == 'credit',
        Transaction.date.between(start_date, end_date)
    ).scalar() or 0

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

    total_income, total_expense, total_savings = 0, 0, 0
    category_response = {}

    saving_category_ids = {cat_id[0] for cat_id in db.query(SavingsGoal.category_id).filter(SavingsGoal.user_id == user_id).distinct()}

    for category in category_report:
        income = category[1] if category[1] is not None else 0
        expense = category[2] if category[2] is not None else 0
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
