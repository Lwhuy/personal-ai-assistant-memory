"""A thin local chat/memory client; all durable state belongs to the backend."""

import re

import httpx
import streamlit as st

from personal_assistant.config import Settings

st.set_page_config(page_title="Memory Lab", page_icon="🧠", layout="wide")
settings = Settings()


def api(method, path, **kwargs):
    try:
        response = httpx.request(
            method,
            settings.backend_url.rstrip("/") + path,
            timeout=settings.request_timeout_seconds + 30,
            **kwargs,
        )
        if response.is_error:
            try:
                detail = response.json().get("detail", "Request failed")
            except ValueError:
                detail = "Backend returned an invalid response."
            st.error(str(detail))
            st.stop()
        return response.json() if response.status_code != 204 else None
    except httpx.HTTPError:
        st.error("Backend unavailable. Start the FastAPI server and check BACKEND_URL.")
        st.stop()


st.title("Personal Assistant · Memory Lab")
st.caption("A local experiment in persistent, inspectable agent memory.")
st.sidebar.warning("Local prototype: selecting a user ID is impersonation, not authentication.")
user_id = st.sidebar.text_input("User ID", "local-user", max_chars=80)
if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", user_id):
    st.error("Use 1–80 letters, digits, underscores, or hyphens for the user ID.")
    st.stop()
if st.session_state.get("active_user") != user_id:
    for draft_key in ("new_memory_key", "new_memory_content"):
        st.session_state.pop(draft_key, None)
    st.session_state["active_user"] = user_id
base = f"/users/{user_id}"
remember = st.sidebar.checkbox(
    "Allow automatic memory saving", value=False, key=f"consent_{user_id}"
)
st.sidebar.caption(
    "Opt-in saves selected facts, preferences, and goals. Chat history is stored separately. "
    "Turning this off stops new automatic writes; existing memories remain available."
)
if st.sidebar.button("New conversation", key="new_session"):
    created_session = api("POST", base + "/sessions")
    st.session_state[f"session_{user_id}"] = created_session["session_id"]
    st.rerun()
sessions = api("GET", base + "/sessions")
if not sessions:
    sessions = [api("POST", base + "/sessions")]
session_id = st.sidebar.selectbox(
    "Conversation", [session["session_id"] for session in sessions], key=f"session_{user_id}"
)
if st.sidebar.button("Delete this conversation", key="delete_session"):
    api("DELETE", base + f"/sessions/{session_id}")
    st.rerun()
with st.sidebar.expander("Delete all my data"):
    confirmed = st.checkbox("Delete my memories and all conversations", key=f"erase_{user_id}")
    if st.button("Delete all data", disabled=not confirmed, key="erase_data"):
        api("DELETE", base + "/data")
        st.rerun()

chat_tab, memory_tab = st.tabs(["Chat", "Memory manager"])
with chat_tab:
    st.info(
        "Messages are sent to the configured Ollama server. Recent history is saved locally. "
        "Recognized sensitive inputs are excluded from storage; avoid sharing secrets."
    )
    messages = api("GET", base + f"/sessions/{session_id}/messages")
    for message in messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    prompt = st.chat_input("Message your assistant", max_chars=4000)
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)
        with st.spinner("Thinking and checking memory…"):
            result = api(
                "POST",
                "/chat",
                json={
                    "user_id": user_id,
                    "session_id": session_id,
                    "message": prompt,
                    "remember": remember,
                },
            )
        with st.chat_message("assistant"):
            st.write(result["answer"])
        for warning in result["warnings"]:
            st.warning(warning)
        with st.expander("Inspect this turn's retrieved memories and lifecycle", expanded=True):
            st.caption(
                "These records were supplied to the model; use does not prove causal reliance."
            )
            st.json(
                {
                    "profile_memories": result["profile_memories"],
                    "retrieved_memories": result["retrieved_memories"],
                    "memory_events": result["memory_events"],
                }
            )

with memory_tab:
    st.caption(
        "Adding or editing here explicitly saves a memory. Reuse a key to replace a current fact. "
        "Updating or deleting a memory clears your chat histories to remove stale context."
    )
    with st.form("new_memory", clear_on_submit=True):
        key = st.text_input("Fact key (lowercase snake_case)", key="new_memory_key", max_chars=64)
        content = st.text_area("Memory content", key="new_memory_content", max_chars=500)
        memory_type = st.selectbox("Memory type", ["semantic", "episodic", "procedural"])
        if st.form_submit_button("Save memory", key="add_memory"):
            api(
                "POST",
                base + "/memories",
                json={"key": key, "content": content, "memory_type": memory_type},
            )
            st.rerun()
    query = st.text_input(
        "Inspect keyword/vector retrieval", key=f"search_{user_id}", max_chars=4000
    )
    if query.strip():
        st.json(api("GET", base + "/memories/search", params={"query": query}))
    memories = api("GET", base + "/memories")
    st.write(f"{len(memories)} saved memories")
    for memory in memories:
        with st.expander(memory["key"]):
            st.caption(f"ID: {memory['id']} · Updated: {memory['updated_at']}")
            st.caption(
                f"Source conversation: {memory['source_session_id'] or 'explicit memory manager'}"
            )
            if memory.get("source_quote"):
                st.caption("Supporting user quote")
                st.text(memory["source_quote"])
            with st.form("edit_" + memory["id"]):
                new_key = st.text_input("Key", memory["key"], max_chars=64)
                new_content = st.text_area("Content", memory["content"], max_chars=500)
                types = ["semantic", "episodic", "procedural"]
                new_type = st.selectbox("Type", types, index=types.index(memory["memory_type"]))
                if st.form_submit_button("Update"):
                    api(
                        "PUT",
                        base + "/memories/" + memory["id"],
                        json={
                            "key": new_key,
                            "content": new_content,
                            "memory_type": new_type,
                        },
                    )
                    st.rerun()
            if st.button("Delete memory", key="delete_" + memory["id"]):
                api("DELETE", base + "/memories/" + memory["id"])
                st.rerun()
