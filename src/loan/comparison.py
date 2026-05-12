from decimal import Decimal, getcontext

from loan.models import Comparison, LoanRequest, VariableRateComparison
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


def build_variable_rate_comparison(request: LoanRequest) -> VariableRateComparison:
    """生成浮动利率 vs 全程封顶利率（固定）等额本息的对比结果。"""
    baseline_request = LoanRequest(
        principal=request.principal,
        annual_rate=request.annual_rate,
        months=request.months,
        method="equal-installment",
    )
    variable_request = LoanRequest(
        principal=request.principal,
        annual_rate=request.annual_rate,
        months=request.months,
        method="variable-installment",
        rate_changes=request.rate_changes,
    )

    baseline_schedule = STRATEGIES["equal-installment"]().generate(baseline_request)
    variable_schedule = STRATEGIES["variable-installment"]().generate(variable_request)

    interest_saved = baseline_schedule.total_interest - variable_schedule.total_interest
    total_payment_saved = baseline_schedule.total_payment - variable_schedule.total_payment

    if baseline_schedule.total_interest == Decimal("0"):
        saving_ratio = Decimal("0")
    else:
        saving_ratio = (interest_saved / baseline_schedule.total_interest * Decimal(100)).quantize(_CENT)

    return VariableRateComparison(
        baseline=baseline_schedule,
        variable=variable_schedule,
        interest_saved=interest_saved,
        total_payment_saved=total_payment_saved,
        saving_ratio=saving_ratio,
    )
