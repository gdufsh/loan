"""
核心算法单元测试。
覆盖：正确性、边界条件、不变量（末期归零、总本金匹配）。
"""

from decimal import Decimal

from loan.models import LoanRequest
from loan.strategies.equal_installment import EqualInstallmentStrategy
from loan.strategies.equal_principal import EqualPrincipalStrategy

_EP = EqualPrincipalStrategy()
_EI = EqualInstallmentStrategy()
_CENT = Decimal("0.01")


# ---------------------------------------------------------------------------
# 等额本金
# ---------------------------------------------------------------------------


class TestEqualPrincipal:
    def test_last_remaining_is_zero(self, short_request):
        sched = _EP.generate(short_request)
        assert sched.installments[-1].remaining == Decimal("0.00")

    def test_total_principal_matches(self, short_request):
        sched = _EP.generate(short_request)
        total_principal = sum(i.principal for i in sched.installments)
        assert total_principal == short_request.principal

    def test_monthly_principal_fixed(self, short_request):
        """除最后一期外，每期本金应相等（允许最后一期有微小差异）。"""
        sched = _EP.generate(short_request)
        principals = [i.principal for i in sched.installments[:-1]]
        assert len(set(principals)) == 1, "前 n-1 期本金应相同"

    def test_interest_decreases(self, short_request):
        sched = _EP.generate(short_request)
        interests = [i.interest for i in sched.installments]
        assert all(a >= b for a, b in zip(interests, interests[1:])), "利息应单调不增"

    def test_payment_decreases(self, short_request):
        sched = _EP.generate(short_request)
        payments = [i.payment for i in sched.installments]
        assert all(a >= b for a, b in zip(payments, payments[1:])), "月供应单调不增"

    def test_zero_rate(self, zero_rate_request):
        req = LoanRequest(
            principal=Decimal("120000"),
            annual_rate=Decimal("0"),
            months=12,
            method="equal-principal",
        )
        sched = _EP.generate(req)
        assert sched.installments[-1].remaining == Decimal("0.00")
        assert all(i.interest == Decimal("0.00") for i in sched.installments)

    def test_single_period(self):
        req = LoanRequest(
            principal=Decimal("10000"),
            annual_rate=Decimal("12"),
            months=1,
            method="equal-principal",
        )
        sched = _EP.generate(req)
        assert len(sched.installments) == 1
        assert sched.installments[0].remaining == Decimal("0.00")
        assert sched.installments[0].principal == Decimal("10000")

    def test_long_term_360(self, typical_request):
        req = LoanRequest(
            principal=typical_request.principal,
            annual_rate=typical_request.annual_rate,
            months=360,
            method="equal-principal",
        )
        sched = _EP.generate(req)
        assert len(sched.installments) == 360
        assert sched.installments[-1].remaining == Decimal("0.00")
        total = sum(i.principal for i in sched.installments)
        assert total == req.principal

    def test_summary_totals(self, short_request):
        sched = _EP.generate(short_request)
        expected_payment = sum(i.payment for i in sched.installments)
        expected_interest = sum(i.interest for i in sched.installments)
        assert sched.total_payment == expected_payment
        assert sched.total_interest == expected_interest

    def test_period_numbers_sequential(self, short_request):
        sched = _EP.generate(short_request)
        for idx, inst in enumerate(sched.installments, start=1):
            assert inst.period == idx


# ---------------------------------------------------------------------------
# 等额本息
# ---------------------------------------------------------------------------


class TestEqualInstallment:
    def test_last_remaining_is_zero(self, typical_request):
        sched = _EI.generate(typical_request)
        assert sched.installments[-1].remaining == Decimal("0.00")

    def test_total_principal_matches(self, typical_request):
        sched = _EI.generate(typical_request)
        total_principal = sum(i.principal for i in sched.installments)
        assert total_principal == typical_request.principal

    def test_monthly_payment_fixed(self, typical_request):
        """前 n-1 期月供应相同（最后一期因差值修正可能略有差异）。"""
        sched = _EI.generate(typical_request)
        payments = [i.payment for i in sched.installments[:-1]]
        assert len(set(payments)) == 1, "前 n-1 期月供应相同"

    def test_interest_decreases(self, typical_request):
        sched = _EI.generate(typical_request)
        interests = [i.interest for i in sched.installments]
        assert all(a >= b for a, b in zip(interests, interests[1:])), "利息应单调不增"

    def test_principal_increases(self, typical_request):
        """等额本息中，每期还本金应单调不减。"""
        sched = _EI.generate(typical_request)
        principals = [i.principal for i in sched.installments]
        assert all(a <= b for a, b in zip(principals, principals[1:])), "每期本金应单调不减"

    def test_zero_rate(self, zero_rate_request):
        sched = _EI.generate(zero_rate_request)
        assert sched.installments[-1].remaining == Decimal("0.00")
        assert all(i.interest == Decimal("0.00") for i in sched.installments)
        # 零利率下月供 = 本金 / 期数
        expected = (zero_rate_request.principal / Decimal(zero_rate_request.months)).quantize(Decimal("0.01"))
        for inst in sched.installments[:-1]:
            assert inst.payment == expected

    def test_single_period(self):
        req = LoanRequest(
            principal=Decimal("10000"),
            annual_rate=Decimal("12"),
            months=1,
            method="equal-installment",
        )
        sched = _EI.generate(req)
        assert len(sched.installments) == 1
        assert sched.installments[0].remaining == Decimal("0.00")
        assert sched.installments[0].principal == Decimal("10000")

    def test_long_term_360(self, typical_request):
        sched = _EI.generate(typical_request)
        assert len(sched.installments) == 360
        assert sched.installments[-1].remaining == Decimal("0.00")

    def test_known_pmt_value(self):
        """
        参考值：本金100万，年利率4.5%，360期
        Excel PMT(4.5%/12, 360, -1000000) ≈ 5066.85
        允许 ±0.01 误差（末位舍入）。
        """
        req = LoanRequest(
            principal=Decimal("1000000"),
            annual_rate=Decimal("4.5"),
            months=360,
            method="equal-installment",
        )
        sched = _EI.generate(req)
        first_payment = sched.installments[0].payment
        assert abs(first_payment - Decimal("5066.85")) <= Decimal("0.01")

    def test_summary_totals(self, typical_request):
        sched = _EI.generate(typical_request)
        expected_payment = sum(i.payment for i in sched.installments)
        expected_interest = sum(i.interest for i in sched.installments)
        assert sched.total_payment == expected_payment
        assert sched.total_interest == expected_interest

    def test_period_numbers_sequential(self, typical_request):
        sched = _EI.generate(typical_request)
        for idx, inst in enumerate(sched.installments, start=1):
            assert inst.period == idx
