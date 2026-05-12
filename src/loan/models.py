from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class LoanRequest:
    principal: Decimal  # 贷款本金（元）
    annual_rate: Decimal  # 年利率（百分比），浮动利率模式下为封顶利率
    months: int  # 还款期数
    method: str  # 还款方式标识
    # 浮动利率区间：((start, end, rate), ...)，未覆盖期数使用 annual_rate
    rate_changes: tuple[tuple[int, int, Decimal], ...] = field(default=())


@dataclass(frozen=True)
class Installment:
    period: int  # 期数（从 1 开始）
    payment: Decimal  # 月供
    principal: Decimal  # 当期还本金
    interest: Decimal  # 当期还利息
    remaining: Decimal  # 剩余本金
    annual_rate: Decimal = field(default=Decimal("0"))  # 当期年利率


@dataclass(frozen=True)
class Schedule:
    request: LoanRequest
    installments: tuple[Installment, ...]
    total_payment: Decimal  # 总还款额
    total_interest: Decimal  # 总利息


@dataclass(frozen=True)
class Comparison:
    """两种还款方式的对比结果。
    interest_diff = equal_installment.total_interest - equal_principal.total_interest
    正值代表等额本息多付的利息。
    """

    equal_principal: Schedule
    equal_installment: Schedule
    interest_diff: Decimal  # EI 总利息 - EP 总利息（正值=EI多付）
    total_payment_diff: Decimal  # EI 总还款 - EP 总还款
    saving_ratio: Decimal  # 选等额本金节省的利息比例（基于 EI），零利率时为 0


@dataclass(frozen=True)
class VariableRateComparison:
    """浮动利率 vs 封顶利率（固定）等额本息对比结果。
    interest_saved = baseline.total_interest - variable.total_interest
    正值代表因浮动利率优惠节省的利息。
    """

    baseline: Schedule  # 全程封顶利率的固定等额本息
    variable: Schedule  # 浮动利率等额本息
    interest_saved: Decimal  # 节省利息（基准-实际，正值=省钱）
    total_payment_saved: Decimal  # 节省总还款（基准-实际）
    saving_ratio: Decimal  # 节省利息 / 基准总利息 * 100，零利率时为 0
