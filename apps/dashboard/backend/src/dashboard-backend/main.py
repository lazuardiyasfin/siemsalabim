import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated
from pathlib import Path

import jwt
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from .config import DashboardConfig
from .engine_client import EngineClient
from .security import ALGORITHM, create_access_token, verify_password
from .state import DashboardState
from .workers import (
    broadcast_to_frontends,
    eps_broadcast_worker,
    exporter_monitor_worker,
)
from .enrich import enrich_geoip, close_geoip_reader

config = DashboardConfig()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger(__name__)

engine_client: EngineClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine_client
    logger.info("Starting dashboard backend...")

    if not config.password_hash or not config.jwt_secret_key:
        raise ValueError(
            "Missing DASHBOARD_PASSWORD_HASH and DASHBOARD_JWT_SECRET_KEY."
        )

    app.state.config = config
    app.state.live_state = DashboardState()

    async def on_engine_event(event: dict) -> None:
        app.state.live_state.event_counter += 1

        exporter_id = event.get("exporter_id") or "unknown_exporter"
        app.state.live_state.exporter_registry[exporter_id] = time.time()

        if "rule_id" in event and "type" not in event:
            event["type"] = "ALERT"

        if event["type"] == "ALERT":
            event = enrich_geoip(event)

        await broadcast_to_frontends(app.state.live_state, event)

    engine_client = EngineClient(config.engine_url, on_event=on_engine_event)

    engine_task = asyncio.create_task(engine_client.reconnect(max_retries=5))
    eps_task = asyncio.create_task(eps_broadcast_worker(app.state.live_state))
    exporter_task = asyncio.create_task(exporter_monitor_worker(app.state.live_state))

    yield

    logger.info("Shutting down dashboard backend...")
    engine_task.cancel()
    eps_task.cancel()
    exporter_task.cancel()

    await asyncio.gather(engine_task, eps_task, exporter_task, return_exceptions=True)

    close_geoip_reader()
    if engine_client:
        await engine_client.disconnect()


app = FastAPI(title="siemsalabim-dashboard", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/login")
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> dict:
    """Endpoint for single admin authentication and JWT token issuance via HttpOnly cookie."""
    cfg = request.app.state.config
    if form_data.username != cfg.user or not verify_password(
        form_data.password, cfg.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        data={"sub": cfg.user}, secret_key=cfg.jwt_secret_key
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return {"message": "Login successful"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/stats")
async def stats(request: Request) -> dict:
    """Dashboard statistics."""
    state = request.app.state.live_state
    return {
        "connected_frontends": len(state.connected_frontends),
        "engine_connected": engine_client.connected if engine_client else False,
    }


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket) -> None:
    """WebSocket endpoint for frontend to receive real-time events from engine."""
    await websocket.accept()
    cfg = websocket.app.state.config
    state = websocket.app.state.live_state

    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Missing token"
        )
        return

    try:
        payload = jwt.decode(token, cfg.jwt_secret_key, algorithms=[ALGORITHM])
        if payload.get("sub") != cfg.user:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION, reason="Invalid user"
            )
            return
    except jwt.PyJWTError:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token"
        )
        return

    state.connected_frontends.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        state.connected_frontends.discard(websocket)


@app.get("/api/auth/me")
async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No token found")

    cfg = request.app.state.config
    try:
        payload = jwt.decode(token, cfg.jwt_secret_key, algorithms=[ALGORITHM])
        if payload.get("sub") != cfg.user:
            raise HTTPException(status_code=401, detail="Invalid user")
        return {"username": cfg.user}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"

if FRONTEND_DIR.exists() and FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "dashboard-backend.main:app", host=config.host, port=config.port, reload=True
    )
