import pytest
from pydantic import ValidationError

from taskboard.main import create_app
from taskboard.settings import AuthSettings, MemoryStorage, Settings
from tests.conftest import AUDIENCE, ISSUER, SigningKey


@pytest.fixture
def auth(signing_key: SigningKey) -> AuthSettings:
    return AuthSettings(issuer=ISSUER, audience=AUDIENCE, public_key_file=signing_key.public_file)


def test_create_app_without_storage_and_auth_fails_at_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("TASKBOARD_STORAGE__DRIVER", "TASKBOARD_AUTH__ISSUER", "TASKBOARD_ENVIRONMENT"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValidationError) as error:
        create_app()

    assert {"storage", "auth"} <= {str(item["loc"][0]) for item in error.value.errors()}


def test_production_refuses_in_memory_storage(auth: AuthSettings) -> None:
    with pytest.raises(ValidationError, match="No durable storage backend"):
        Settings(storage=MemoryStorage(driver="memory"), auth=auth)


def test_development_with_open_docs_is_allowed(auth: AuthSettings) -> None:
    settings = Settings(environment="development", storage=MemoryStorage(driver="memory"), auth=auth, docs_enabled=True)

    assert settings.docs_enabled


@pytest.mark.parametrize("algorithms", [["HS256"], ["none"], []])
def test_auth_with_symmetric_or_no_algorithm_is_rejected(auth: AuthSettings, algorithms: list[str]) -> None:
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
def test_auth_without_exactly_one_existing_key_source_is_rejected(
    signing_key: SigningKey, key_source: dict[str, str]
) -> None:
    source = {name: signing_key.public_file if value == "PLACEHOLDER" else value for name, value in key_source.items()}

    with pytest.raises(ValidationError):
        AuthSettings.model_validate({"issuer": ISSUER, "audience": AUDIENCE, **source})


def test_settings_load_from_environment_only(monkeypatch: pytest.MonkeyPatch, signing_key: SigningKey) -> None:
    monkeypatch.setenv("TASKBOARD_ENVIRONMENT", "development")
    monkeypatch.setenv("TASKBOARD_STORAGE__DRIVER", "memory")
    monkeypatch.setenv("TASKBOARD_AUTH__ISSUER", ISSUER)
    monkeypatch.setenv("TASKBOARD_AUTH__AUDIENCE", AUDIENCE)
    monkeypatch.setenv("TASKBOARD_AUTH__PUBLIC_KEY_FILE", str(signing_key.public_file))

    settings = Settings()

    assert isinstance(settings.storage, MemoryStorage)
    assert (settings.environment, settings.auth.audience, settings.docs_enabled) == ("development", AUDIENCE, False)
