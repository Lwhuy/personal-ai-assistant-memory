from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from personal_assistant.api import create_app
from personal_assistant.config import Settings
from tests.fakes import FakeProvider


def test_streamlit_chat_and_explicit_memory(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, database_path=tmp_path / "ui.db")
    with TestClient(create_app(settings, FakeProvider())) as client:

        def local_request(method, url, **kwargs):
            kwargs.pop("timeout", None)
            path = httpx.URL(url).raw_path.decode()
            return client.request(method, path, **kwargs)

        monkeypatch.setattr(httpx, "request", local_request)
        app = AppTest.from_file(
            Path(__file__).resolve().parents[1] / "streamlit_app.py", default_timeout=15
        ).run()
        assert not app.exception
        assert app.title[0].value == "Personal Assistant · Memory Lab"
        app.chat_input[0].set_value("Hello").run()
        assert not app.exception
        assert any(message.value == "A test answer." for message in app.markdown)
        previous_session = app.sidebar.selectbox[0].value
        app.button(key="new_session").click().run()
        new_session = app.sidebar.selectbox[0].value
        assert new_session != previous_session
        app.chat_input[0].set_value("A new conversation").run()
        messages = client.get(f"/users/local-user/sessions/{new_session}/messages").json()
        assert messages[0]["content"] == "A new conversation"
        app.text_input(key="new_memory_key").set_value("editor_preference")
        app.text_area(key="new_memory_content").set_value("Favorite editor is VS Code")
        app.button(key="add_memory").click().run()
        assert not app.exception
        assert (
            client.get("/users/local-user/memories").json()[0]["content"]
            == "Favorite editor is VS Code"
        )
        app.text_area(key="new_memory_content").set_value("Alice private draft").run()
        app.sidebar.text_input[0].set_value("bob").run()
        assert not app.exception
        assert app.text_area(key="new_memory_content").value == ""
        assert not any("VS Code" in element.value for element in app.markdown)
