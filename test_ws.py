import asyncio
import websockets
import json

async def test_websocket(channel):
    uri = f"ws://localhost:8000/ws/{channel}"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {channel}")
            # Wait for initial data
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received data for {channel}: {json.dumps(data, indent=2)[:500]}...")
            return True
    except Exception as e:
        print(f"Failed to connect to {channel}: {e}")
        return False

async def main():
    # Test a few channels
    channels = [
        "news:HOME:headline",
        "news:POLITICS:headline",
        "news:liveTV",
        "news:Cartoons:headline",
        "news:popular:headline"
    ]
    
    for channel in channels:
        await test_websocket(channel)

if __name__ == "__main__":
    asyncio.run(main())
