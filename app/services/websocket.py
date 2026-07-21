from typing import List, Dict, Any
from fastapi import WebSocket
from app.core.logging import logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)
        logger.info("WebSocket connected", user_id=user_id, active_count=len(self.active_connections))

    def disconnect(self, websocket: WebSocket, user_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        logger.info("WebSocket disconnected", user_id=user_id, active_count=len(self.active_connections))

    async def send_personal_message(self, message: Dict[str, Any], user_id: str):
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                await connection.send_json(message)

    async def broadcast(self, event: str, data: Dict[str, Any]):
        payload = {"event": event, "data": data}
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception as e:
                logger.error("Failed to send WS message", error=str(e))


ws_manager = ConnectionManager()
