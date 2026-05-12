import pytest
from decimal import Decimal

from loan.errors import InvalidLoanParameterError
from loan.models import LoanRequest
from loan.validation import validate_request


def _req(**kwargs) -> LoanRequest:
    defaults = dict(principal=Decimal("100000"), annual_rate=Decimal("5"), months=12, method="equal-installment")
    defaults.update(kwargs)
    return LoanRequest(**defaults)


def test_valid_request_passes():
    validate_request(_req())


def test_negative_principal_raises():
    with pytest.raises(InvalidLoanParameterError, match="本金"):
        validate_request(_req(principal=Decimal("-1")))


def test_zero_principal_raises():
    with pytest.raises(InvalidLoanParameterError, match="本金"):
        validate_request(_req(principal=Decimal("0")))


def test_negative_rate_raises():
    with pytest.raises(InvalidLoanParameterError, match="年利率"):
        validate_request(_req(annual_rate=Decimal("-0.1")))


def test_rate_over_100_raises():
    with pytest.raises(InvalidLoanParameterError, match="100%"):
        validate_request(_req(annual_rate=Decimal("101")))


def test_zero_months_raises():
    with pytest.raises(InvalidLoanParameterError, match="期数"):
        validate_request(_req(months=0))


def test_negative_months_raises():
    with pytest.raises(InvalidLoanParameterError, match="期数"):
        validate_request(_req(months=-1))


def test_zero_rate_passes():
    validate_request(_req(annual_rate=Decimal("0")))


def test_rate_exactly_100_raises():
    with pytest.raises(InvalidLoanParameterError):
        validate_request(_req(annual_rate=Decimal("100.01")))
