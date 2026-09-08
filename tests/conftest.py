import asyncio
import httpx
import pytest
from fabops.api.app import app


class InProcessASGIClient:
    """Thread-free synchronous facade over HTTPX ASGITransport.

    Starlette/FastAPI TestClient uses an AnyIO blocking portal and a helper thread.
    On the Microsoft Store CPython 3.13 runtime this project observed native access
    violations while that portal was being joined.  Driving ASGI directly keeps
    API tests in one event loop and exercises the same application routes without
    the fragile cross-thread bridge.
    """

    def request(self, method: str, path: str, **kwargs):
        async def _request():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(_request())

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)


@pytest.fixture
def client():
    return InProcessASGIClient()
