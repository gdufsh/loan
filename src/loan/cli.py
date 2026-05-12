import argparse
import sys
from decimal import Decimal, InvalidOperation

from loan.comparison import build_comparison, build_variable_rate_comparison
from loan.errors import LoanError, UnknownStrategyError
from loan.models import LoanRequest
from loan.presentation import render_comparison, render_schedule, render_variable_rate_comparison
from loan.rate_schedule import parse_rate_changes
from loan.strategies import STRATEGIES
from loan.validation import validate_request


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="loan",
        description=(
            "贷款还款计划计算器，支持等额本金和等额本息。"
            "使用 --compare 对比两种方式；使用 --rate-changes 计算浮动利率还款计划。"
        ),
    )
    parser.add_argument(
        "--principal", "-p",
        required=True,
        metavar="金额",
        help="贷款本金（元），如 1000000",
    )
    parser.add_argument(
        "--annual-rate", "-r",
        required=True,
        metavar="利率",
        help="年利率（百分比），浮动利率模式下为封顶利率，如 3.25 表示 3.25%%",
    )
    parser.add_argument(
        "--months", "-m",
        required=True,
        type=int,
        metavar="期数",
        help="还款期数（月），如 360",
    )
    parser.add_argument(
        "--method", "-M",
        choices=list(STRATEGIES.keys()),
        default="equal-installment",
        metavar="方式",
        help=f"还款方式：{', '.join(STRATEGIES.keys())}（默认：equal-installment，启用 --compare 时忽略）",
    )
    parser.add_argument(
        "--compare", "-c",
        action="store_true",
        help="对比等额本金和等额本息两种方式（忽略 --method）",
    )
    parser.add_argument(
        "--compare-detail", "-d",
        action="store_true",
        help="在对比模式下额外输出逐期明细（需配合 --compare 使用）",
    )
    parser.add_argument(
        "--rate-changes",
        metavar="区间",
        help="浮动利率区间，格式：x:y:rc[,x:y:rc,...]，如 1:24:2.5,25:36:3.0",
    )
    parser.add_argument(
        "--no-color", "-n",
        action="store_true",
        help="禁用彩色输出，输出纯文本",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        principal = Decimal(args.principal)
        annual_rate = Decimal(args.annual_rate)
    except InvalidOperation:
        print("错误：本金和利率必须为有效数字", file=sys.stderr)
        return 1

    use_rich = not args.no_color

    # 解析浮动利率区间
    rate_changes: tuple = ()
    if args.rate_changes:
        try:
            rate_changes = parse_rate_changes(args.rate_changes)
        except ValueError as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 1

    # --compare + --rate-changes：浮动利率对比模式
    if args.compare and rate_changes:
        if args.method != "equal-installment":
            print("提示：已启用对比模式，--method 参数被忽略", file=sys.stderr)

        request = LoanRequest(
            principal=principal,
            annual_rate=annual_rate,
            months=args.months,
            method="variable-installment",
            rate_changes=rate_changes,
        )
        try:
            validate_request(request)
            comp = build_variable_rate_comparison(request)
        except (LoanError, ValueError) as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 1

        render_variable_rate_comparison(comp, use_rich=use_rich, show_detail=args.compare_detail)
        return 0

    if args.compare:
        if args.method != "equal-installment":
            print("提示：已启用对比模式，--method 参数被忽略", file=sys.stderr)

        request = LoanRequest(
            principal=principal,
            annual_rate=annual_rate,
            months=args.months,
            method="equal-installment",
        )
        try:
            validate_request(request)
        except LoanError as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 1

        comp = build_comparison(request)
        render_comparison(comp, use_rich=use_rich, show_detail=args.compare_detail)
        return 0

    # 浮动利率模式：自动切换到 variable-installment
    if rate_changes:
        method = "variable-installment"
        request = LoanRequest(
            principal=principal,
            annual_rate=annual_rate,
            months=args.months,
            method=method,
            rate_changes=rate_changes,
        )
        try:
            validate_request(request)
            strategy = STRATEGIES[method]()
            schedule = strategy.generate(request)
        except (LoanError, ValueError) as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 1

        render_schedule(schedule, use_rich=use_rich)
        return 0

    method = args.method
    if method not in STRATEGIES:
        raise UnknownStrategyError(f"未知还款方式: {method}")

    request = LoanRequest(
        principal=principal,
        annual_rate=annual_rate,
        months=args.months,
        method=method,
    )

    try:
        validate_request(request)
    except LoanError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    strategy = STRATEGIES[method]()
    schedule = strategy.generate(request)
    render_schedule(schedule, use_rich=use_rich)
    return 0


if __name__ == "__main__":
    sys.exit(main())
