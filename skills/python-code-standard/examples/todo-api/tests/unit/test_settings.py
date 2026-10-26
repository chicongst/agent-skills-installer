import pytest
from pydantic import SecretStr, ValidationError

from tests.conftest import AUDIENCE, ISSUER, SigningKey
from todo_api.settings import AuthSettings, MemoryStorage, PostgresStorage, Settings


@pytest.fixture
def auth(signing_key: SigningKey) -> AuthSettings:
    return AuthSettings(issuer=ISSUER, audience=AUDIENCE, public_key_file=signing_key.public_file)


def test_missing_storage_and_auth_stop_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("TODO_STORAGE__DRIVER", "TODO_AUTH__ISSUER"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValidationError) as error:
        Settings()

    assert {"storage", "auth"} <= {str(item["loc"][0]) for item in error.value.errors()}


def test_postgres_driver_requires_a_database_url() -> None:
    with pytest.raises(ValidationError, match="database_url"):
        PostgresStorage.model_validate({"driver": "postgres"})


def test_production_refuses_in_memory_storage(auth: AuthSettings) -> None:
    with pytest.raises(ValidationError, match="memory is not allowed"):
        Settings(storage=MemoryStorage(driver="memory"), auth=auth)


def test_production_refuses_open_docs(auth: AuthSettings) -> None:
    storage = PostgresStorage(driver="postgres", database_url=SecretStr("postgresql+asyncpg://u:p@db/todo"))

    with pytest.raises(ValidationError, match="DOCS_ENABLED"):
        Settings(storage=storage, auth=auth, docs_enabled=True)


@pytest.mark.parametrize("algorithms", [["HS256"], ["none"], []])
def test_auth_accepts_only_asymmetric_algorithms(auth: AuthSettings, algorithms: list[str]) -> None:
    with pytest.raises(ValidationError):
        AuthSettings.model_validate({**auth.model_dump(), "algorithms": algorithms})


@pytest.mark.parametrize(
    "key_source",
    [
        {},
        {"jwks_url": "https://issuer.test/jwks", "public_key_file": "PLACEHOLDER"},
        {"public_key_file": "/missing.pem"},
    ],
)
def test_auth_needs_exactly_one_existing_key_source(signing_key: SigningKey, key_source: dict[str, str]) -> None:
    source = {name: signing_key.public_file if value == "PLACEHOLDER" else value for name, value in key_source.items()}

    with pytest.raises(ValidationError):
        AuthSettings.model_validate({"issuer": ISSUER, "audience": AUDIENCE, **source})


def test_settings_load_from_environment_only(monkeypatch: pytest.MonkeyPatch, signing_key: SigningKey) -> None:
    monkeypatch.setenv("TODO_ENVIRONMENT", "development")
    monkeypatch.setenv("TODO_STORAGE__DRIVER", "memory")
    monkeypatch.setenv("TODO_AUTH__ISSUER", ISSUER)
    monkeypatch.setenv("TODO_AUTH__AUDIENCE", AUDIENCE)
    monkeypatch.setenv("TODO_AUTH__PUBLIC_KEY_FILE", str(signing_key.public_file))

    settings = Settings()

    assert isinstance(settings.storage, MemoryStorage)
    assert (settings.environment, settings.auth.audience, settings.docs_enabled) == ("development", AUDIENCE, False)
