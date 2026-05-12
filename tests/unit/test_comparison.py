"""
Comparison 单元测试：验证 build_comparison 的差额方向、数值一致性、边界条件。
"""
import pytest
from decimal import Decimal

from loan.comparison import build_comparison
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
