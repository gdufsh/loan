from decimal import Decimal, ROUND_HALF_UP, getcontext

from loan.models import Installment, LoanRequest, Schedule
from loan.strategies.base import RepaymentStrategy

getcontext().prec = 28

_CENT = Decimal("0.01")


class EqualPrincipalStrategy(RepaymentStrategy):
    """等额本金：每月归还相同本金，利息逐月递减。"""

    def generate(self, request: LoanRequest) -> Schedule:
        monthly_rate = request.annual_rate / Decimal(100) / Decimal(12)
        monthly_principal = (request.principal / Decimal(request.months)).quantize(
            _CENT, rounding=ROUND_HALF_UP
        )

        installments: list[Installment] = []
        remaining = request.principal

        for period in range(1, request.months + 1):
            is_last = period == request.months
            # 最后一期本金用差值，确保剩余本金精确归零
            principal_this = remaining if is_last else monthly_principal
            interest_this = (remaining * monthly_rate).quantize(_CENT, rounding=ROUND_HALF_UP)
            payment = principal_this + interest_this
            remaining = (remaining - principal_this).quantize(_CENT, rounding=ROUND_HALF_UP)

            installments.append(
                Installment(
                    period=period,
                    payment=payment,
                    principal=principal_this,
                    interest=interest_this,
                    remaining=remaining,
                )
            )

        total_payment = sum(i.payment for i in installments)
        total_interest = sum(i.interest for i in installments)
        return Schedule(
            request=request,
            installments=tuple(installments),
            total_payment=total_payment,
            total_interest=total_interest,
        )
