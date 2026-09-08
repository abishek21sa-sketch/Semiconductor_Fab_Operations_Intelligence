from fabops import __version__
import asyncio, httpx
from fabops.api.app import app

async def get(path):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as c:
        return await c.get(path)

def test_v4_platform():
    r=asyncio.run(get("/v4/platform")); assert r.status_code==200
    assert r.json()["version"]==__version__
    assert len(r.json()["workspaces"])>=13

def test_v4_genealogy_api():
    r=asyncio.run(get("/v4/lot/LOT-017/genealogy")); assert r.status_code==200
    assert r.json()["route_length"]>=14

def test_v4_operational_apis():
    for path in ["/v4/maintenance-calendar","/v4/yield-genealogy","/v4/amhs-network","/v4/queue-time-watch"]:
        assert asyncio.run(get(path)).status_code==200
