from loan.strategies.equal_installment import EqualInstallmentStrategy
from loan.strategies.equal_principal import EqualPrincipalStrategy
from loan.strategies.variable_installment import VariableRateInstallmentStrategy

STRATEGIES: dict[str, type] = {
    "equal-principal": EqualPrincipalStrategy,
    "equal-installment": EqualInstallmentStrategy,
    "variable-installment": VariableRateInstallmentStrategy,
}
