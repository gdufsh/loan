from decimal import Decimal, ROUND_HALF_UP, getcontext

from loan.models import Installment, LoanRequest, Schedule
from loan.strategies.base import RepaymentStrategy

getcontext().prec = 28

_CENT = Decimal("0.01")


class EqualInstallmentStrategy(RepaymentStrategy):
    """等额本息（PMT）：每月还款总额固定，前期利息多、本金少。"""

    def generate(self, request: LoanRequest) -> Schedule:
        monthly_rate = request.annual_rate / Decimal(100) / Decimal(12)
        n = request.months
        p = request.principal

        # 零利率特殊处理
        if monthly_rate == Decimal(0):
            monthly_payment = (p / Decimal(n)).quantize(_CENT, rounding=ROUND_HALF_UP)
        else:
            factor = (1 + monthly_rate) ** n
            monthly_payment = (p * monthly_rate * factor / (factor - 1)).quantize(
                _CENT, rounding=ROUND_HALF_UP
            )

        installments: list[Installment] = []
        remaining = p

        for period in range(1, n + 1):
            is_last = period == n
            interest_this = (remaining * monthly_rate).quantize(_CENT, rounding=ROUND_HALF_UP)

            if is_last:
                # 最后一期：本金 = 剩余本金，月供重算，确保剩余精确归零
                principal_this = remaining
                payment = principal_this + interest_this
            else:
                payment = monthly_payment
                principal_this = (payment - interest_this).quantize(_CENT, rounding=ROUND_HALF_UP)

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
