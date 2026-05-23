import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Set, Annotated
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

config = DashboardConfig()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger(__name__)

engine_client: EngineClient | None = None
connected_frontends: Set[WebSocket] = set()


async def broadcast_to_frontends(event: dict) -> None:
    """Broadcast event from engine to all connected frontends."""
    disconnected = set()

    for websocket in connected_frontends:
        try:
            await websocket.send_json(event)
        except Exception as exc:
            logger.warning("Failed to send event to frontend: %s", exc)
            disconnected.add(websocket)

    for websocket in disconnected:
        connected_frontends.discard(websocket)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global engine_client

    logger.info("Starting dashboard backend...")

    if not config.password_hash or not config.jwt_secret_key:
        raise ValueError(
            "Missing DASHBOARD_PASSWORD_HASH and DASHBOARD_JWT_SECRET_KEY."
        )

    app.state.config = config

    async def on_engine_event(event: dict) -> None:
        """Handle event from engine."""
        await broadcast_to_frontends(event)

    engine_client = EngineClient(config.engine_url, on_event=on_engine_event)
    engine_task = asyncio.create_task(engine_client.reconnect(max_retries=5))

    yield

    logger.info("Shutting down dashboard backend...")
    engine_task.cancel()
    try:
        await engine_task
    except Exception:
        logger.info("Engine task cancelled successfully.")
    finally:
        if engine_client:
            await engine_client.disconnect()


app = FastAPI(
    title="siemsalabim-dashboard",
    version="0.1.0",
    lifespan=lifespan,
)

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
    config = request.app.state.config

    if form_data.username != config.user or not verify_password(
        form_data.password, config.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        data={"sub": config.user}, secret_key=config.jwt_secret_key
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
async def stats() -> dict:
    """Dashboard statistics."""
    return {
        "connected_frontends": len(connected_frontends),
        "engine_connected": engine_client.connected if engine_client else False,
    }


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket) -> None:
    """WebSocket endpoint for frontend to receive real-time events from engine."""
    await websocket.accept()
    config = websocket.app.state.config

    # Extract token automatically from HttpOnly cookies
    token = websocket.cookies.get("access_token")

    # Validate presence of the token cookie
    if not token:
        logger.warning("WebSocket connection rejected: Missing token cookie")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Missing token"
        )
        return

    # Validate JWT token signature and expiration status
    try:
        payload = jwt.decode(token, config.jwt_secret_key, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username != config.user:
            logger.warning("WebSocket connection rejected: Invalid user identification")
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION, reason="Invalid user"
            )
            return
    except jwt.PyJWTError:
        logger.warning("WebSocket connection rejected: Invalid or expired token")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token"
        )
        return

    # Connection accepted and tracked
    connected_frontends.add(websocket)
    logger.info("Frontend connected. Total frontends: %d", len(connected_frontends))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_frontends.discard(websocket)
        logger.info(
            "Frontend disconnected. Total frontends: %d", len(connected_frontends)
        )


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "dashboard-backend.main:app",
        host=config.host,
        port=config.port,
        reload=True,
    )
