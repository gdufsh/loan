"""
rate_schedule 解析器与 resolve_rate 单元测试。

格式：--rate-changes x:y:rc[,x:y:rc,...]
  x  = 开始期数（含）
  y  = 结束期数（含）
  rc = 该区间利率（年利率百分比，不能超过 cap rate）

未被覆盖的期数使用默认 cap rate（即 -r 参数值）。
"""

from decimal import Decimal

import pytest

from loan.rate_schedule import parse_rate_changes, resolve_rate

CAP = Decimal("3.25")


# ---------------------------------------------------------------------------
# parse_rate_changes
# ---------------------------------------------------------------------------


class TestParseRateChanges:
    def test_single_segment(self):
        result = parse_rate_changes("13:24:2.1")
        assert result == ((13, 24, Decimal("2.1")),)

    def test_multiple_segments(self):
        result = parse_rate_changes("1:12:2.5,13:24:2.8,25:36:3.0")
        assert result == (
            (1, 12, Decimal("2.5")),
            (13, 24, Decimal("2.8")),
            (25, 36, Decimal("3.0")),
        )

    def test_empty_string_returns_empty(self):
        assert parse_rate_changes("") == ()

    def test_whitespace_stripped(self):
        result = parse_rate_changes(" 13:24:2.1 , 25:36:2.5 ")
        assert result == (
            (13, 24, Decimal("2.1")),
            (25, 36, Decimal("2.5")),
        )

    def test_invalid_format_missing_field_raises(self):
        with pytest.raises(ValueError, match="格式"):
            parse_rate_changes("13:24")

    def test_invalid_format_extra_field_raises(self):
        with pytest.raises(ValueError, match="格式"):
            parse_rate_changes("13:24:2.1:extra")

    def test_non_numeric_start_raises(self):
        with pytest.raises(ValueError):
            parse_rate_changes("abc:24:2.1")

    def test_non_numeric_end_raises(self):
        with pytest.raises(ValueError):
            parse_rate_changes("13:abc:2.1")

    def test_non_numeric_rate_raises(self):
        with pytest.raises(ValueError):
            parse_rate_changes("13:24:abc")

    def test_start_greater_than_end_raises(self):
        with pytest.raises(ValueError, match="开始期数"):
            parse_rate_changes("24:13:2.1")

    def test_start_equals_end_valid(self):
        result = parse_rate_changes("13:13:2.1")
        assert result == ((13, 13, Decimal("2.1")),)

    def test_zero_start_raises(self):
        with pytest.raises(ValueError, match="期数"):
            parse_rate_changes("0:12:2.1")

    def test_negative_start_raises(self):
        with pytest.raises(ValueError, match="期数"):
            parse_rate_changes("-1:12:2.1")

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="利率"):
            parse_rate_changes("13:24:-1.0")


# ---------------------------------------------------------------------------
# resolve_rate —— 校验区间合法性
# ---------------------------------------------------------------------------


class TestValidateSegments:
    def test_overlapping_segments_raises(self):
        segments = ((13, 24, Decimal("2.1")), (20, 30, Decimal("2.5")))
        with pytest.raises(ValueError, match="重叠"):
            resolve_rate(1, CAP, segments, CAP, months=360)

    def test_adjacent_segments_valid(self):
        segments = ((13, 24, Decimal("2.1")), (25, 36, Decimal("2.5")))
        resolve_rate(1, CAP, segments, CAP, months=360)  # 不应抛出

    def test_segment_period_exceeds_months_raises(self):
        segments = ((13, 400, Decimal("2.1")),)
        with pytest.raises(ValueError, match="期数"):
            resolve_rate(1, CAP, segments, CAP, months=360)

    def test_rc_exceeds_cap_raises(self):
        segments = ((13, 24, Decimal("4.0")),)
        with pytest.raises(ValueError, match="封顶"):
            resolve_rate(1, CAP, segments, CAP, months=360)

    def test_rc_equals_cap_valid(self):
        segments = ((13, 24, CAP),)
        resolve_rate(1, CAP, segments, CAP, months=360)  # 不应抛出


# ---------------------------------------------------------------------------
# resolve_rate —— 查询利率
# ---------------------------------------------------------------------------


class TestResolveRate:
    def _segments(self):
        return (
            (13, 24, Decimal("2.1")),
            (25, 36, Decimal("2.5")),
        )

    def test_period_before_first_segment_uses_cap(self):
        rate = resolve_rate(1, CAP, self._segments(), CAP, months=360)
        assert rate == CAP

    def test_period_at_segment_start(self):
        rate = resolve_rate(13, CAP, self._segments(), CAP, months=360)
        assert rate == Decimal("2.1")

    def test_period_inside_segment(self):
        rate = resolve_rate(20, CAP, self._segments(), CAP, months=360)
        assert rate == Decimal("2.1")

    def test_period_at_segment_end(self):
        rate = resolve_rate(24, CAP, self._segments(), CAP, months=360)
        assert rate == Decimal("2.1")

    def test_period_at_second_segment(self):
        rate = resolve_rate(25, CAP, self._segments(), CAP, months=360)
        assert rate == Decimal("2.5")

    def test_period_after_all_segments_uses_cap(self):
        rate = resolve_rate(37, CAP, self._segments(), CAP, months=360)
        assert rate == CAP

    def test_period_at_last_month(self):
        rate = resolve_rate(360, CAP, self._segments(), CAP, months=360)
        assert rate == CAP

    def test_empty_segments_always_returns_cap(self):
        rate = resolve_rate(1, CAP, (), CAP, months=360)
        assert rate == CAP

    def test_full_coverage_segment(self):
        segments = ((1, 360, Decimal("2.0")),)
        for period in (1, 180, 360):
            assert resolve_rate(period, CAP, segments, CAP, months=360) == Decimal("2.0")
