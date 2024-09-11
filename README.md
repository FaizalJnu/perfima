# PERFIMA

## Overview

This project is a backend service built with **Python** using **FastAPI** for the API layer, **SQLAlchemy** for ORM, and **SQLite** for database persistence. It provides users with a personal finance management system where they can manage their accounts, track transactions, set savings goals, and generate financial reports.

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

### 3. **Category Management**
   - **Custom Categories**: Users can create custom categories to organize their financial transactions.
   - **View and Manage Categories**: Users can view, update, and delete categories for easier financial tracking.

### 4. **Savings Goals**
   - **Set Savings Goals**: Users can create savings goals by defining:
     - Target amount
     - Target date
   - **Track Progress**: The system automatically tracks progress towards these goals based on the user's transactions and savings.

### 5. **Reports**
   - **Monthly and Yearly Reports**: The system generates monthly and yearly financial reports to show:
     - Income
     - Expenses
     - Savings
   - **Visual Representations**: Reports include visual representations (such as pie charts and bar graphs) to give users insights into their spending by category.

### 6. **Data Persistence**
   - **Database**: All user data, transactions, categories, and savings goals are persisted in a SQLite database using SQLAlchemy ORM to ensure data integrity and security.

---

## Tech Stack

- **Backend Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: SQLite
- **Authentication**: OAuth2 with JWT tokens
- **Python Version**: 3.10+

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/finance-management-api.git
   cd finance-management-api
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use `env\Scripts\activate`
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:

   ```bash
   fastapi dev main.py
   ```

6. Access the FastAPI Swagger documentation at `http://127.0.0.1:8000/docs`.

7. Run tests:

   ```bash
   PYTHONPATH=./ pytest perfima/tests/
   ```

---

## API Endpoints

### **User Management**

- **POST** `/signup`: Register a new user.
- **POST** `/login`: Login a user and get access token.

### **Transaction Management**

- **POST** `/transactions`: Add a new transaction.
- **GET** `/transactions`: Get a list of all transactions.
- **PUT** `/transactions/{id}`: Update a specific transaction.
- **DELETE** `/transactions/{id}`: Delete a specific transaction.

### **Category Management**

- **POST** `/categories`: Create a new category.
- **GET** `/categories`: List all categories.
- **PUT** `/categories/{id}`: Update a specific category.
- **DELETE** `/categories/{id}`: Delete a specific category.

### **Savings Goals**

- **POST** `/savings_goal`: Set a new savings goal.
- **GET** `/savings_goal`: Get all savings goals.
- **PUT** `/savings_goal/{id}`: Update a specific savings goal.
- **DELETE** `/savings_goal/{id}`: Delete a specific savings goal.

### **Reports**

- **GET** `/reports/monthly`: Generate a monthly financial report.
- **GET** `/reports/yearly`: Generate a yearly financial report.

---

## Database Schema

- **Users**: Stores user data such as `username`, `email`, `hashed_password`, and personal details.
- **Transactions**: Stores transactions with fields like `amount`, `date`, `category`, and `description`.
- **Categories**: Stores user-defined categories for transactions.
- **Savings Goals**: Stores savings goals including `target_amount` and `target_date`.

---

## Future Improvements

- Add user notifications for goal progress.
- Add a front end to make it product ready.
- Use a more robust database set up like supabase or MySQL
- Implement CSV export of transaction history.
- Add filtering and sorting to transaction listings.

---
