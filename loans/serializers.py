from rest_framework import serializers
from .models import User, LoanApplication, Payment
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from .utils import calculate_emi, payment_handler

getcontext().prec = 10


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["unique_user_id", "aadhar_id", "name", "email_id", "annual_income"]


class LoanApplicationSerializer(serializers.ModelSerializer):
    user = serializers.UUIDField()
    emi_dates = serializers.SerializerMethodField()

    class Meta:
        model = LoanApplication
        fields = [
            "loan_id",
            "user",
            "loan_type",
            "loan_amount",
            "interest_rate",
            "term_period",
            "disbursement_date",
            "emi_dates",
        ]

    def validate_disbursement_date(self, value):
        if value <= datetime.now().date():
            raise serializers.ValidationError(
                "Disbursement date must be set after today's date."
            )
        return value

    def create(self, validated_data):
        user_id = validated_data.pop("user")
        user = User.objects.get(unique_user_id=user_id)

        # Convert loan_amount, interest_rate, and annual_income to float
        loan_amount = float(validated_data["loan_amount"])
        interest_rate = float(validated_data["interest_rate"])
        annual_income = float(user.annual_income)
        term_period = validated_data["term_period"]
        disbursement_date = validated_data["disbursement_date"]

        # Validate interest rate
        if interest_rate < 14:
            raise serializers.ValidationError("Interest rate should be >= 14%")

        # Calculate EMI using the external function
        emi_amount, emi_dates = calculate_emi(
            loan_amount, interest_rate, term_period, disbursement_date
        )

        # Ensure EMI amount is at most 60% of user's monthly income
        max_emi = annual_income / 12 * 0.6
        if emi_amount > max_emi:
            raise serializers.ValidationError(
                "EMI amount exceeds 60% of the user's monthly income"
            )

        # Calculate total interest earned
        total_interest = emi_amount * term_period - loan_amount
        if total_interest <= 10000:
            raise serializers.ValidationError("Total interest earned should be > 10000")

        validated_data["emi_dates"] = emi_dates
        loan_application = LoanApplication.objects.create(user=user, **validated_data)
        return loan_application

    def get_emi_dates(self, obj):
        return obj.emi_dates


# class PaymentSerializer(serializers.ModelSerializer):
#     loan = serializers.UUIDField()

#     class Meta:
#         model = Payment
#         fields = ["loan", "date", "amount"]

#     def validate(self, data):
#         try:
#             loan = LoanApplication.objects.get(loan_id=data["loan"])
#             data["loan"] = loan
#         except LoanApplication.DoesNotExist:
#             raise serializers.ValidationError("Invalid loan ID")

#         # Check for duplicate payment
#         if Payment.objects.filter(loan=loan, date=data["date"]).exists():
#             raise serializers.ValidationError(
#                 "A payment for this loan on this date already exists"
#             )

#         # Check for previous EMIs due
#         emi_dates = loan.emi_dates
#         for emi in emi_dates:
#             if emi["date"] < str(data["date"]) and emi["amount_due"] > 0:
#                 raise serializers.ValidationError("Previous EMIs are due")

#         return data

#     def create(self, validated_data):
#         loan = validated_data.pop("loan")
#         payment_date = validated_data["date"]
#         payment_amount = float(validated_data["amount"])

#         # Register the payment
#         payment = Payment.objects.create(loan=loan, **validated_data)

#         # Update EMI dates
#         emi_dates = loan.emi_dates
#         remaining_payment = payment_amount
#         user = loan.user
#         max_emi = float(user.annual_income) / 12 * 0.6

#         # Apply payment to the current EMI
#         for emi in emi_dates:
#             if emi["date"] == str(payment_date):
#                 if remaining_payment == emi["amount_due"]:
#                     emi["amount_due"] = 0
#                     remaining_payment = 0
#                 elif remaining_payment > emi["amount_due"]:
#                     remaining_payment -= emi["amount_due"]
#                     emi["amount_due"] = 0
#                 else:
#                     emi["amount_due"] -= remaining_payment
#                     remaining_payment = 0
#                 break

#         # If there's remaining payment, distribute it to future EMIs
#         if remaining_payment > 0:
#             for emi in emi_dates:
#                 if remaining_payment == 0:
#                     break
#                 if emi["amount_due"] > 0:
#                     if remaining_payment >= emi["amount_due"]:
#                         remaining_payment -= emi["amount_due"]
#                         emi["amount_due"] = 0
#                     else:
#                         emi["amount_due"] -= remaining_payment
#                         remaining_payment = 0

#         # Adjust the EMIs to ensure no month is skipped
#         new_emi_dates = []
#         for emi in emi_dates:
#             new_emi_dates.append(emi)
#             if emi["amount_due"] == 0 and remaining_payment > 0:
#                 new_emi_dates.append(
#                     {
#                         "date": (
#                             datetime.strptime(emi["date"], "%Y-%m-%d")
#                             + timedelta(days=30)
#                         ).strftime("%Y-%m-%d"),
#                         "amount_due": remaining_payment,
#                     }
#                 )
#                 remaining_payment = 0

#         loan.emi_dates = [emi for emi in new_emi_dates if emi["amount_due"] > 0]

#         # Adjust the last EMI if there's still remaining principal
#         if remaining_payment > 0:
#             last_emi = loan.emi_dates[-1]
#             last_emi["amount_due"] += remaining_payment

#         loan.save()

#         return payment


# class PaymentSerializer(serializers.ModelSerializer):
#     loan = serializers.UUIDField()

#     class Meta:
#         model = Payment
#         fields = ["loan", "date", "amount"]

#     def validate(self, data):
#         try:
#             loan = LoanApplication.objects.get(loan_id=data["loan"])
#             data["loan"] = loan
#         except LoanApplication.DoesNotExist:
#             raise serializers.ValidationError("Invalid loan ID")

#         # Check for duplicate payment
#         if Payment.objects.filter(loan=loan, date=data["date"]).exists():
#             raise serializers.ValidationError(
#                 "A payment for this loan on this date already exists"
#             )

#         # Check for previous EMIs due
#         emi_dates = loan.emi_dates
#         for emi in emi_dates:
#             if emi["date"] < str(data["date"]) and emi["amount_due"] > 0:
#                 raise serializers.ValidationError("Previous EMIs are due")

#         return data

#     def create(self, validated_data):
#         loan = validated_data.pop("loan")
#         payment_date = validated_data["date"]
#         payment_amount = float(validated_data["amount"])

#         # Register the payment
#         payment = Payment.objects.create(loan=loan, **validated_data)

#         # Update EMI dates using the adjust_emi_dates function
#         user = loan.user
#         max_emi = float(user.annual_income) / 12 * 0.6
#         loan.emi_dates = adjust_emi_dates(
#             loan.emi_dates, payment_date, payment_amount, max_emi
#         )

#         loan.save()

#         return payment


class PaymentSerializer(serializers.ModelSerializer):
    loan = serializers.UUIDField()

    class Meta:
        model = Payment
        fields = ["loan", "date", "amount"]

    def validate(self, data):
        try:
            loan = LoanApplication.objects.get(loan_id=data["loan"])
            data["loan"] = loan
        except LoanApplication.DoesNotExist:
            raise serializers.ValidationError("Invalid loan ID")

        # Check for duplicate payment
        if Payment.objects.filter(loan=loan, date=data["date"]).exists():
            raise serializers.ValidationError(
                "A payment for this loan on this date already exists"
            )

        # Check for previous EMIs due
        emi_dates = loan.emi_dates
        for emi in emi_dates:
            if emi["date"] < str(data["date"]) and emi["amount_due"] > 0:
                raise serializers.ValidationError("Previous EMIs are due")

        return data

    def create(self, validated_data):
        loan = validated_data.pop("loan")
        payment_date = validated_data["date"]
        payment_amount = float(validated_data["amount"])

        # Register the payment
        payment = Payment.objects.create(loan=loan, **validated_data)

        # Adjust EMI dates using payment_handler
        max_emi = float(loan.user.annual_income) / 12 * 0.6
        loan.emi_dates = payment_handler(
            loan.emi_dates, payment_date, payment_amount, max_emi
        )

        loan.save()

        return payment
