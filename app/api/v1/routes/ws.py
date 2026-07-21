from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_token
from app.services.websocket import ws_manager
from app.core.logging import logger

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    user_id = "anonymous"
    try:
        payload = decode_token(token)
        user_id = payload.get("sub", "anonymous")
    except Exception as e:
        logger.warning("WebSocket token decoding failed", error=str(e))

    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back ping or message
            await websocket.send_json({"event": "pong", "data": {"received": data}})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
