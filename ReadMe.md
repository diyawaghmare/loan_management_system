# Loan Management System

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Setup Instructions](#setup-instructions)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
4. [API Endpoints](#api-endpoints)
    - [User Registration](#1-user-registration)
    - [Apply for Loan](#2-apply-for-loan)
    - [Make Payment](#3-make-payment)
    - [Get Loan Statement](#4-get-loan-statement)
5. [Utility Functions](#utility-functions)
    - [calculate_emi](#calculate_emi)
    - [payment_handler](#payment_handler)
    - [calculate_credit_score (Celery task)](#calculate_credit_score-celery-task)
6. [Usage](#usage)
    - [Register User](#1-register-user)
    - [Apply for Loan](#2-apply-for-loan)
    - [Make Payment](#3-make-payment)
    - [Get Loan Statement](#4-get-loan-statement)

## Overview

The Loan Management System is a Django-based application that allows users to register and apply for loans, make payments, and manage their loan accounts. It includes additional features such as credit score calculation and EMI calculation.

## Features

- User registration
- Credit score calculation using Celery
- Loan application
- EMI calculation and adjustment
- Payment processing
- Get Loan statement

## Setup Instructions

### Prerequisites

- Python 3.x
- Django
- Django REST Framework
- Celery
- Redis (for Celery message broker and backend)
- SQLite (Note: SQLite is being used as default Django database since no specific database was mentioned in the problem statement.)

### Installation

1. **cd into project directory:**
   ```sh
   cd loan-management-system
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install the required packages:**
   ```sh 
   pip install -r requirements.txt
   ```
4. **Apply migrations:**
   ```sh
   python manage.py makemigrations
   python manage.py migrate
   ```
5. **Run the server:**
   ```sh
   python manage.py runserver
   ```
6. **Start Redis server using Docker:**
   ```sh
   docker run -d -p 6379:6379 redis
   ```
7. **Start Celery worker:**
    ```sh
    celery -A loan_management_system worker --loglevel=info
    ```

## API Endpoints

### 1. User Registration

- **Endpoint:** `/api/register-user/`
- **Method:** `POST`
- **Request Fields:**
  - `aadhar_id` (string): Aadhar ID of the user (required)
  - `name` (string): Name of the user (required)
  - `email_id` (string): Email ID of the user (required)
  - `annual_income` (decimal): Annual income of the user (required)
- **Response:**
  - `unique_user_id` (UUID): Unique user identifier
  - **Example Response:**
    ```json
    {
      "unique_user_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    ```

### 2. Apply for Loan

- **Endpoint:** `/api/apply-loan/`
- **Method:** `POST`
- **Request Fields:**
  - `user` (string): UUID generated of the user (required)
  - `loan_type` (string): Type of loan (required)
  - `loan_amount` (decimal): Amount of loan in rupees (required)
  - `interest_rate` (decimal): Rate of interest in percentage (required, minimum 14%)
  - `term_period` (integer): Time period of repayment in months (required)
  - `disbursement_date` (date): Date of disbursal (required, must be a future date)
- **Response:**
  - `error` (string or null): Error string if any, otherwise null
  - `loan_id` (UUID): Unique identifier of the loan
  - `due_dates` (array): List of EMI due dates and amounts
  - **Example Response:**
    ```json
    {
      "error": null,
      "loan_id": "123e4567-e89b-12d3-a456-426614174000",
      "due_dates": [
        {"date": "2024-07-01", "amount_due": 28410.19},
        {"date": "2024-08-01", "amount_due": 28410.19}
      ]
    }
    ```

### 3. Make Payment

- **Endpoint:** `/api/make-payment/`
- **Method:** `POST`
- **Request Fields:**
  - `loan` (UUID): Loan ID (required)
  - `date` (date): Payment date (required)
  - `amount` (decimal): Amount paid (required)
- **Response:**
  - `status` (string): Payment status
  - **Example Response:**
    ```json
    {
      "status": "Payment registered successfully"
    }
    ```

### 4. Get Loan Statement

- **Endpoint:** `/api/get-statement/<loan_id>/`
- **Method:** `GET`
- **Response:**
  - `error` (string or null): None if no error, otherwise error string
  - `past_transactions` (array): List of past transactions with details
    - `date` (date): Transaction date
    - `principal` (decimal): Principal amount paid
    - `interest` (decimal): Interest amount paid
    - `amount_paid` (decimal): Total amount paid
  - `upcoming_transactions` (array): List of upcoming EMIs
    - `date` (date): EMI date
    - `amount_due` (decimal): Amount due on that date
  - **Example Response:**
    ```json
    {
      "error": null,
      "past_transactions": [
        {"date": "2024-07-01", "principal": 15000, "interest": 5000, "amount_paid": 20000},        
      ],
      "upcoming_transactions": [
        {"date": "2024-08-01", "amount_due": 28410.19},
      ]
    }
    ```

## Utility Functions

This project contains several utility functions that perform essential calculations for loan management, such as calculating EMIs and handling payments.

### `calculate_emi`

This function calculates the Equated Monthly Installment (EMI) and the schedule of due dates for a loan.

- **Parameters:**
  - `loan_amount` (float): The principal amount of the loan.
  - `interest_rate` (float): The annual interest rate (in percentage).
  - `term_period` (int): The loan repayment period (in months).
  - `disbursement_date` (datetime): The date when the loan amount is disbursed.

- **Returns:**
  - `emi_amount` (float): The monthly EMI amount.
  - `emi_dates` (list): A list of dictionaries containing the due dates and amounts of each EMI.

- **Formula for EMI Calculation:**

    The Equated Monthly Installment (EMI) is calculated using the following formula:

    $$EMI = P \times \frac{r(1+r)^n}{(1+r)^n - 1}$$

    Where:
    - \( P \) is the loan amount (Principal)
    - \( r \) is the monthly interest rate (annual interest rate divided by 12 and then by 100)
    - \( n \) is the loan tenure in months

- **Example:**
  ```python
  from datetime import datetime
  from utils import calculate_emi

  loan_amount = 500000
  interest_rate = 15
  term_period = 20
  disbursement_date = datetime(2024, 6, 14)

  emi_amount, emi_dates = calculate_emi(loan_amount, interest_rate, term_period, disbursement_date)
  print(emi_amount)
  print(emi_dates)
  ```
<br>

### `payment_handler`

This function adjusts the EMI schedule based on payments made by the user, ensuring that any overpayment or underpayment is distributed correctly.

- **Parameters:**
  - `emi_dates` (list): A list of dictionaries containing the due dates and amounts of each EMI.
  - `payment_date` (datetime): The date when the payment is made.
  - `payment_amount` (float): The amount paid by the user.
  - `max_emi` (float): The maximum EMI amount allowed based on the user’s income.

- **Returns:**
  - `adjusted_emi_dates` (list): The updated list of EMI due dates and amounts after adjusting for the payment.

- **Logic:**
    - Apply payment to the current EMI:
	    - If the payment is equal to the EMI due amount, set the EMI amount due to 0 and remove it from the upcoming transactions.
	    - If the payment is more or less than the EMI due amount, set the EMI amount due to 0, remove it from the upcoming transactions, and carry forward the remaining due amount to the next EMI.
	- Distribute remaining payment to future EMIs:
	    - If the remaining payment is positive, subtract it from the next EMI due amount.
	    - If the remaining payment is negative, add it to the next EMI due amount, ensuring it does not exceed the max_emi.

- **Example:**
  ```python
  from datetime import datetime
  from utils import payment_handler

  emi_dates = [
    {"date": "2024-07-01", "amount_due": 28410.19},
    {"date": "2024-08-01", "amount_due": 28410.19},
    ...
  ]
  payment_date = datetime(2024, 7, 1)
  payment_amount = 20000
  max_emi = 35000

  adjusted_emi_dates = payment_handler(emi_dates, payment_date, payment_amount, max_emi)
  print(adjusted_emi_dates)
  ```
<br>

### `calculate_credit_score` (Celery task)

This asynchronous task triggered during user registration reads the user’s transaction history from a CSV file, calculates the total balance from the transactions, and updates the user’s credit score based on the predefined parameter.

- **Parameters:**
  - `aadhar_id` (string): The Aadhar ID of the user.

- **Task:**
  ```python
  @shared_task
  def calculate_credit_score(aadhar_id):
    user = User.objects.get(aadhar_id=aadhar_id)
    transactions = pd.read_csv("data/transactions_data_backend__1_.csv")
    
    # Filter transactions for the specific user by aadhar_id
    user_transactions = transactions[transactions["user"] == str(user.aadhar_id)]

    # Calculate total balance from user transactions
    total_balance = user_transactions.apply(
        lambda x: x["amount"] if x["transaction_type"] == "CREDIT" else -x["amount"],
        axis=1
    ).sum()

    # Determine credit score based on total balance
    if total_balance >= 1000000:
        credit_score = 900
    elif total_balance <= 100000:
        credit_score = 300
    else:
        credit_score = 300 + ((total_balance - 100000) // 15000) * 10

    user.credit_score = credit_score
    user.save()
  ```

## Usage

Tools like Postman or cURL can be used to test the APIs. The following commands will help you interact with the API endpoints and test the main features of the application.

### 1. Register User

Use this endpoint to register a new user.

**Endpoint:** `/api/register-user/`

**Method:** `POST`

**cURL Command:**
```bash
curl -X POST http://127.0.0.1:8000/api/register-user/ \
-d '{"aadhar_id": "f5abc955-889d-4a17-87b9-45b362eb673b", "name": "Alice", "email_id": "alice@example.com", "annual_income": 700000}' \
-H "Content-Type: application/json"
```

### 2. Apply for Loan

Use this endpoint to apply for a new loan.

**Endpoint:** `/api/apply-loan/`

**Method:** `POST`

**cURL Command:**
```bash
curl -X POST http://127.0.0.1:8000/api/apply-loan/ \
-d '{"user": "123456789012", "loan_type": "Car", "loan_amount": 500000, "interest_rate": 15, "term_period": 20, "disbursement_date": "2024-06-14"}' \
-H "Content-Type: application/json"
```

### 3. Make Payment

Use this endpoint to register a payment made towards an EMI.

**Endpoint:** `/api/make-payment/`

**Method:** `POST`

**cURL Command:**
```bash
curl -X POST http://127.0.0.1:8000/api/make-payment/ \
-d '{"loan": "3b5da63d-9ebb-4738-8d1a-da28d17c6b7c", "date": "2024-07-01", "amount": 20000}' \
-H "Content-Type: application/json"
```

### 4. Get Loan Statement

Use this endpoint to get the loan statement, including past transactions and upcoming EMIs.

**Endpoint:** `/api/get-statement/{loan_id}/`

**Method:** `GET`

**cURL Command:**
```bash
curl -X GET http://127.0.0.1:8000/api/get-statement/3b5da63d-9ebb-4738-8d1a-da28d17c6b7c/ -H "Content-Type: application/json"
```