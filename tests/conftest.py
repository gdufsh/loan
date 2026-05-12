import pytest
from decimal import Decimal
from loan.models import LoanRequest


@pytest.fixture
def typical_request() -> LoanRequest:
    """典型房贷：100万、4.5%年利率、30年（360期）"""
    return LoanRequest(
        principal=Decimal("1000000"),
        annual_rate=Decimal("4.5"),
        months=360,
        method="equal-installment",
    )


@pytest.fixture
def short_request() -> LoanRequest:
    """短期贷款：10万、6%、12期"""
    return LoanRequest(
        principal=Decimal("100000"),
        annual_rate=Decimal("6"),
        months=12,
        method="equal-principal",
    )


@pytest.fixture
def zero_rate_request() -> LoanRequest:
    """零利率贷款：10万、0%、12期"""
    return LoanRequest(
        principal=Decimal("100000"),
        annual_rate=Decimal("0"),
        months=12,
        method="equal-installment",
    )
