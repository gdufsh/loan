from abc import ABC, abstractmethod

from loan.models import LoanRequest, Schedule
from loan.validation import validate_request


class RepaymentStrategy(ABC):
    @abstractmethod
    def generate(self, request: LoanRequest) -> Schedule:
        ...

    def _validated_generate(self, request: LoanRequest) -> Schedule:
        validate_request(request)
        return self.generate(request)
