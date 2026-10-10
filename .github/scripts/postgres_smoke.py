"""CI only: exercise the full API against migrated disposable PostgreSQL/Redis."""
import asyncio
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.main import app


async def main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        readiness = await client.get("/health/ready")
        assert readiness.status_code == 200, readiness.text
        password = "CI-only passphrase 419!"
        accounts = []
        for _ in range(2):
            result = await client.post("/auth/register", json={
                "email": f"ci-{uuid4()}@example.com", "password": password,
            })
            assert result.status_code == 201, result.text
            accounts.append({"Authorization": f"Bearer {result.json()['access_token']}"})
        owner, stranger = accounts
        result = await client.post("/support/conversations", headers=owner, json={"channel": "chat"})
        assert result.status_code == 201, result.text
        conversation = result.json()["id"]
        url = f"/support/conversations/{conversation}"
        result = await client.post(f"{url}/messages", headers=owner,
                                   json={"content": "My UPI payment of INR 500 failed. What next?"})
        assert result.status_code == 200, result.text
        assert result.json()["queries"][0]["facts"]["verified"] is False
        stored = await client.get(url, headers=owner)
        assert stored.status_code == 200, stored.text
        assert len(stored.json()["messages"]) == 2
        assert (await client.get(url, headers=stranger)).status_code == 404
        assert (await client.get("/support/queue", headers=owner)).status_code == 403
        assert (await client.post("/support/conversations", headers=owner,
                                  json={"channel": "voice"})).status_code == 422
        assert (await client.post("/auth/logout", headers=owner)).status_code == 204
        assert (await client.get(url, headers=owner)).status_code == 401
    print("PostgreSQL API smoke passed: persisted chat, isolation, consent, logout")


asyncio.run(main())
