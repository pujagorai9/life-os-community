from datetime import datetime, timezone
from fastapi.testclient import TestClient
from life_os.api import create_app
from life_os.store import LifeOSStore
from test_goal_cycles import goal_payload


def test_convert_and_continue_recurring_without_losing_history(tmp_path):
    db = tmp_path / 'api.db'
    client = TestClient(create_app(db))
    goal = client.post('/v1/goals', json=goal_payload()).json()
    gid = goal['id']
    client.post(f'/v1/goals/{gid}/approve?tenant_id=tenant-a')
    client.post(f'/v1/goals/{gid}/tracking-protocol/approval', json={'tenant_id':'tenant-a','approved':True})
    params = {'tenant_id':'tenant-a', 'start_at':'2030-01-01T00:00:00Z', 'end_at':'2030-01-03T23:59:59Z'}
    before = client.get('/v1/check-ins', params=params).json()
    item = before[0]
    client.patch(f"/v1/check-ins/{item['id']}", json={'tenant_id':'tenant-a','status':'responded','outcome':'done'})
    result = client.post(f'/v1/goals/{gid}/amendments', json={'tenant_id':'tenant-a','reason':'Ongoing goal','changes':{'review_at':None,'review_cadence':'weekly'}})
    assert result.status_code == 200, result.text
    assert result.json()['review_at'] is None
    protocol = client.get(f'/v1/goals/{gid}/tracking-protocol?tenant_id=tenant-a').json()
    assert protocol['approved'] and protocol['goal_version'] == 2
    after = client.get('/v1/check-ins', params=params).json()
    assert len(after) == len(before)
    assert next(x for x in after if x['id']==item['id'])['status']=='responded'
    future = {**params, 'start_at':'2032-04-01T00:00:00Z','end_at':'2032-04-08T23:59:59Z'}
    first = client.get('/v1/check-ins', params=future).json()
    assert first and all(x['goal_id']==gid for x in first)
    assert {x['id'] for x in first} == {x['id'] for x in client.get('/v1/check-ins', params=future).json()}
    assert client.get('/v1/reviews/due', params={'tenant_id':'tenant-a','as_of':'2032-04-08T23:59:59Z'}).json()==[]
    review=client.post(f'/v1/goals/{gid}/review?tenant_id=tenant-a')
    assert review.json()['goal']['status']=='active'
    assert client.get('/v1/check-ins',params={**future,'tenant_id':'tenant-b'}).json()==[]
    # Persistence survives a new store instance, without a fake expiry date.
    assert LifeOSStore(db).get_goal('tenant-a',gid).review_at is None


def test_new_ongoing_goal_and_unapproved_protocol(tmp_path):
    client=TestClient(create_app(tmp_path/'api.db'))
    payload=goal_payload(); payload.pop('review_at')
    result=client.post('/v1/goals',json=payload)
    assert result.status_code==200, result.text
    gid=result.json()['id']
    assert client.post(f'/v1/goals/{gid}/approve?tenant_id=tenant-a').status_code==200
    assert client.get('/v1/check-ins',params={'tenant_id':'tenant-a','start_at':'2030-01-01T00:00:00Z','end_at':'2030-02-01T00:00:00Z'}).json()==[]


def test_ongoing_routines_follow_wall_clock_across_dst(tmp_path):
    from life_os.lifecycle import generate_tracking_protocol, schedule_protocol
    from life_os.models import GoalContractCreate
    store=LifeOSStore(tmp_path/'dst.db')
    payload=goal_payload()
    payload.update(start_at='2026-10-30T08:00:00-07:00',review_at=None,timezone='America/Los_Angeles')
    goal=store.create_goal(GoalContractCreate.model_validate(payload))
    protocol=generate_tracking_protocol(goal)
    items=schedule_protocol(goal,protocol,datetime(2026,10,31,tzinfo=timezone.utc),datetime(2026,11,3,tzinfo=timezone.utc))
    logs=[x for x in items if 'Complete food log' in x.prompt]
    assert [x.due_at.hour for x in logs]==[20,20,20]
    assert [x.due_at.utcoffset().total_seconds()/3600 for x in logs]==[-7,-7,-8]
