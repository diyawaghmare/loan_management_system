from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, LoanApplication, Payment
from .serializers import UserSerializer, LoanApplicationSerializer, PaymentSerializer
from .tasks import calculate_credit_score


class RegisterUser(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            calculate_credit_score.delay(user.id)  # Trigger async task
            return Response(
                {"unique_user_id": user.unique_user_id}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class ApplyLoan(APIView):
#     def post(self, request):
#         serializer = LoanApplicationSerializer(data=request.data)
#         if serializer.is_valid():
#             user_id = serializer.validated_data["user"]
#             user = User.objects.get(unique_user_id=user_id)
#             if user.credit_score < 450 or user.annual_income < 150000:
#                 return Response(
#                     {"error": "User does not meet the criteria for loan application"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )
#             # Validate loan amount based on loan type
#             loan_amount = serializer.validated_data["loan_amount"]
#             loan_type = serializer.validated_data["loan_type"]
#             if (
#                 (loan_type == "Car" and loan_amount > 750000)
#                 or (loan_type == "Home" and loan_amount > 8500000)
#                 or (loan_type == "Education" and loan_amount > 5000000)
#                 or (loan_type == "Personal" and loan_amount > 1000000)
#             ):
#                 return Response(
#                     {
#                         "error": "Loan amount exceeds the limit for the selected loan type"
#                     },
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )
#             loan = serializer.save()
#             return Response({"loan_id": loan.loan_id}, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class ApplyLoan(APIView):
    def post(self, request):
        serializer = LoanApplicationSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data["user"]
            try:
                user = User.objects.get(unique_user_id=user_id)
                # Validate user's credit score and annual income
                if user.credit_score < 450 or user.annual_income < 150000:
                    return Response(
                        {
                            "error": "User does not meet the criteria for loan application"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                loan_amount = serializer.validated_data["loan_amount"]
                loan_type = serializer.validated_data["loan_type"]
                interest_rate = serializer.validated_data["interest_rate"]

                # Validate loan amount based on loan type
                loan_limits = {
                    "Car": 750000,
                    "Home": 8500000,
                    "Education": 5000000,
                    "Personal": 1000000,
                }
                if loan_amount > loan_limits.get(loan_type, 0):
                    return Response(
                        {
                            "error": "Loan amount exceeds the limit for the selected loan type"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Validate interest rate
                if interest_rate < 14:
                    return Response(
                        {"error": "Interest rate should be >= 14%"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                loan = serializer.save()
                return Response(
                    {
                        "error": None,
                        "loan_id": loan.loan_id,
                        "due_dates": loan.emi_dates,
                    },
                    status=status.HTTP_200_OK,
                )
            except User.DoesNotExist:
                return Response(
                    {"error": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MakePayment(APIView):
    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save()
            return Response(
                {"status": "Payment registered successfully"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetStatement(APIView):
    def get(self, request, loan_id):
        try:
            loan = LoanApplication.objects.get(loan_id=loan_id)
            if loan.is_closed:
                return Response(
                    {"error": "Loan is closed"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate past transactions and upcoming EMIs
            past_transactions = Payment.objects.filter(loan=loan).values(
                "date", "amount"
            )
            upcoming_transactions = loan.emi_dates

            return Response(
                {
                    "past_transactions": past_transactions,
                    "upcoming_transactions": upcoming_transactions,
                },
                status=status.HTTP_200_OK,
            )
        except LoanApplication.DoesNotExist:
            return Response(
                {"error": "Loan does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )
