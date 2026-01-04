import asyncio
import websockets
import json

async def test_status_events():
    uri = "ws://localhost:8000/ws/news:HOME:headline"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for messages...\n")
            
            # Receive messages for 10 seconds
            timeout = 10
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "status":
                        status_data = data.get("data", {})
                        print(f"[STATUS] {status_data.get('status')}: {status_data.get('message')}")
                        print(f"  Timestamp: {status_data.get('timestamp')}\n")
                    elif data.get("type") == "data":
                        print(f"[DATA] Received {len(data.get('data', []))} items\n")
                    elif data.get("type") == "error":
                        print(f"[ERROR] {data.get('error')}\n")
                    else:
                        print(f"[UNKNOWN] {data}\n")
                        
                except asyncio.TimeoutError:
                    continue
                    
            print("Test completed!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_status_events())
