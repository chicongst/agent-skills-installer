from tests.conftest import SettingsFactory, SigningKey
from tests.integration.conftest import open_api
from todo_api.main import create_app

UNREACHABLE = "postgresql+asyncpg://todo:unused@127.0.0.1:1/todo"


async def test_ready_returns_503_when_the_database_is_down_while_live_stays_200(
    make_settings: SettingsFactory, signing_key: SigningKey
) -> None:
    async for api in open_api(create_app(make_settings(database_url=UNREACHABLE)), signing_key):
        ready = await api.send("GET", "/health/ready", anonymous=True)
        live = await api.send("GET", "/health/live", anonymous=True)

        assert (ready.status_code, ready.json()["code"], ready.json()["failing"]) == (
            503,
            "SERVICE_UNAVAILABLE",
            ["database"],
        )
        assert live.status_code == 200
