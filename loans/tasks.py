from celery import shared_task
from .models import User
import pandas as pd


@shared_task
def calculate_credit_score(user_id):
    user = User.objects.get(id=user_id)
    # Read the transactions CSV file
    transactions = pd.read_csv("data/transactions_data_backend__1_.csv")
    # Filter transactions for the specific user by UUID
    user_transactions = transactions[transactions["user"] == str(user.unique_user_id)]

    # Calculate total balance from user transactions
    total_balance = user_transactions.apply(
        lambda x: x["amount"] if x["transaction_type"] == "CREDIT" else -x["amount"],
        axis=1,
    ).sum()

    # Determine credit score based on total balance
    if total_balance >= 1000000:
        credit_score = 900
    elif total_balance <= 100000:
        credit_score = 300
    else:
        credit_score = 300 + ((total_balance - 100000) // 15000) * 10

    # Update user's credit score
    user.credit_score = credit_score
    user.save()
