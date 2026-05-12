"""
VariableRateInstallmentStrategy 单元测试。

核心不变量：
  1. 末期 remaining == 0
  2. sum(installment.principal) == request.principal
  3. 期数 == months（不延长）
  4. 空 rate_changes → 结果与 EqualInstallmentStrategy 逐期相同
  5. 区间内利率生效，区间外用 cap rate
  6. 利率降低期月供变小，利率恢复期月供变大
"""

from decimal import Decimal

from loan.models import LoanRequest
from loan.strategies.equal_installment import EqualInstallmentStrategy
from loan.strategies.variable_installment import VariableRateInstallmentStrategy

_EI = EqualInstallmentStrategy()
_VI = VariableRateInstallmentStrategy()
_CENT = Decimal("0.01")

CAP = Decimal("3.25")


def _req(months=360, rate_changes=()):
    return LoanRequest(
        principal=Decimal("1000000"),
        annual_rate=CAP,
        months=months,
        method="variable-installment",
        rate_changes=rate_changes,
    )


# ---------------------------------------------------------------------------
# 向后兼容：空 rate_changes 等价于固定利率等额本息
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    def test_empty_rate_changes_first_payment_matches_equal_installment(self):
        """空 rate_changes 时，浮动策略首期月供与固定利率 EI 一致（均基于相同 PMT 公式）。"""
        req = _req()
        vi_sched = _VI.generate(req)
        ei_req = LoanRequest(
            principal=req.principal,
            annual_rate=req.annual_rate,
            months=req.months,
            method="equal-installment",
            rate_changes=(),
        )
        ei_sched = _EI.generate(ei_req)
        assert vi_sched.installments[0].payment == ei_sched.installments[0].payment
        assert vi_sched.installments[-1].remaining == Decimal("0.00")
        assert vi_sched.total_interest > Decimal("0")

    def test_single_period_loan(self):
        req = LoanRequest(
            principal=Decimal("10000"),
            annual_rate=Decimal("12"),
            months=1,
            method="variable-installment",
            rate_changes=(),
        )
        sched = _VI.generate(req)
        assert len(sched.installments) == 1
        assert sched.installments[0].remaining == Decimal("0.00")
        assert sched.installments[0].principal == Decimal("10000")


# ---------------------------------------------------------------------------
# 核心不变量
# ---------------------------------------------------------------------------


class TestInvariants:
    def test_last_remaining_is_zero(self):
        req = _req(rate_changes=((13, 24, Decimal("2.1")),))
        sched = _VI.generate(req)
        assert sched.installments[-1].remaining == Decimal("0.00")

    def test_total_principal_matches(self):
        req = _req(rate_changes=((13, 24, Decimal("2.1")), (25, 36, Decimal("2.5"))))
        sched = _VI.generate(req)
        total = sum(i.principal for i in sched.installments)
        assert total == req.principal

    def test_period_count_fixed(self):
        req = _req(rate_changes=((1, 360, Decimal("1.0")),))
        sched = _VI.generate(req)
        assert len(sched.installments) == 360

    def test_period_numbers_sequential(self):
        req = _req(rate_changes=((13, 24, Decimal("2.1")),))
        sched = _VI.generate(req)
        for idx, inst in enumerate(sched.installments, start=1):
            assert inst.period == idx

    def test_summary_totals_consistent(self):
        req = _req(rate_changes=((13, 24, Decimal("2.1")),))
        sched = _VI.generate(req)
        assert sched.total_payment == sum(i.payment for i in sched.installments)
        assert sched.total_interest == sum(i.interest for i in sched.installments)


# ---------------------------------------------------------------------------
# 利率生效验证
# ---------------------------------------------------------------------------


class TestRateApplication:
    def test_annual_rate_field_inside_segment(self):
        """区间内的 installment.annual_rate 应为区间利率。"""
        segments = ((13, 24, Decimal("2.1")),)
        req = _req(rate_changes=segments)
        sched = _VI.generate(req)
        for inst in sched.installments[12:24]:
            assert inst.annual_rate == Decimal("2.1"), f"期{inst.period}利率应为2.1%"

    def test_annual_rate_field_outside_segment_uses_cap(self):
        """区间外的 installment.annual_rate 应为封顶利率。"""
        segments = ((13, 24, Decimal("2.1")),)
        req = _req(rate_changes=segments)
        sched = _VI.generate(req)
        for inst in sched.installments[:12]:
            assert inst.annual_rate == CAP, f"期{inst.period}利率应为cap {CAP}%"
        for inst in sched.installments[24:]:
            assert inst.annual_rate == CAP, f"期{inst.period}利率应为cap {CAP}%"

    def test_payment_decreases_when_rate_drops(self):
        """利率降低时，新月供应小于降息前的月供。"""
        segments = ((13, 24, Decimal("2.1")),)
        req = _req(rate_changes=segments)
        sched = _VI.generate(req)
        payment_before = sched.installments[11].payment  # 第12期（cap利率）
        payment_after = sched.installments[12].payment  # 第13期（低利率）
        assert payment_after < payment_before

    def test_payment_increases_when_rate_recovers(self):
        """利率恢复时，新月供应大于优惠期月供。"""
        segments = ((13, 24, Decimal("2.1")),)
        req = _req(rate_changes=segments)
        sched = _VI.generate(req)
        payment_low = sched.installments[12].payment  # 第13期（低利率）
        payment_cap = sched.installments[24].payment  # 第25期（cap利率）
        assert payment_cap > payment_low

    def test_interest_calculated_with_segment_rate(self):
        """区间内利息应按区间月利率计算：interest == remaining_before * rc / 12。"""
        segments = ((13, 24, Decimal("2.1")),)
        req = _req(rate_changes=segments)
        sched = _VI.generate(req)
        inst = sched.installments[12]  # 第13期
        remaining_before = sched.installments[11].remaining
        monthly_rate = Decimal("2.1") / 100 / 12
        expected_interest = (remaining_before * monthly_rate).quantize(_CENT)
        assert inst.interest == expected_interest

    def test_multiple_segments(self):
        """多段变化：各段利率均正确生效。"""
        segments = (
            (1, 12, Decimal("2.0")),
            (13, 24, Decimal("2.5")),
            (25, 36, Decimal("3.0")),
        )
        req = _req(rate_changes=segments)
        sched = _VI.generate(req)
        for inst in sched.installments[:12]:
            assert inst.annual_rate == Decimal("2.0")
        for inst in sched.installments[12:24]:
            assert inst.annual_rate == Decimal("2.5")
        for inst in sched.installments[24:36]:
            assert inst.annual_rate == Decimal("3.0")
        for inst in sched.installments[36:]:
            assert inst.annual_rate == CAP


# ---------------------------------------------------------------------------
# 边界条件
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_zero_rate_segment(self):
        """零利率区间：利息为 0。"""
        segments = ((1, 12, Decimal("0")),)
        req = LoanRequest(
            principal=Decimal("120000"),
            annual_rate=Decimal("3.0"),
            months=24,
            method="variable-installment",
            rate_changes=segments,
        )
        sched = _VI.generate(req)
        for inst in sched.installments[:12]:
            assert inst.interest == Decimal("0.00")

    def test_full_period_low_rate_matches_ei(self):
        """全期低利率：结果与用该低利率的等额本息首期月供一致。"""
        low = Decimal("2.0")
        segments = ((1, 360, low),)
        req = _req(rate_changes=segments)
        vi_sched = _VI.generate(req)

        ei_req = LoanRequest(
            principal=req.principal,
            annual_rate=low,
            months=req.months,
            method="equal-installment",
            rate_changes=(),
        )
        ei_sched = _EI.generate(ei_req)
        assert vi_sched.installments[0].payment == ei_sched.installments[0].payment
        assert vi_sched.installments[-1].remaining == Decimal("0.00")

    def test_short_loan_with_rate_change(self):
        """短期贷款（12期）中途变化利率。"""
        req = LoanRequest(
            principal=Decimal("100000"),
            annual_rate=Decimal("3.25"),
            months=12,
            method="variable-installment",
            rate_changes=((7, 12, Decimal("2.0")),),
        )
        sched = _VI.generate(req)
        assert len(sched.installments) == 12
        assert sched.installments[-1].remaining == Decimal("0.00")
        total = sum(i.principal for i in sched.installments)
        assert total == req.principal

    def test_rate_change_at_last_period(self):
        """最后一期变化利率：归零逻辑仍正确。"""
        req = LoanRequest(
            principal=Decimal("100000"),
            annual_rate=Decimal("3.25"),
            months=12,
            method="variable-installment",
            rate_changes=((12, 12, Decimal("2.0")),),
        )
        sched = _VI.generate(req)
        assert sched.installments[-1].remaining == Decimal("0.00")
        assert sched.installments[-1].annual_rate == Decimal("2.0")

    def test_typical_hk_mortgage_scenario(self):
        """典型香港按揭：100万、cap 3.25%、前24期优惠 2.5%。"""
        req = LoanRequest(
            principal=Decimal("1000000"),
            annual_rate=Decimal("3.25"),
            months=360,
            method="variable-installment",
            rate_changes=((1, 24, Decimal("2.5")),),
        )
        sched = _VI.generate(req)
        assert len(sched.installments) == 360
        assert sched.installments[-1].remaining == Decimal("0.00")
        total = sum(i.principal for i in sched.installments)
        assert total == req.principal
        # 优惠期月供应低于 cap 利率下的等额本息月供
        cap_ei_sched = _EI.generate(
            LoanRequest(
                principal=req.principal,
                annual_rate=req.annual_rate,
                months=req.months,
                method="equal-installment",
                rate_changes=(),
            )
        )
        assert sched.installments[0].payment < cap_ei_sched.installments[0].payment
