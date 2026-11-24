import time
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.errors import RateLimitedError

DHAKA_TZ = ZoneInfo("Asia/Dhaka")
USER_DAILY_CHAT_LIMIT = 50
IP_HOURLY_CHAT_LIMIT = 100


def current_dhaka_date(now: datetime | None = None) -> str:
    """Return calendar date YYYY-MM-DD in Asia/Dhaka time (UTC+6) per D26."""
    ref = now.astimezone(DHAKA_TZ) if now is not None else datetime.now(DHAKA_TZ)
    return ref.strftime("%Y-%m-%d")


@dataclass
class RateLimitStatus:
    limit: int
    remaining: int
    reset_epoch: int
    is_ai_resting: bool = False


class RateLimiter:
    """In-memory rate limiter for per-user daily (50/day Dhaka time), per-IP hourly (100/hr),
    and global daily AI circuit breaker ('AI rest mode') per D15 and D26.
    """

    def __init__(
        self,
        user_daily_limit: int = USER_DAILY_CHAT_LIMIT,
        ip_hourly_limit: int = IP_HOURLY_CHAT_LIMIT,
        global_daily_ai_limit: int | None = None,
    ) -> None:
        self.user_daily_limit = user_daily_limit
        self.ip_hourly_limit = ip_hourly_limit
        self.global_daily_ai_limit = (
            global_daily_ai_limit
            if global_daily_ai_limit is not None
            else get_settings().DAILY_AI_LIMIT
        )
        self._user_counts: dict[str, int] = {}
        self._ip_counts: dict[str, tuple[int, float]] = {}
        self._global_ai_counts: dict[str, int] = {}

    def check_and_increment_user_or_ip(
        self,
        uid: str | None = None,
        client_ip: str = "127.0.0.1",
        now: datetime | None = None,
    ) -> RateLimitStatus:
        date_str = current_dhaka_date(now)

        # 1. Per-IP hourly check
        now_mono = time.monotonic()
        ip_count, window_end = self._ip_counts.get(client_ip, (0, now_mono + 3600.0))
        if now_mono >= window_end:
            ip_count = 0
            window_end = now_mono + 3600.0

        if ip_count >= self.ip_hourly_limit:
            raise RateLimitedError(
                message_bn="এই আইপি থেকে প্রতি ঘণ্টার সীমা (১০০) অতিক্রম করেছে। কিছুক্ষণ পর চেষ্টা করুন।",
                message_en="Hourly request limit (100/hr) exceeded for this IP. Try again soon.",
            )
        self._ip_counts[client_ip] = (ip_count + 1, window_end)

        # 2. Per-user daily check (50/day in Asia/Dhaka time)
        if uid:
            user_key = f"{uid}_{date_str}"
            current_count = self._user_counts.get(user_key, 0)
            if current_count >= self.user_daily_limit:
                raise RateLimitedError()
            next_count = current_count + 1
            self._user_counts[user_key] = next_count
            remaining = max(0, self.user_daily_limit - next_count)
            limit_val = self.user_daily_limit
        else:
            remaining = max(0, self.ip_hourly_limit - (ip_count + 1))
            limit_val = self.ip_hourly_limit

        ai_used = self._global_ai_counts.get(date_str, 0)
        is_resting = ai_used >= self.global_daily_ai_limit

        return RateLimitStatus(
            limit=limit_val,
            remaining=remaining,
            reset_epoch=int(time.time()) + 3600,
            is_ai_resting=is_resting,
        )

    def try_consume_global_ai_quota(self, now: datetime | None = None) -> bool:
        """Attempt to consume 1 unit of global daily AI quota. Returns False if in AI rest mode."""
        date_str = current_dhaka_date(now)
        used = self._global_ai_counts.get(date_str, 0)
        if used >= self.global_daily_ai_limit:
            return False
        self._global_ai_counts[date_str] = used + 1
        return True

    def get_user_remaining(self, uid: str, now: datetime | None = None) -> int:
        date_str = current_dhaka_date(now)
        used = self._user_counts.get(f"{uid}_{date_str}", 0)
        return max(0, self.user_daily_limit - used)

    def reset(self) -> None:
        self._user_counts.clear()
        self._ip_counts.clear()
        self._global_ai_counts.clear()


global_rate_limiter = RateLimiter()
