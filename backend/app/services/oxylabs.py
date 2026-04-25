import httpx
import base64
from app.core.config import settings

BASE_URL = "https://residential-api.oxylabs.io/v2"


class OxylabsService:
    def __init__(self):
        self.token: str | None = None
        self.user_id: str | None = None

    async def login(self) -> bool:
        credentials = base64.b64encode(
            f"{settings.OXYLABS_USERNAME}:{settings.OXYLABS_PASSWORD}".encode()
        ).decode()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}/login",
                headers={"Authorization": f"Basic {credentials}", "accept": "application/json"},
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data["token"]
                self.user_id = data["user_id"]
                return True
            return False

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "accept": "application/json"}

    async def create_sub_user(self, username: str, password: str, traffic_limit_gb: float = 1.0) -> dict | None:
        if not self.token:
            await self.login()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}/users/{self.user_id}/sub-users",
                headers=self._headers(),
                json={
                    "username": username,
                    "password": password,
                    "trafficLimit": int(traffic_limit_gb * 1024 * 1024 * 1024),
                },
            )
            if resp.status_code in (200, 201):
                return resp.json()
            return None

    async def delete_sub_user(self, sub_user_id: str) -> bool:
        if not self.token:
            await self.login()
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BASE_URL}/users/{self.user_id}/sub-users/{sub_user_id}",
                headers=self._headers(),
            )
            return resp.status_code == 200

    async def get_usage(self) -> dict | None:
        if not self.token:
            await self.login()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/users/{self.user_id}/client-stats",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return resp.json()
            return None

    def get_proxy_config(self, sub_username: str, sub_password: str) -> dict:
        return {
            "server": "pr.oxylabs.io",
            "port": 7777,
            "username": sub_username,
            "password": sub_password,
        }


oxylabs_service = OxylabsService()
