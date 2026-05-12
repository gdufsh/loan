from decimal import Decimal

from rich.console import Console
from rich.table import Table
from rich import box

from loan.models import Comparison, Schedule

_CONSOLE = Console()


def _fmt(value: Decimal) -> str:
    return f"{value:,.2f}"


def render_schedule(schedule: Schedule, *, use_rich: bool = True) -> None:
    req = schedule.request
    method_label = {
        "equal-principal": "等额本金",
        "equal-installment": "等额本息",
    }.get(req.method, req.method)

    title = (
        f"还款计划 — {method_label} | "
        f"本金 ¥{req.principal:,.2f} | "
        f"年利率 {req.annual_rate}% | "
        f"期限 {req.months} 期"
    )

    if use_rich:
        _render_rich(schedule, title)
    else:
        _render_plain(schedule, title)

    _render_summary(schedule)


def _render_rich(schedule: Schedule, title: str) -> None:
    table = Table(title=title, box=box.SIMPLE_HEAVY, show_lines=False, highlight=True)
    table.add_column("期数", justify="right", style="bold")
    table.add_column("月供(元)", justify="right")
    table.add_column("还本金(元)", justify="right", style="green")
    table.add_column("还利息(元)", justify="right", style="yellow")
    table.add_column("剩余本金(元)", justify="right")

    for inst in schedule.installments:
        table.add_row(
            str(inst.period),
            f"{inst.payment:>12,.2f}",
            f"{inst.principal:>12,.2f}",
            f"{inst.interest:>12,.2f}",
            f"{inst.remaining:>14,.2f}",
        )

    _CONSOLE.print(table)


def _render_plain(schedule: Schedule, title: str) -> None:
    print(title)
    print("-" * 80)
    header = f"{'期数':>4}  {'月供':>12}  {'还本金':>12}  {'还利息':>12}  {'剩余本金':>14}"
    print(header)
    print("-" * 80)
    for inst in schedule.installments:
        print(
            f"{inst.period:>4}  "
            f"{inst.payment:>12,.2f}  "
            f"{inst.principal:>12,.2f}  "
            f"{inst.interest:>12,.2f}  "
            f"{inst.remaining:>14,.2f}"
        )
    print("-" * 80)


def _render_summary(schedule: Schedule) -> None:
    first = schedule.installments[0]
    last = schedule.installments[-1]
    lines = [
        f"  总还款额:   ¥{schedule.total_payment:>14,.2f}",
        f"  总利息:     ¥{schedule.total_interest:>14,.2f}",
        f"  首期月供:   ¥{first.payment:>14,.2f}",
        f"  末期月供:   ¥{last.payment:>14,.2f}",
    ]
    _CONSOLE.print("\n".join(lines))


# ---------------------------------------------------------------------------
# 对比渲染
# ---------------------------------------------------------------------------

def render_comparison(comp: Comparison, *, use_rich: bool = True, show_detail: bool = False) -> None:
    req = comp.equal_principal.request

    header = (
        f"还款方式对比 | 本金 ¥{_fmt(req.principal)} | "
        f"年利率 {req.annual_rate}% | 期限 {req.months} 期"
    )

    if use_rich:
        _render_comparison_rich(comp, header, show_detail)
    else:
        _render_comparison_plain(comp, header, show_detail)


def _render_comparison_rich(comp: Comparison, header: str, show_detail: bool) -> None:
    ep = comp.equal_principal
    ei = comp.equal_installment

    _CONSOLE.print(f"\n[bold]{header}[/bold]\n")

    summary = Table(box=box.SIMPLE_HEAVY, show_header=True, highlight=True)
    summary.add_column("指标", style="bold", min_width=14)
    summary.add_column("等额本金", justify="right", style="green")
    summary.add_column("等额本息", justify="right", style="yellow")
    summary.add_column("差异(EI-EP)", justify="right", style="cyan")

    ep_first = ep.installments[0]
    ei_first = ei.installments[0]
    ep_last = ep.installments[-1]
    ei_last = ei.installments[-1]
    ep_avg = ep.total_payment / len(ep.installments)
    ei_avg = ei.total_payment / len(ei.installments)

    rows = [
        ("首月月供(元)",   _fmt(ep_first.payment),  _fmt(ei_first.payment),  _fmt(ei_first.payment - ep_first.payment)),
        ("末月月供(元)",   _fmt(ep_last.payment),   _fmt(ei_last.payment),   _fmt(ei_last.payment - ep_last.payment)),
        ("月均月供(元)",   _fmt(ep_avg),             _fmt(ei_avg),             _fmt(ei_avg - ep_avg)),
        ("总还款额(元)",   _fmt(ep.total_payment),  _fmt(ei.total_payment),  _fmt(comp.total_payment_diff)),
        ("总利息(元)",     _fmt(ep.total_interest), _fmt(ei.total_interest), _fmt(comp.interest_diff)),
        ("利息节省比例",   f"{comp.saving_ratio}%", "基准",                   "—"),
    ]
    for row in rows:
        summary.add_row(*row)

    _CONSOLE.print(summary)

    if show_detail:
        _render_detail_rich(comp)


def _render_detail_rich(comp: Comparison) -> None:
    ep_insts = comp.equal_principal.installments
    ei_insts = comp.equal_installment.installments

    detail = Table(title="逐期对比明细", box=box.SIMPLE_HEAVY, show_lines=False, highlight=True)
    detail.add_column("期数", justify="right", style="bold")
    detail.add_column("EP月供", justify="right", style="green")
    detail.add_column("EP还本", justify="right", style="green")
    detail.add_column("EP还息", justify="right", style="green")
    detail.add_column("EI月供", justify="right", style="yellow")
    detail.add_column("EI还本", justify="right", style="yellow")
    detail.add_column("EI还息", justify="right", style="yellow")

    for ep_inst, ei_inst in zip(ep_insts, ei_insts):
        detail.add_row(
            str(ep_inst.period),
            _fmt(ep_inst.payment),
            _fmt(ep_inst.principal),
            _fmt(ep_inst.interest),
            _fmt(ei_inst.payment),
            _fmt(ei_inst.principal),
            _fmt(ei_inst.interest),
        )

    _CONSOLE.print(detail)
    _CONSOLE.print(f"  共 {len(ep_insts)} 期\n")


def _render_comparison_plain(comp: Comparison, header: str, show_detail: bool) -> None:
    ep = comp.equal_principal
    ei = comp.equal_installment

    print(f"\n{header}")
    print("=" * 80)

    ep_first = ep.installments[0]
    ei_first = ei.installments[0]
    ep_last = ep.installments[-1]
    ei_last = ei.installments[-1]
    ep_avg = ep.total_payment / len(ep.installments)
    ei_avg = ei.total_payment / len(ei.installments)

    rows = [
        ("首月月供(元)",   _fmt(ep_first.payment),  _fmt(ei_first.payment),  _fmt(ei_first.payment - ep_first.payment)),
        ("末月月供(元)",   _fmt(ep_last.payment),   _fmt(ei_last.payment),   _fmt(ei_last.payment - ep_last.payment)),
        ("月均月供(元)",   _fmt(ep_avg),             _fmt(ei_avg),             _fmt(ei_avg - ep_avg)),
        ("总还款额(元)",   _fmt(ep.total_payment),  _fmt(ei.total_payment),  _fmt(comp.total_payment_diff)),
        ("总利息(元)",     _fmt(ep.total_interest), _fmt(ei.total_interest), _fmt(comp.interest_diff)),
        ("利息节省比例",   f"{comp.saving_ratio}%", "基准",                   "—"),
    ]

    col_w = [16, 14, 14, 14]
    hdr = f"{'指标':<{col_w[0]}}{'等额本金':>{col_w[1]}}{'等额本息':>{col_w[2]}}{'差异(EI-EP)':>{col_w[3]}}"
    print(hdr)
    print("-" * 80)
    for label, ep_val, ei_val, diff_val in rows:
        print(f"{label:<{col_w[0]}}{ep_val:>{col_w[1]}}{ei_val:>{col_w[2]}}{diff_val:>{col_w[3]}}")
    print("=" * 80)

    if show_detail:
        _render_detail_plain(comp)


def _render_detail_plain(comp: Comparison) -> None:
    ep_insts = comp.equal_principal.installments
    ei_insts = comp.equal_installment.installments

    print("\n逐期对比明细")
    print("-" * 90)
    hdr = f"{'期数':>4}  {'EP月供':>10}  {'EP还本':>10}  {'EP还息':>10}  {'EI月供':>10}  {'EI还本':>10}  {'EI还息':>10}"
    print(hdr)
    print("-" * 90)

    for ep_inst, ei_inst in zip(ep_insts, ei_insts):
        print(
            f"{ep_inst.period:>4}  "
            f"{_fmt(ep_inst.payment):>10}  "
            f"{_fmt(ep_inst.principal):>10}  "
            f"{_fmt(ep_inst.interest):>10}  "
            f"{_fmt(ei_inst.payment):>10}  "
            f"{_fmt(ei_inst.principal):>10}  "
            f"{_fmt(ei_inst.interest):>10}"
        )
    print("-" * 90)
    print(f"共 {len(ep_insts)} 期")
