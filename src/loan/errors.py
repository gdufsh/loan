class LoanError(ValueError):
    pass


class InvalidLoanParameterError(LoanError):
    pass


class UnknownStrategyError(LoanError):
    pass


class InvalidRateScheduleError(LoanError):
    pass
