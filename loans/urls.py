from django.urls import path
from .views import RegisterUser, ApplyLoan, MakePayment, GetStatement

urlpatterns = [
    path("api/register-user/", RegisterUser.as_view(), name="register-user"),
    path("api/apply-loan/", ApplyLoan.as_view(), name="apply-loan"),
    path("api/make-payment/", MakePayment.as_view(), name="make-payment"),
    path(
        "api/get-statement/<uuid:loan_id>/",
        GetStatement.as_view(),
        name="get-statement",
    ),
]
