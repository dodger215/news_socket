from fastapi import WebSocket
from typing import Dict, Set, List
import json

class ConnectionManager:
    def __init__(self):
        # channel_name -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].remove(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]

    async def broadcast(self, channel: str, message: dict):
        if channel in self.active_connections:
            # Create a copy of the set to avoid issues if a connection is removed during iteration
            for connection in list(self.active_connections[channel]):
                try:
                    await connection.send_json(message)
                except Exception:
                    self.active_connections[channel].remove(connection)
    
    async def send_status(self, websocket: WebSocket, status: str, message: str = None):
        """Send a status event to a specific WebSocket connection."""
        from datetime import datetime
        from models import StatusEvent
        
        event = StatusEvent(
            status=status,
            message=message,
            timestamp=datetime.utcnow().isoformat()
        )
        try:
            await websocket.send_json({"type": "status", "data": event.model_dump()})
        except Exception as e:
            print(f"Error sending status: {e}")

manager = ConnectionManager()
