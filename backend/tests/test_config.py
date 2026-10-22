from app.core.config import Settings


def test_cors_environment_supports_documented_formats(monkeypatch):
    for value in ['http://localhost:3000,https://support.example', '["http://localhost:3000", "https://support.example"]']:
        monkeypatch.setenv("CORS_ORIGINS", value)
        assert Settings(_env_file=None).cors_origins == ["http://localhost:3000", "https://support.example"]
