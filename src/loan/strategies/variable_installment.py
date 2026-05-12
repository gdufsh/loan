from decimal import ROUND_HALF_UP, Decimal, getcontext

from loan.models import Installment, LoanRequest, Schedule
from loan.rate_schedule import resolve_rate
from loan.strategies.base import RepaymentStrategy

getcontext().prec = 28

_CENT = Decimal("0.01")


class VariableRateInstallmentStrategy(RepaymentStrategy):
    """浮动利率等额本息：每期按当期利率与剩余期数重新计算月供（PMT），期数固定不延长。"""

    def generate(self, request: LoanRequest) -> Schedule:
        cap = request.annual_rate
        segments = request.rate_changes
        months = request.months
        remaining = request.principal

        installments: list[Installment] = []

        for period in range(1, months + 1):
            annual_rate_t = resolve_rate(period, cap, segments, cap, months)
            monthly_rate = annual_rate_t / Decimal(100) / Decimal(12)
            n_remaining = months - period + 1
            is_last = period == months

            interest_this = (remaining * monthly_rate).quantize(_CENT, rounding=ROUND_HALF_UP)

            if is_last:
                principal_this = remaining
                payment = principal_this + interest_this
            else:
                if monthly_rate == Decimal(0):
                    payment = (remaining / Decimal(n_remaining)).quantize(_CENT, rounding=ROUND_HALF_UP)
                else:
                    factor = Decimal(1) / ((1 + monthly_rate) ** n_remaining)
                    payment = (remaining * monthly_rate / (1 - factor)).quantize(_CENT, rounding=ROUND_HALF_UP)
                principal_this = (payment - interest_this).quantize(_CENT, rounding=ROUND_HALF_UP)

            remaining = (remaining - principal_this).quantize(_CENT, rounding=ROUND_HALF_UP)

            installments.append(
                Installment(
                    period=period,
                    payment=payment,
                    principal=principal_this,
                    interest=interest_this,
                    remaining=remaining,
                    annual_rate=annual_rate_t,
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
