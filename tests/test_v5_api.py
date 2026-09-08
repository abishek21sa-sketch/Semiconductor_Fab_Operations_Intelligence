from fabops import __version__
import asyncio, httpx
from fabops.api.app import app

async def get(path):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as c:
        return await c.get(path)

def test_v5_platform():
    r=asyncio.run(get("/v5/platform")); assert r.status_code==200
    j=r.json(); assert j["version"]==__version__
    assert j["engine"]["integrated_schedule_success"] is True

def test_v5_chambers_api():
    r=asyncio.run(get("/v5/chambers")); assert r.status_code==200
    assert r.json()["count"]>=19

def test_v5_integrated_schedule_api():
    r=asyncio.run(get("/v5/demo-integrated-schedule")); assert r.status_code==200
    assert r.json()["queue_breaches"]==0 and r.json()["reticle_conflicts"]==0
