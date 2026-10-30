"""Create optional, synthetic recurring goals. Never reads cloud or private data."""
from __future__ import annotations
import os
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from life_os.lifecycle import activate_goal, schedule_protocol
from life_os.models import GoalContractCreate
from life_os.store import LifeOSStore


def seed_demo(store: LifeOSStore, tenant_id: str, zone: str) -> int:
    now = datetime.now(ZoneInfo(zone))
    start = datetime.combine(now.date() - timedelta(days=1), time.min, now.tzinfo)
    existing = {goal.title for goal in store.list_goals(tenant_id)}
    examples = [
        ('learning', 'knowledge_guru', 'Demo: keep a small learning habit', 'Read or practice for ten minutes', '20:00'),
        ('fitness', 'fitness_coach', 'Demo: make time for movement', 'Take a comfortable walk', '18:00'),
        ('operations', 'operations_manager', 'Demo: plan the next day', 'Write down one priority for tomorrow', '20:30'),
    ]
    count = 0
    for domain, agent, title, routine, preferred_time in examples:
        if title in existing:
            continue
        request = GoalContractCreate.model_validate({
            'tenant_id': tenant_id, 'domain': domain, 'owner_agent': agent,
            'title': title, 'motivation': 'Try the local app with synthetic examples.',
            'success_definition': 'Complete the routine when it is useful; adjust it during a regular review.',
            'start_at': start.isoformat(), 'review_at': None, 'timezone': zone,
            'review_cadence': 'weekly',
            'metrics': [{'key': 'routine_days', 'label': 'Completed routine days', 'unit': 'day', 'target_type': 'at_least', 'target_value': 1, 'cadence': 'weekly'}],
            'routines': [{'title': routine, 'cadence': 'daily', 'target_count': 1, 'unit': 'session', 'minimum_success': routine, 'preferred_time': preferred_time}],
        })
        goal = store.create_goal(request)
        goal, protocol = activate_goal(store, tenant_id, goal.id)
        protocol = store.set_tracking_protocol_approval(tenant_id, goal.id, True)
        store.replace_pending_check_ins(tenant_id, goal.id, schedule_protocol(goal, protocol, start, now + timedelta(days=30)))
        count += 1
    return count


def main() -> None:
    load_dotenv()
    path = Path(os.getenv('LIFE_OS_DATABASE', 'private/life_os.db'))
    path.parent.mkdir(parents=True, exist_ok=True)
    count = seed_demo(LifeOSStore(path), os.getenv('LIFE_OS_DEMO_TENANT', 'me'), os.getenv('LIFE_OS_TIMEZONE', 'UTC'))
    print(f'Added {count} synthetic demo goals. Existing goals were kept.')


if __name__ == '__main__':
    main()
