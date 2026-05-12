from loan.strategies.equal_installment import EqualInstallmentStrategy
from loan.strategies.equal_principal import EqualPrincipalStrategy

STRATEGIES: dict[str, type] = {
    "equal-principal": EqualPrincipalStrategy,
    "equal-installment": EqualInstallmentStrategy,
}
