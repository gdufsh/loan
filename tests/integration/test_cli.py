"""
CLI 集成测试：直接调用 main() 验证端到端流程。
"""
import pytest
from unittest.mock import patch

from loan.cli import main


def test_equal_installment_basic():
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "4.5",
        "--months", "12",
        "--method", "equal-installment",
        "--no-color",
    ])
    assert exit_code == 0


def test_equal_principal_basic():
    exit_code = main([
        "--principal", "100000",
        "--annual-rate", "6",
        "--months", "12",
        "--method", "equal-principal",
        "--no-color",
    ])
    assert exit_code == 0


def test_invalid_principal_returns_nonzero(capsys):
    exit_code = main([
        "--principal", "-1000",
        "--annual-rate", "4.5",
        "--months", "12",
        "--no-color",
    ])
    assert exit_code != 0
    err = capsys.readouterr().err
    assert "错误" in err


def test_invalid_rate_returns_nonzero(capsys):
    exit_code = main([
        "--principal", "100000",
        "--annual-rate", "abc",
        "--months", "12",
        "--no-color",
    ])
    assert exit_code != 0
    err = capsys.readouterr().err
    assert "错误" in err


def test_zero_months_returns_nonzero(capsys):
    exit_code = main([
        "--principal", "100000",
        "--annual-rate", "4.5",
        "--months", "0",
        "--no-color",
    ])
    assert exit_code != 0


def test_zero_rate_succeeds():
    exit_code = main([
        "--principal", "100000",
        "--annual-rate", "0",
        "--months", "12",
        "--method", "equal-installment",
        "--no-color",
    ])
    assert exit_code == 0


def test_default_method_is_equal_installment():
    exit_code = main([
        "--principal", "500000",
        "--annual-rate", "5",
        "--months", "60",
        "--no-color",
    ])
    assert exit_code == 0


# ---------------------------------------------------------------------------
# 对比模式
# ---------------------------------------------------------------------------

def test_compare_mode_succeeds():
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "4.5",
        "--months", "360",
        "--compare",
        "--no-color",
    ])
    assert exit_code == 0


def test_compare_outputs_both_method_labels(capsys):
    main([
        "--principal", "1000000",
        "--annual-rate", "4.5",
        "--months", "12",
        "--compare",
        "--no-color",
    ])
    out = capsys.readouterr().out
    assert "等额本金" in out
    assert "等额本息" in out


def test_compare_with_detail(capsys):
    main([
        "--principal", "100000",
        "--annual-rate", "6",
        "--months", "12",
        "--compare",
        "--compare-detail",
        "--no-color",
    ])
    out = capsys.readouterr().out
    assert "逐期对比明细" in out


def test_compare_short_flags():
    exit_code = main(["-p", "500000", "-r", "5", "-m", "60", "-c", "-n"])
    assert exit_code == 0


def test_compare_detail_short_flag(capsys):
    main(["-p", "100000", "-r", "6", "-m", "12", "-c", "-d", "-n"])
    out = capsys.readouterr().out
    assert "逐期对比明细" in out


def test_compare_with_invalid_params_returns_nonzero(capsys):
    exit_code = main([
        "--principal", "-1000",
        "--annual-rate", "4.5",
        "--months", "12",
        "--compare",
        "--no-color",
    ])
    assert exit_code != 0


def test_method_ignored_when_compare_set(capsys):
    exit_code = main([
        "--principal", "500000",
        "--annual-rate", "4.5",
        "--months", "12",
        "--method", "equal-principal",
        "--compare",
        "--no-color",
    ])
    assert exit_code == 0
    err = capsys.readouterr().err
    assert "忽略" in err


def test_compare_zero_rate_succeeds():
    exit_code = main([
        "--principal", "120000",
        "--annual-rate", "0",
        "--months", "12",
        "--compare",
        "--no-color",
    ])
    assert exit_code == 0


# ---------------------------------------------------------------------------
# 浮动利率模式
# ---------------------------------------------------------------------------

def test_rate_changes_basic_succeeds():
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "360",
        "--rate-changes", "13:24:2.1",
        "--no-color",
    ])
    assert exit_code == 0


def test_rate_changes_multiple_segments_succeeds():
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "360",
        "--rate-changes", "1:12:2.5,13:24:2.8,25:36:3.0",
        "--no-color",
    ])
    assert exit_code == 0


def test_rate_changes_output_contains_rate_column(capsys):
    main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "12",
        "--rate-changes", "7:12:2.0",
        "--no-color",
    ])
    out = capsys.readouterr().out
    assert "年利率" in out


def test_rate_changes_rate_change_row_marked(capsys):
    """利率变化行应有标记。"""
    main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "12",
        "--rate-changes", "7:12:2.0",
        "--no-color",
    ])
    out = capsys.readouterr().out
    assert "2.0" in out  # 变化利率出现在输出中


def test_rate_changes_invalid_format_returns_nonzero(capsys):
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "360",
        "--rate-changes", "13:24",  # 缺少 rc
        "--no-color",
    ])
    assert exit_code != 0
    assert "错误" in capsys.readouterr().err


def test_rate_changes_non_numeric_returns_nonzero(capsys):
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "360",
        "--rate-changes", "abc:24:2.1",
        "--no-color",
    ])
    assert exit_code != 0


def test_rate_changes_overlapping_segments_returns_nonzero(capsys):
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "360",
        "--rate-changes", "13:24:2.1,20:30:2.5",
        "--no-color",
    ])
    assert exit_code != 0
    assert "重叠" in capsys.readouterr().err


def test_rate_changes_rc_exceeds_cap_returns_nonzero(capsys):
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "360",
        "--rate-changes", "13:24:4.0",  # 4.0 > cap 3.25
        "--no-color",
    ])
    assert exit_code != 0
    assert "封顶" in capsys.readouterr().err


def test_rate_changes_period_exceeds_months_returns_nonzero(capsys):
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "360",
        "--rate-changes", "13:400:2.1",  # 400 > months 360
        "--no-color",
    ])
    assert exit_code != 0


def test_rate_changes_with_compare_succeeds():
    """--compare 与 --rate-changes 组合：输出浮动利率对比。"""
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "360",
        "--rate-changes", "13:24:2.1",
        "--compare",
        "--no-color",
    ])
    assert exit_code == 0


def test_variable_compare_outputs_labels(capsys):
    main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "12",
        "--rate-changes", "1:6:2.5",
        "--compare",
        "--no-color",
    ])
    out = capsys.readouterr().out
    assert "基准" in out
    assert "实际" in out
    assert "节省" in out


def test_variable_compare_with_detail(capsys):
    main([
        "--principal", "100000",
        "--annual-rate", "3.25",
        "--months", "12",
        "--rate-changes", "1:6:2.5",
        "--compare",
        "--compare-detail",
        "--no-color",
    ])
    out = capsys.readouterr().out
    assert "逐期对比明细" in out


def test_variable_compare_short_flags():
    exit_code = main([
        "-p", "500000", "-r", "3.25", "-m", "60",
        "--rate-changes", "1:12:2.5",
        "-c", "-n",
    ])
    assert exit_code == 0


def test_variable_compare_detail_short_flags(capsys):
    main([
        "-p", "100000", "-r", "3.25", "-m", "12",
        "--rate-changes", "1:6:2.5",
        "-c", "-d", "-n",
    ])
    out = capsys.readouterr().out
    assert "逐期对比明细" in out


def test_variable_compare_segments_equal_cap_succeeds():
    """所有区间利率等于封顶利率，节省为 0，正常输出不报错。"""
    exit_code = main([
        "--principal", "100000",
        "--annual-rate", "3.25",
        "--months", "12",
        "--rate-changes", "1:12:3.25",
        "--compare",
        "--no-color",
    ])
    assert exit_code == 0


def test_variable_compare_invalid_segments_returns_nonzero(capsys):
    """浮动对比模式下非法区间仍被拦截。"""
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "360",
        "--rate-changes", "13:24:4.0",  # rc > cap
        "--compare",
        "--no-color",
    ])
    assert exit_code != 0


def test_rate_changes_zero_rate_segment_succeeds():
    exit_code = main([
        "--principal", "120000",
        "--annual-rate", "3.25",
        "--months", "24",
        "--rate-changes", "1:12:0",
        "--no-color",
    ])
    assert exit_code == 0


def test_rate_changes_typical_hk_mortgage(capsys):
    """典型香港按揭：100万、cap 3.25%、前24期优惠 2.5%，验证输出完整。"""
    exit_code = main([
        "--principal", "1000000",
        "--annual-rate", "3.25",
        "--months", "360",
        "--rate-changes", "1:24:2.5",
        "--no-color",
    ])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "360" in out  # 期数出现
    assert "2.5" in out  # 优惠利率出现
