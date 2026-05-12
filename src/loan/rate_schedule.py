from decimal import Decimal, InvalidOperation

RateSegment = tuple[int, int, Decimal]  # (start, end, rate)


def parse_rate_changes(spec: str) -> tuple[RateSegment, ...]:
    """解析 '--rate-changes' 参数字符串。

    格式：x:y:rc[,x:y:rc,...]
      x  = 开始期数（含，>= 1）
      y  = 结束期数（含，>= x）
      rc = 该区间年利率百分比（>= 0）
    """
    spec = spec.strip()
    if not spec:
        return ()

    segments: list[RateSegment] = []
    for part in spec.split(","):
        part = part.strip()
        fields = part.split(":")
        if len(fields) != 3:
            raise ValueError(f"格式错误：'{part}'，应为 x:y:rc（如 13:24:2.1）")

        try:
            start = int(fields[0])
        except ValueError:
            raise ValueError(f"期数必须为整数，无法解析：'{fields[0]}'")

        try:
            end = int(fields[1])
        except ValueError:
            raise ValueError(f"期数必须为整数，无法解析：'{fields[1]}'")

        try:
            rate = Decimal(fields[2])
        except InvalidOperation:
            raise ValueError(f"利率必须为数字，无法解析：'{fields[2]}'")

        if start < 1:
            raise ValueError(f"期数必须 >= 1，实际：{start}")
        if end < 1:
            raise ValueError(f"期数必须 >= 1，实际：{end}")
        if start > end:
            raise ValueError(f"开始期数 {start} 不能大于结束期数 {end}")
        if rate < Decimal("0"):
            raise ValueError(f"利率不能为负数，实际：{rate}")

        segments.append((start, end, rate))

    return tuple(segments)


def resolve_rate(
    period: int,
    default_rate: Decimal,
    segments: tuple[RateSegment, ...],
    cap_rate: Decimal,
    months: int,
) -> Decimal:
    """返回指定期数的实际年利率，并校验所有区间合法性。

    校验规则：
    - 每个区间的 end <= months
    - rc <= cap_rate
    - 区间之间不能重叠
    """
    _validate_segments(segments, cap_rate, months)

    for start, end, rate in segments:
        if start <= period <= end:
            return rate
    return default_rate


def _validate_segments(
    segments: tuple[RateSegment, ...],
    cap_rate: Decimal,
    months: int,
) -> None:
    for start, end, rate in segments:
        if end > months:
            raise ValueError(f"期数 {end} 超过总期数 {months}")
        if rate > cap_rate:
            raise ValueError(f"区间利率 {rate}% 超过封顶利率 {cap_rate}%")

    sorted_segs = sorted(segments, key=lambda s: s[0])
    for i in range(len(sorted_segs) - 1):
        curr_end = sorted_segs[i][1]
        next_start = sorted_segs[i + 1][0]
        if curr_end >= next_start:
            raise ValueError(f"区间重叠：{sorted_segs[i][:2]} 与 {sorted_segs[i + 1][:2]}")
