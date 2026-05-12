from decimal import Decimal

from loan.errors import InvalidLoanParameterError
from loan.models import LoanRequest


def validate_request(req: LoanRequest) -> None:
    if req.principal <= Decimal(0):
        raise InvalidLoanParameterError("贷款本金必须大于 0")
    if req.annual_rate < Decimal(0):
        raise InvalidLoanParameterError("年利率不能为负数")
    if req.annual_rate > Decimal(100):
        raise InvalidLoanParameterError("年利率超过 100%，请确认输入单位为百分比（如 4.5 表示 4.5%）")
    if req.months <= 0:
        raise InvalidLoanParameterError("还款期数必须大于 0")
