from fabops import __version__
import asyncio, httpx
from fabops.api.app import app

async def get(path):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as c:
        return await c.get(path)

def test_v6_platform():
    r=asyncio.run(get("/v6/platform")); assert r.status_code==200
    j=r.json(); assert j["version"]==__version__
    assert j["integration"]["multi_operation_schedule"] is True

def test_v6_coupled_demo():
    r=asyncio.run(get("/v6/coupled-twin/demo?lots=24")); assert r.status_code==200
    assert r.json()["event_count"]>0

def test_v6_schedule_demo():
    r=asyncio.run(get("/v6/multi-operation-schedule/demo?lots=2")); assert r.status_code==200
    j=r.json(); assert j["success"] is True and j["precedence_violations"]==0
