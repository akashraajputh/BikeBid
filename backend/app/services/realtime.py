from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


class AuctionConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[int, list[WebSocket]] = {}

    async def connect(self, auction_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.setdefault(auction_id, []).append(websocket)

    def disconnect(self, auction_id: int, websocket: WebSocket) -> None:
        connections = self.connections.get(auction_id, [])
        self.connections[auction_id] = [connection for connection in connections if connection != websocket]

    async def broadcast(self, auction_id: int, payload: dict[str, Any]) -> None:
        stale_connections = []
        for connection in list(self.connections.get(auction_id, [])):
            try:
                await connection.send_json(payload)
            except (RuntimeError, WebSocketDisconnect):
                stale_connections.append(connection)
        for connection in stale_connections:
            self.disconnect(auction_id, connection)
auction_connections = AuctionConnectionManager()
