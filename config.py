"""Read connection settings from one server-side file or Cloud secrets."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    api_base_url: str
    api_key: str
    school_access_code: str
    database_path: Path


def load_settings() -> Settings:
    """No credential cache: edits are picked up on the next full app rerun."""
    local = ROOT / '.streamlit' / 'secrets.toml'
    values = tomllib.loads(local.read_text(encoding='utf-8')) if local.exists() else {}
    try:
        values.update(dict(st.secrets))
    except (FileNotFoundError, StreamlitSecretNotFoundError):
        pass
    def setting(name: str) -> str:
        return str(os.environ.get(name, values.get(name, ''))).strip()
    database = setting('STUDENT360_DATABASE_PATH')
    return Settings(
        api_base_url=setting('DIFY_API_BASE_URL'),
        api_key=setting('DIFY_API_KEY'),
        school_access_code=setting('SCHOOL_ACCESS_CODE'),
        database_path=Path(database).expanduser() if database else ROOT / 'data' / 'requests.sqlite3',
    )
