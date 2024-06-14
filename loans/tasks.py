from celery import shared_task
from .models import User
import pandas as pd
import logging


@shared_task
def calculate_credit_score(aadhar_id):
    user = User.objects.get(aadhar_id=aadhar_id)
    transactions = pd.read_csv("data/transactions_data_backend__1_.csv")
    logging.info(f"Loaded transactions: {transactions.head()}")

    # Filter transactions for the specific user by aadhar_id
    user_transactions = transactions[transactions["user"] == str(user.aadhar_id)]
    logging.info(f"Filtered transactions for user {aadhar_id}: {user_transactions}")

    if user_transactions.empty:
        logging.info(
            f"No transactions found for user {aadhar_id}. Setting default credit score."
        )
        # No transactions found for the user, set credit score to default
        user.credit_score = 300
        user.save()
        return

    # Calculate total balance from user transactions
    total_balance = user_transactions.apply(
        lambda x: x["amount"] if x["transaction_type"] == "CREDIT" else -x["amount"],
        axis=1,
    ).sum()
    logging.info(f"Total balance for user {aadhar_id}: {total_balance}")

    # Determine credit score based on total balance
    if total_balance >= 1000000:
        credit_score = 900
    elif total_balance <= 100000:
        credit_score = 300
    else:
        credit_score = 300 + ((total_balance - 100000) // 15000) * 10

    logging.info(f"Calculated credit score for user {aadhar_id}: {credit_score}")

    # Update user's credit score
    user.credit_score = credit_score
    user.save()
