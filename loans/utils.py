from datetime import datetime
from dateutil.relativedelta import relativedelta


def calculate_emi(loan_amount, interest_rate, term_period, disbursement_date):
    monthly_interest_rate = interest_rate / (12 * 100)
    emi_amount = (
        loan_amount
        * monthly_interest_rate
        * ((1 + monthly_interest_rate) ** term_period)
        / (((1 + monthly_interest_rate) ** term_period) - 1)
    )

    emi_dates = []
    remaining_principal = loan_amount

    for i in range(term_period):
        # Calculate interest for the current month
        interest_for_month = remaining_principal * monthly_interest_rate
        principal_for_month = emi_amount - interest_for_month

        # Reduce remaining principal
        remaining_principal -= principal_for_month

        # Calculate EMI due date
        emi_date = (disbursement_date + relativedelta(months=i + 1)).replace(day=1)
        emi_dates.append(
            {
                "date": emi_date.strftime("%Y-%m-%d"),
                "amount_due": round(emi_amount, 2),
            }
        )

    # Adjust the last EMI
    if remaining_principal > 0:
        last_emi_date = (disbursement_date + relativedelta(months=term_period)).replace(
            day=1
        )
        emi_dates[-1] = {
            "date": last_emi_date.strftime("%Y-%m-%d"),
            "amount_due": round(
                remaining_principal + (emi_dates[-1]["amount_due"] - emi_amount), 2
            ),
        }

    return emi_amount, emi_dates


def payment_handler(emi_dates, payment_date, payment_amount, max_emi):
    remaining_payment = payment_amount
    new_emi_dates = []

    # Apply payment to the current EMI
    for emi in emi_dates:
        if emi["date"] == str(payment_date):
            if remaining_payment >= emi["amount_due"]:
                remaining_payment -= emi["amount_due"]
                emi["amount_due"] = 0
            else:
                remaining_due = emi["amount_due"] - remaining_payment
                emi["amount_due"] = 0
                remaining_payment = (
                    -remaining_due
                )  # Set to negative to indicate remaining due
            new_emi_dates.append(emi)
        else:
            new_emi_dates.append(emi)

    # Remove the fully paid EMI from the list
    new_emi_dates = [emi for emi in new_emi_dates if emi["amount_due"] != 0]

    # Distribute remaining due amount to future EMIs, excluding the current month
    for i in range(len(new_emi_dates)):
        if new_emi_dates[i]["date"] > str(payment_date):
            if remaining_payment == 0:
                break
            if remaining_payment > 0:
                # Remaining positive payment, subtract from next month
                if remaining_payment > new_emi_dates[i]["amount_due"]:
                    remaining_payment -= new_emi_dates[i]["amount_due"]
                    new_emi_dates[i]["amount_due"] = 0
                else:
                    new_emi_dates[i]["amount_due"] -= remaining_payment
                    remaining_payment = 0
            else:
                # Remaining negative payment, add to next month
                remaining_due = -remaining_payment
                if new_emi_dates[i]["amount_due"] + remaining_due <= max_emi:
                    new_emi_dates[i]["amount_due"] += remaining_due
                    remaining_payment = 0
                else:
                    excess_amount = (
                        new_emi_dates[i]["amount_due"] + remaining_due - max_emi
                    )
                    new_emi_dates[i]["amount_due"] = max_emi
                    remaining_payment = -excess_amount

    # If there's still remaining due, add it to the last EMI
    if remaining_payment < 0:
        last_emi = new_emi_dates[-1]
        last_emi["amount_due"] += -remaining_payment
        remaining_payment = 0

    # Ensure all EMIs are included and only fully paid EMIs are removed
    adjusted_emi_dates = []
    for emi in new_emi_dates:
        if emi["amount_due"] > 0:
            adjusted_emi_dates.append(emi)

    return adjusted_emi_dates
