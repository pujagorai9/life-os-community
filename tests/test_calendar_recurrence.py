"""Calendar recurrence must clamp individual months without changing the anchor."""
from datetime import datetime, timezone

import pytest

from life_os.lifecycle import generate_tracking_protocol, schedule_protocol
from life_os.models import GoalContractCreate
from life_os.store import LifeOSStore
from test_goal_cycles import goal_payload


def scheduled_dates(tmp_path, start, cadence, end, *, finite=False, window_start=None, zone='UTC'):
    store = LifeOSStore(tmp_path / 'recurrence.db')
    payload = goal_payload()
    payload.update(
        start_at=start, review_at=end if finite else None, timezone=zone,
        milestones=[], routines=[{
            'title': 'Recurring calendar check-in', 'cadence': cadence,
            'target_count': 1, 'unit': 'check-in',
            'minimum_success': 'Review the current period', 'preferred_time': '18:00',
        }],
    )
    goal = store.create_goal(GoalContractCreate.model_validate(payload))
    protocol = generate_tracking_protocol(goal)
    dates = schedule_protocol(
        goal, protocol,
        datetime.fromisoformat(window_start or start), datetime.fromisoformat(end),
    )
    recurring_id = next(prompt.id for prompt in protocol.prompts if prompt.cadence == cadence)
    return [item.due_at for item in dates if item.prompt_id == recurring_id]


@pytest.mark.parametrize('finite', [False, True])
def test_monthly_anchor_returns_to_31_after_short_months(tmp_path, finite):
    # Existing first-due rule: Jan 1 + one month - one day = Jan 31.
    dates = scheduled_dates(tmp_path, '2030-01-01T08:00:00+00:00', 'monthly', '2030-12-31T23:59:59+00:00', finite=finite)
    assert [date.day for date in dates] == [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    assert [date.month for date in dates] == list(range(1, 13))


def test_december_31_goal_keeps_january_30_anchor(tmp_path):
    dates = scheduled_dates(tmp_path, '2029-12-31T08:00:00+00:00', 'monthly', '2030-05-31T23:59:59+00:00')
    assert [(date.month, date.day) for date in dates] == [(1, 30), (2, 28), (3, 30), (4, 30), (5, 30)]


def test_january_31_goal_preserves_existing_first_due_rule(tmp_path):
    dates = scheduled_dates(tmp_path, '2030-01-31T08:00:00+00:00', 'monthly', '2030-05-31T23:59:59+00:00')
    assert [(date.month, date.day) for date in dates] == [(2, 27), (3, 27), (4, 27), (5, 27)]


def test_monthly_anchor_handles_leap_february(tmp_path):
    dates = scheduled_dates(tmp_path, '2032-01-01T08:00:00+00:00', 'monthly', '2032-04-30T23:59:59+00:00')
    assert [(date.month, date.day) for date in dates] == [(1, 31), (2, 29), (3, 31), (4, 30)]


def test_quarterly_anchor_survives_two_clamped_months(tmp_path):
    dates = scheduled_dates(tmp_path, '2030-03-01T08:00:00+00:00', 'quarterly', '2031-08-31T23:59:59+00:00')
    assert [(date.year, date.month, date.day) for date in dates] == [
        (2030, 5, 31), (2030, 8, 31), (2030, 11, 30),
        (2031, 2, 28), (2031, 5, 31), (2031, 8, 31),
    ]


def test_yearly_february_29_returns_in_next_leap_year(tmp_path):
    dates = scheduled_dates(tmp_path, '2023-03-01T08:00:00+00:00', 'yearly', '2028-03-01T00:00:00+00:00')
    assert [(date.year, date.month, date.day) for date in dates] == [
        (2024, 2, 29), (2025, 2, 28), (2026, 2, 28), (2027, 2, 28), (2028, 2, 29),
    ]


def test_rolling_window_does_not_use_window_end_as_calendar_anchor(tmp_path):
    dates = scheduled_dates(tmp_path, '2030-01-01T08:00:00+00:00', 'yearly', '2031-01-15T23:59:59+00:00', window_start='2031-01-01T00:00:00+00:00')
    assert dates == []  # Jan 31 is not due yet; the window must not invent Jan 15.


def test_later_window_skips_clamped_month_without_losing_anchor(tmp_path):
    dates = scheduled_dates(tmp_path, '2030-01-01T08:00:00+00:00', 'monthly', '2030-05-31T23:59:59+00:00', window_start='2030-03-01T00:00:00+00:00')
    assert [(date.month, date.day) for date in dates] == [(3, 31), (4, 30), (5, 31)]


def test_monthly_wall_clock_and_anchor_survive_dst(tmp_path):
    dates = scheduled_dates(tmp_path, '2030-01-01T08:00:00-08:00', 'monthly', '2030-04-30T23:59:59-07:00', zone='America/Los_Angeles')
    assert [date.day for date in dates] == [31, 28, 31, 30]
    assert [date.hour for date in dates] == [18, 18, 18, 18]
    assert [date.utcoffset().total_seconds() / 3600 for date in dates] == [-8, -8, -7, -7]


def test_calendar_first_due_remains_at_finite_cycle_end(tmp_path):
    dates = scheduled_dates(tmp_path, '2030-01-01T08:00:00+00:00', 'monthly', '2030-01-15T12:00:00+00:00', finite=True)
    assert dates == [datetime(2030, 1, 15, 12, tzinfo=timezone.utc)]


def test_query_before_future_goal_start_does_not_create_occurrences(tmp_path):
    dates = scheduled_dates(tmp_path, '2035-01-01T08:00:00+00:00', 'yearly', '2030-01-15T23:59:59+00:00', window_start='2030-01-01T00:00:00+00:00')
    assert dates == []
