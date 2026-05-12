"""
Comparison 单元测试：验证 build_comparison / build_variable_rate_comparison 的差额方向、数值一致性、边界条件。
"""

from decimal import Decimal

import pytest

from loan.comparison import build_comparison, build_variable_rate_comparison
from loan.models import LoanRequest


@pytest.fixture
def typical_request() -> LoanRequest:
    return LoanRequest(
        principal=Decimal("1000000"),
        annual_rate=Decimal("4.5"),
        months=360,
        method="equal-installment",
    )


@pytest.fixture
def zero_rate_request() -> LoanRequest:
    return LoanRequest(
        principal=Decimal("100000"),
        annual_rate=Decimal("0"),
        months=12,
        method="equal-installment",
    )


class TestBuildComparison:
    def test_returns_both_schedules(self, typical_request):
        comp = build_comparison(typical_request)
        assert len(comp.equal_principal.installments) == 360
        assert len(comp.equal_installment.installments) == 360

    def test_equal_installment_pays_more_interest(self, typical_request):
        comp = build_comparison(typical_request)
        assert comp.interest_diff > Decimal("0"), "正利率下等额本息总利息应高于等额本金"

    def test_interest_diff_direction(self, typical_request):
        comp = build_comparison(typical_request)
        expected_diff = comp.equal_installment.total_interest - comp.equal_principal.total_interest
        assert comp.interest_diff == expected_diff

    def test_total_payment_diff_matches_schedules(self, typical_request):
        comp = build_comparison(typical_request)
        expected = comp.equal_installment.total_payment - comp.equal_principal.total_payment
        assert comp.total_payment_diff == expected

    def test_saving_ratio_zero_for_zero_rate(self, zero_rate_request):
        comp = build_comparison(zero_rate_request)
        assert comp.saving_ratio == Decimal("0")
        assert comp.interest_diff == Decimal("0")

    def test_saving_ratio_positive_for_typical(self, typical_request):
        comp = build_comparison(typical_request)
        assert comp.saving_ratio > Decimal("0")
        assert comp.saving_ratio < Decimal("100")

    def test_input_method_field_ignored(self, typical_request):
        req_ep = LoanRequest(
            principal=typical_request.principal,
            annual_rate=typical_request.annual_rate,
            months=typical_request.months,
            method="equal-principal",
        )
        comp1 = build_comparison(typical_request)
        comp2 = build_comparison(req_ep)
        assert comp1.interest_diff == comp2.interest_diff
        assert comp1.total_payment_diff == comp2.total_payment_diff

    def test_comparison_is_frozen(self, typical_request):
        from dataclasses import FrozenInstanceError

        comp = build_comparison(typical_request)
        with pytest.raises(FrozenInstanceError):
            comp.interest_diff = Decimal("0")  # type: ignore[misc]

    def test_schedules_last_remaining_zero(self, typical_request):
        comp = build_comparison(typical_request)
        assert comp.equal_principal.installments[-1].remaining == Decimal("0.00")
        assert comp.equal_installment.installments[-1].remaining == Decimal("0.00")


# ---------------------------------------------------------------------------
# build_variable_rate_comparison
# ---------------------------------------------------------------------------


@pytest.fixture
def variable_request() -> LoanRequest:
    """典型香港按揭：100万、cap 3.25%、前24期优惠 2.5%、30年。"""
    return LoanRequest(
        principal=Decimal("1000000"),
        annual_rate=Decimal("3.25"),
        months=360,
        method="variable-installment",
        rate_changes=((1, 24, Decimal("2.5")),),
    )


@pytest.fixture
def variable_request_zero_cap() -> LoanRequest:
    return LoanRequest(
        principal=Decimal("120000"),
        annual_rate=Decimal("0"),
        months=12,
        method="variable-installment",
        rate_changes=((1, 6, Decimal("0")),),
    )


@pytest.fixture
def variable_request_equal_cap() -> LoanRequest:
    """所有区间利率等于封顶利率，节省为 0。"""
    return LoanRequest(
        principal=Decimal("100000"),
        annual_rate=Decimal("3.25"),
        months=12,
        method="variable-installment",
        rate_changes=((1, 12, Decimal("3.25")),),
    )


class TestBuildVariableRateComparison:
    def test_returns_both_schedules(self, variable_request):
        comp = build_variable_rate_comparison(variable_request)
        assert len(comp.baseline.installments) == 360
        assert len(comp.variable.installments) == 360

    def test_baseline_uses_cap_rate_throughout(self, variable_request):
        comp = build_variable_rate_comparison(variable_request)
        for inst in comp.baseline.installments:
            assert inst.annual_rate == Decimal("3.25")

    def test_variable_uses_segment_rate_in_range(self, variable_request):
        comp = build_variable_rate_comparison(variable_request)
        for inst in comp.variable.installments[:24]:
            assert inst.annual_rate == Decimal("2.5")
        for inst in comp.variable.installments[24:]:
            assert inst.annual_rate == Decimal("3.25")

    def test_interest_saved_positive_when_rate_below_cap(self, variable_request):
        comp = build_variable_rate_comparison(variable_request)
        assert comp.interest_saved > Decimal("0"), "优惠利率下浮动方案应节省利息"

    def test_interest_saved_direction(self, variable_request):
        comp = build_variable_rate_comparison(variable_request)
        expected = comp.baseline.total_interest - comp.variable.total_interest
        assert comp.interest_saved == expected

    def test_total_payment_saved_direction(self, variable_request):
        comp = build_variable_rate_comparison(variable_request)
        expected = comp.baseline.total_payment - comp.variable.total_payment
        assert comp.total_payment_saved == expected

    def test_saving_ratio_positive(self, variable_request):
        comp = build_variable_rate_comparison(variable_request)
        assert comp.saving_ratio > Decimal("0")
        assert comp.saving_ratio < Decimal("100")

    def test_saving_ratio_calculation(self, variable_request):
        comp = build_variable_rate_comparison(variable_request)
        expected = (comp.interest_saved / comp.baseline.total_interest * Decimal(100)).quantize(Decimal("0.01"))
        assert comp.saving_ratio == expected

    def test_zero_cap_rate_saving_ratio_is_zero(self, variable_request_zero_cap):
        comp = build_variable_rate_comparison(variable_request_zero_cap)
        assert comp.saving_ratio == Decimal("0")
        assert comp.interest_saved == Decimal("0")

    def test_segments_equal_cap_no_saving(self, variable_request_equal_cap):
        comp = build_variable_rate_comparison(variable_request_equal_cap)
        assert comp.interest_saved == Decimal("0")
        assert comp.saving_ratio == Decimal("0")

    def test_last_remaining_zero_both_schedules(self, variable_request):
        comp = build_variable_rate_comparison(variable_request)
        assert comp.baseline.installments[-1].remaining == Decimal("0.00")
        assert comp.variable.installments[-1].remaining == Decimal("0.00")

    def test_result_is_frozen(self, variable_request):
        from dataclasses import FrozenInstanceError

        comp = build_variable_rate_comparison(variable_request)
        with pytest.raises(FrozenInstanceError):
            comp.interest_saved = Decimal("0")  # type: ignore[misc]

    def test_multiple_segments(self):
        req = LoanRequest(
            principal=Decimal("1000000"),
            annual_rate=Decimal("3.25"),
            months=360,
            method="variable-installment",
            rate_changes=((1, 12, Decimal("2.0")), (13, 24, Decimal("2.5"))),
        )
        comp = build_variable_rate_comparison(req)
        assert comp.interest_saved > Decimal("0")
        assert comp.baseline.installments[-1].remaining == Decimal("0.00")
        assert comp.variable.installments[-1].remaining == Decimal("0.00")
