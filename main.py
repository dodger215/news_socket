from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from scraper import scrub_headlines, scrub_article_detail, scrub_live_tv, scrub_cartoons, scrub_popular
from manager import manager
import asyncio
import json
from typing import List

app = FastAPI()

CATEGORIES = ["HOME", "NEWS", "POLITICS", "ENTERTAINMENT", "SPORTS", "BUSINESS", "OPINION", "VIDEOS", "ELECTIONS"]

async def background_scrubber():
    """Periodically scrubs the site and broadcasts to active channels."""
    while True:
        try:
            # 1. Headlines for categories
            for cat in CATEGORIES:
                channel = f"news:{cat}:headline"
                if channel in manager.active_connections:
                    try:
                        # Send syncing status to all connections in channel
                        for ws in manager.active_connections[channel]:
                            await manager.send_status(ws, "syncing", f"Syncing {cat} headlines")
                        headlines = await scrub_headlines(cat)
                        if headlines:
                            await manager.broadcast(channel, {"type": "data", "data": [h.model_dump() for h in headlines]})
                            for ws in manager.active_connections[channel]:
                                await manager.send_status(ws, "ready", "Sync complete")
                    except Exception as e:
                        print(f"Error broadcasting headlines for {cat}: {e}")
    
            # 2. Live TV
            live_channel = "news:liveTV"
            if live_channel in manager.active_connections:
                try:
                    for ws in manager.active_connections[live_channel]:
                        await manager.send_status(ws, "syncing", "Syncing Live TV")
                    live_data = await scrub_live_tv()
                    if live_data:
                        await manager.broadcast(live_channel, {"type": "data", "data": live_data.model_dump()})
                        for ws in manager.active_connections[live_channel]:
                            await manager.send_status(ws, "ready", "Sync complete")
                except Exception as e:
                    print(f"Error broadcasting live TV: {e}")
    
            # 3. Cartoons Headlines
            cartoon_headline_channel = "news:Cartoons:headline"
            if cartoon_headline_channel in manager.active_connections:
                try:
                    for ws in manager.active_connections[cartoon_headline_channel]:
                        await manager.send_status(ws, "syncing", "Syncing Cartoons")
                    cartoons = await scrub_cartoons()
                    if cartoons:
                        await manager.broadcast(cartoon_headline_channel, {"type": "data", "data": [h.model_dump() for h in cartoons]})
                        for ws in manager.active_connections[cartoon_headline_channel]:
                            await manager.send_status(ws, "ready", "Sync complete")
                except Exception as e:
                    print(f"Error broadcasting cartoons: {e}")

            # 4. Popular Today
            popular_channel = "news:popular:headline"
            if popular_channel in manager.active_connections:
                try:
                    for ws in manager.active_connections[popular_channel]:
                        await manager.send_status(ws, "syncing", "Syncing Popular")
                    popular_data = await scrub_popular()
                    if popular_data:
                        await manager.broadcast(popular_channel, {"type": "data", "data": [h.model_dump() for h in popular_data]})
                        for ws in manager.active_connections[popular_channel]:
                            await manager.send_status(ws, "ready", "Sync complete")
                except Exception as e:
                    print(f"Error broadcasting popular: {e}")
        except Exception as e:
            print(f"Background scrubber error: {e}")
            
        # Wait for some time before next scrub (e.g., 5 minutes)
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_scrubber())

@app.websocket("/ws/{channel:path}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    await manager.connect(websocket, channel)
    
    # Send loading status
    await manager.send_status(websocket, "loading", "Connecting to channel")
    
    # Initial data push
    try:
        # Send fetching status
        await manager.send_status(websocket, "fetching", "Fetching initial data")
        
        if ":headline" in channel:
            if "Cartoons" in channel:
                data = await scrub_cartoons()
            elif "popular" in channel:
                data = await scrub_popular()
            else:
                parts = channel.split(":")
                if len(parts) > 1:
                    cat = parts[1]
                    data = await scrub_headlines(cat)
                else:
                    data = []
            if data:
                await websocket.send_json({"type": "data", "data": [h.model_dump() for h in data]})
            else:
                await websocket.send_json({"type": "data", "data": []})
            await manager.send_status(websocket, "ready", "Data loaded")
            
        elif ":topic_detail:" in channel:
            # Format: news:{CAT}:topic_detail:{route}
            # Or news:Cartoons:topic_detail:{route}
            parts = channel.split(":topic_detail:")
            if len(parts) > 1:
                route = parts[1]
                # Reconstruct full URL if needed or use route as is if it's full URL
                url = route if route.startswith("http") else f"https://3news.com/{route}"
                detail = await scrub_article_detail(url)
                if detail:
                    await websocket.send_json({"type": "data", "data": detail.model_dump()})
                    await manager.send_status(websocket, "ready", "Article loaded")
                else:
                    await websocket.send_json({"type": "error", "error": "Article not found"})
                    await manager.send_status(websocket, "error", "Article not found")
                    
        elif channel == "news:liveTV":
            live_data = await scrub_live_tv()
            if live_data:
                await websocket.send_json({"type": "data", "data": live_data.model_dump()})
                await manager.send_status(websocket, "ready", "Live TV loaded")
            else:
                await websocket.send_json({"type": "error", "error": "Live TV not found"})
                await manager.send_status(websocket, "error", "Live TV not found")

        # Keep connection open
        while True:
            # Wait for any message from client (or just keep alive)
            data = await websocket.receive_text()
            # Handle client messages if needed
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.send_status(websocket, "error", str(e))
        manager.disconnect(websocket, channel)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
