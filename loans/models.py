from django.db import models
import uuid


class User(models.Model):
    unique_user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    aadhar_id = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=100)
    email_id = models.EmailField(unique=True)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2)
    credit_score = models.IntegerField(default=300)


class LoanApplication(models.Model):
    LOAN_TYPES = (
        ("Car", "Car"),
        ("Home", "Home"),
        ("Education", "Education"),
        ("Personal", "Personal"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=10, choices=LOAN_TYPES)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.FloatField()
    term_period = models.IntegerField()  # in months
    disbursement_date = models.DateField()
    loan_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    emi_dates = models.JSONField(
        default=list
    )  # List of dicts with 'date' and 'amount_due'
    is_closed = models.BooleanField(default=False)


class Payment(models.Model):
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
