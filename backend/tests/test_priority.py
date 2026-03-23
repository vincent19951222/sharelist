import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test-sharelist.db")

import pytest  # noqa: E402

from backend.main import repeat_days_to_mask, validate_reward_gp  # noqa: E402


def test_repeat_days_reject_unknown_value():
    with pytest.raises(ValueError, match="Sun/Mon/Tue/Wed/Thu/Fri/Sat"):
        repeat_days_to_mask(["Holiday"])


def test_reward_gp_accepts_upper_bound():
    assert validate_reward_gp(999) == 999


def test_reward_gp_rejects_non_numeric_value():
    with pytest.raises(ValueError, match="must be a number"):
        validate_reward_gp("abc")
