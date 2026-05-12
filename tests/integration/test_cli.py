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
