from decimal import Decimal, getcontext

from loan.models import Comparison, LoanRequest
from loan.strategies import STRATEGIES

getcontext().prec = 28

_CENT = Decimal("0.01")


def build_comparison(request: LoanRequest) -> Comparison:
    """基于贷款参数生成两种还款方式的对比结果。method 字段被忽略，始终计算两种方式。"""
    ep_request = LoanRequest(
        principal=request.principal,
        annual_rate=request.annual_rate,
        months=request.months,
        method="equal-principal",
    )
    ei_request = LoanRequest(
        principal=request.principal,
        annual_rate=request.annual_rate,
        months=request.months,
        method="equal-installment",
    )

    ep_schedule = STRATEGIES["equal-principal"]().generate(ep_request)
    ei_schedule = STRATEGIES["equal-installment"]().generate(ei_request)

    interest_diff = ei_schedule.total_interest - ep_schedule.total_interest
    total_payment_diff = ei_schedule.total_payment - ep_schedule.total_payment

    if ei_schedule.total_interest == Decimal("0"):
        saving_ratio = Decimal("0")
    else:
        saving_ratio = (interest_diff / ei_schedule.total_interest * Decimal(100)).quantize(_CENT)

    return Comparison(
        equal_principal=ep_schedule,
        equal_installment=ei_schedule,
        interest_diff=interest_diff,
        total_payment_diff=total_payment_diff,
        saving_ratio=saving_ratio,
    )
