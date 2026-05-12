"""
presentation 渲染单元测试：验证 render_comparison / render_variable_rate_comparison 纯文本输出包含关键字符串。
"""

from decimal import Decimal

import pytest

from loan.comparison import build_comparison, build_variable_rate_comparison
from loan.models import LoanRequest
from loan.presentation import render_comparison, render_variable_rate_comparison


@pytest.fixture
def comp():
    req = LoanRequest(
        principal=Decimal("1000000"),
        annual_rate=Decimal("4.5"),
        months=360,
        method="equal-installment",
    )
    return build_comparison(req)


@pytest.fixture
def comp_zero_rate():
    req = LoanRequest(
        principal=Decimal("120000"),
        annual_rate=Decimal("0"),
        months=12,
        method="equal-installment",
    )
    return build_comparison(req)


class TestRenderComparison:
    def test_summary_contains_method_labels(self, comp, capsys):
        render_comparison(comp, use_rich=False)
        out = capsys.readouterr().out
        assert "等额本金" in out
        assert "等额本息" in out

    def test_summary_contains_interest_row(self, comp, capsys):
        render_comparison(comp, use_rich=False)
        out = capsys.readouterr().out
        assert "总利息" in out

    def test_summary_contains_formatted_numbers(self, comp, capsys):
        render_comparison(comp, use_rich=False)
        out = capsys.readouterr().out
        assert "," in out  # 千分位分隔符

    def test_summary_contains_saving_ratio(self, comp, capsys):
        render_comparison(comp, use_rich=False)
        out = capsys.readouterr().out
        assert "节省" in out
        assert "%" in out

    def test_no_detail_by_default(self, comp, capsys):
        render_comparison(comp, use_rich=False)
        out = capsys.readouterr().out
        assert "逐期对比明细" not in out

    def test_show_detail_includes_per_period_rows(self, comp, capsys):
        render_comparison(comp, use_rich=False, show_detail=True)
        out = capsys.readouterr().out
        assert "逐期对比明细" in out
        assert len(out.splitlines()) > 370, "360期明细应有足够行数"

    def test_show_detail_shows_period_count(self, comp, capsys):
        render_comparison(comp, use_rich=False, show_detail=True)
        out = capsys.readouterr().out
        assert "360" in out

    def test_zero_rate_saving_ratio_zero(self, comp_zero_rate, capsys):
        render_comparison(comp_zero_rate, use_rich=False)
        out = capsys.readouterr().out
        assert "0%" in out


# ---------------------------------------------------------------------------
# render_variable_rate_comparison
# ---------------------------------------------------------------------------


@pytest.fixture
def variable_comp():
    req = LoanRequest(
        principal=Decimal("1000000"),
        annual_rate=Decimal("3.25"),
        months=360,
        method="variable-installment",
        rate_changes=((1, 24, Decimal("2.5")),),
    )
    return build_variable_rate_comparison(req)


@pytest.fixture
def variable_comp_zero_saving():
    req = LoanRequest(
        principal=Decimal("100000"),
        annual_rate=Decimal("3.25"),
        months=12,
        method="variable-installment",
        rate_changes=((1, 12, Decimal("3.25")),),
    )
    return build_variable_rate_comparison(req)


class TestRenderVariableRateComparison:
    def test_contains_baseline_and_variable_labels(self, variable_comp, capsys):
        render_variable_rate_comparison(variable_comp, use_rich=False)
        out = capsys.readouterr().out
        assert "基准" in out
        assert "实际" in out

    def test_contains_saving_label(self, variable_comp, capsys):
        render_variable_rate_comparison(variable_comp, use_rich=False)
        out = capsys.readouterr().out
        assert "节省" in out

    def test_contains_interest_row(self, variable_comp, capsys):
        render_variable_rate_comparison(variable_comp, use_rich=False)
        out = capsys.readouterr().out
        assert "总利息" in out

    def test_contains_formatted_numbers(self, variable_comp, capsys):
        render_variable_rate_comparison(variable_comp, use_rich=False)
        out = capsys.readouterr().out
        assert "," in out  # 千分位分隔符

    def test_contains_saving_ratio_percentage(self, variable_comp, capsys):
        render_variable_rate_comparison(variable_comp, use_rich=False)
        out = capsys.readouterr().out
        assert "%" in out

    def test_no_detail_by_default(self, variable_comp, capsys):
        render_variable_rate_comparison(variable_comp, use_rich=False)
        out = capsys.readouterr().out
        assert "逐期对比明细" not in out

    def test_show_detail_includes_per_period_rows(self, variable_comp, capsys):
        render_variable_rate_comparison(variable_comp, use_rich=False, show_detail=True)
        out = capsys.readouterr().out
        assert "逐期对比明细" in out
        assert len(out.splitlines()) > 370

    def test_show_detail_contains_annual_rate_column(self, variable_comp, capsys):
        render_variable_rate_comparison(variable_comp, use_rich=False, show_detail=True)
        out = capsys.readouterr().out
        assert "2.5" in out  # 优惠区间利率出现在明细中

    def test_zero_saving_shows_zero(self, variable_comp_zero_saving, capsys):
        render_variable_rate_comparison(variable_comp_zero_saving, use_rich=False)
        out = capsys.readouterr().out
        assert "0.00" in out  # 节省额为零

    def test_contains_cap_rate_info(self, variable_comp, capsys):
        render_variable_rate_comparison(variable_comp, use_rich=False)
        out = capsys.readouterr().out
        assert "3.25" in out  # 封顶利率出现在标题或汇总中
