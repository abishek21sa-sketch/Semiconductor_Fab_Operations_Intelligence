from fabops import __version__

import asyncio, httpx
from fabops.api.app import app

async def get(path):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as c:
        return await c.get(path)

def test_v7_platform():
    r=asyncio.run(get("/v7/platform"))
    assert r.status_code==200
    j=r.json()
    assert j["version"]==__version__
    assert j["data_fabric"]["events"]>100

def test_v7_replay_and_genealogy():
    for path in ["/v7/state-replay?lots=8","/v7/wafer-genealogy?lots=8","/v7/equipment-thread?lots=8"]:
        assert asyncio.run(get(path)).status_code==200

def test_v7_process_health():
    r=asyncio.run(get("/v7/process-health?lots=20"))
    assert r.status_code==200
    assert r.json()["analysis"]["overall_state"] in {"STABLE","ALARM"}
