from datetime import datetime, timezone,timedelta

# 获取当前日期时间
def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# 获取当前日期时间加上指定的时间增量
def utc_now_plus(*, days: int = 0, hours: int = 0, minutes: int = 0) -> datetime:
    return utc_now() + timedelta(days=days, hours=hours, minutes=minutes)

# 获取指定日期时间的 UTC 时间戳（秒级）
def utc_timestamp(dt: datetime | None = None) -> int:
    # JWT 的 exp 常用 int 秒级时间戳
    dt = dt or utc_now()
    return int(dt.timestamp())


# 格式化日期时间为字符串
def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return dt.strftime(fmt)

# 解析字符串为日期时间
def parse_datetime(date_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    return datetime.strptime(date_str, fmt)

