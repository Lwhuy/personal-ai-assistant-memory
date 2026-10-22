"""Loopback-only prototype API. User IDs are namespaces, not authenticated principals."""

import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from personal_assistant.agent import Assistant
from personal_assistant.config import Settings
from personal_assistant.models import ChatRequest, ChatResult, Identifier, Memory, MemoryInput
from personal_assistant.provider import OllamaProvider, Provider, ProviderError


def get_assistant(request: Request) -> Assistant:
    return request.app.state.assistant


Service = Annotated[Assistant, Depends(get_assistant)]


def create_app(settings: Settings | None = None, provider: Provider | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configuration = settings or Settings()
        runtime_provider = provider or OllamaProvider(configuration)
        try:
            app.state.assistant = Assistant(configuration, runtime_provider)
            yield
        finally:
            if provider is None:
                runtime_provider.close()

    app = FastAPI(
        title="Personal Assistant Memory Lab",
        description="Local identity selection only. This API has no authentication.",
        lifespan=lifespan,
    )

    @app.exception_handler(ProviderError)
    async def provider_error(request: Request, exc: ProviderError):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def invalid_value(request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(sqlite3.OperationalError)
    async def storage_error(request: Request, exc: sqlite3.OperationalError):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Local storage unavailable. Check database permissions and disk space."
            },
        )

    @app.get("/health")
    def health():
        return {"status": "ok", "identity": "local-prototype", "model_readiness_checked": False}

    @app.post("/chat", response_model=ChatResult)
    def chat(body: ChatRequest, service: Service):
        return service.chat(**body.model_dump())

    @app.post("/users/{user_id}/sessions", status_code=201)
    def create_session(user_id: Identifier, service: Service):
        with service.lock:
            return service.store.create_session(user_id)

    @app.get("/users/{user_id}/sessions")
    def sessions(user_id: Identifier, service: Service):
        with service.lock:
            return service.store.list_sessions(user_id)

    @app.get("/users/{user_id}/sessions/{session_id}/messages")
    def messages(user_id: Identifier, session_id: Identifier, service: Service):
        with service.lock:
            return service.store.history(user_id, session_id)

    @app.delete("/users/{user_id}/sessions/{session_id}", status_code=204)
    def delete_session(user_id: Identifier, session_id: Identifier, service: Service):
        with service.lock:
            if not service.store.delete_session(user_id, session_id):
                raise HTTPException(404, "Session not found")
        return Response(status_code=204)

    @app.get("/users/{user_id}/memories", response_model=list[Memory])
    def memories(user_id: Identifier, service: Service):
        with service.lock:
            return service.store.list(user_id)

    @app.get("/users/{user_id}/memories/search")
    def search(
        user_id: Identifier, service: Service, query: str = Query(min_length=1, max_length=4000)
    ):
        with service.lock:
            return service.memory.search(user_id, query)

    @app.post("/users/{user_id}/memories", response_model=Memory, status_code=201)
    def add_memory(user_id: Identifier, body: MemoryInput, service: Service):
        with service.lock:
            memory, _ = service.memory.save(user_id, body)
            return memory

    @app.get("/users/{user_id}/memories/{memory_id}", response_model=Memory)
    def memory(user_id: Identifier, memory_id: Identifier, service: Service):
        with service.lock:
            result = service.store.get(user_id, memory_id)
            if result is None:
                raise HTTPException(404, "Memory not found")
            return result

    @app.put("/users/{user_id}/memories/{memory_id}", response_model=Memory)
    def update_memory(
        user_id: Identifier, memory_id: Identifier, body: MemoryInput, service: Service
    ):
        with service.lock:
            result = service.memory.update(user_id, memory_id, body)
            if result is None:
                raise HTTPException(404, "Memory not found")
            return result

    @app.delete("/users/{user_id}/memories/{memory_id}", status_code=204)
    def delete_memory(user_id: Identifier, memory_id: Identifier, service: Service):
        with service.lock:
            if not service.store.delete(user_id, memory_id):
                raise HTTPException(404, "Memory not found")
        return Response(status_code=204)

    @app.delete("/users/{user_id}/data", status_code=204)
    def delete_user_data(user_id: Identifier, service: Service):
        with service.lock:
            service.store.delete_user_data(user_id)
        return Response(status_code=204)

    return app


app = create_app()
