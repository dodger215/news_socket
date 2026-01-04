# 3News Scraper WebSocket API

This project provides a real-time news scraping service for [3news.com](https://3news.com) using FastAPI and WebSockets.

## WebSocket Connection

Connect to the WebSocket server at:
`ws://localhost:8000/ws/{channel}`

## Message Format

All WebSocket messages follow a structured format with a `type` field:

### Status Events
Status events track the data fetching state:

```json
{
  "type": "status",
  "data": {
    "status": "loading|fetching|syncing|ready|error",
    "message": "Optional status message",
    "timestamp": "2026-01-04T00:13:41.951352"
  }
}
```

**Status Types:**
- `loading`: Connection established, initializing
- `fetching`: Fetching initial data
- `syncing`: Background sync in progress (periodic updates)
- `ready`: Data successfully loaded/synced
- `error`: An error occurred

### Data Messages
Data messages contain the actual scraped content:

```json
{
  "type": "data",
  "data": [/* array of items or single object */]
}
```

### Error Messages
Error messages indicate failures:

```json
{
  "type": "error",
  "error": "Error description"
}
```

## Channels

### 1. Headlines
Get the latest headlines for a specific category.

- **Channel Format**: `news:{CATEGORY}:headline`
- **Categories**: `HOME`, `NEWS`, `POLITICS`, `ENTERTAINMENT`, `SPORTS`, `BUSINESS`, `OPINION`, `VIDEOS`, `ELECTIONS`
- **Example**: `news:POLITICS:headline`
- **Response**: A list of `Headline` objects.

```json
{
  "type": "data",
  "data": [
    {
      "topic": "Article Title",
      "images": ["https://example.com/image.jpg"],
      "categories": ["Politics"],
      "isLatest": true,
      "url": "https://3news.com/news/politics/article-slug",
      "route": "/news/politics/article-slug"
    }
  ]
}
```

### 2. Article Details
Get the full content of a specific article.

- **Channel Format**: `news:{CATEGORY}:topic_detail:{route}`
- **Example**: `news:POLITICS:topic_detail:news/politics/some-article-slug`
- **Response**: An `ArticleDetail` object.

```json
{
  "type": "data",
  "data": {
    "topic": "Article Title",
    "images": ["https://example.com/image.jpg"],
    "categories": ["Politics"],
    "descriptions": ["Paragraph 1", "Paragraph 2"],
    "url": "https://3news.com/news/politics/article-slug"
  }
}
```

### 3. Live TV
Get the current live TV stream URL.

- **Channel**: `news:liveTV`
- **Response**: A `LiveTV` object.

```json
{
  "type": "data",
  "data": {
    "video_url": "https://www.youtube.com/embed/...",
    "title": "3News Live TV"
  }
}
```

### 4. Cartoons
Get the latest cartoons from Tilapia Corner.

- **Channel**: `news:Cartoons:headline`
- **Response**: A list of `Headline` objects.

### 5. Popular Today
Get the trending articles from the "Popular Today 24h" section.

- **Channel**: `news:popular:headline`
- **Response**: A list of `Headline` objects.

## Data Models

### Headline
- `topic` (str): The title of the article.
- `images` (List[str]): List of image URLs.
- `categories` (List[str]): List of categories.
- `isLatest` (bool): True if it's the most recent article.
- `url` (str): Full URL to the article.
- `route` (str): Relative path for the article (use this for `topic_detail` channel).

### ArticleDetail
- `topic` (str): The title of the article.
- `images` (List[str]): List of image URLs found in the content.
- `categories` (List[str]): List of categories.
- `descriptions` (List[str]): List of paragraphs from the article content.
- `url` (str): Full URL to the article.

### LiveTV
- `video_url` (str): The URL of the live stream (usually a YouTube embed).
- `title` (str): The title of the stream.

### StatusEvent
- `status` (str): Current status (`loading`, `fetching`, `syncing`, `ready`, `error`).
- `message` (str, optional): Additional context about the status.
- `timestamp` (str): ISO 8601 timestamp of the event.

## Background Updates
The server periodically (every 5 minutes) scrubs the site and broadcasts updates to all active headline and live TV channels. During background updates, clients will receive:
1. A `syncing` status event
2. Updated data
3. A `ready` status event

## Example Usage

```python
import asyncio
import websockets
import json

async def listen_to_news():
    uri = "ws://localhost:8000/ws/news:HOME:headline"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data["type"] == "status":
                print(f"Status: {data['data']['status']}")
            elif data["type"] == "data":
                print(f"Received {len(data['data'])} headlines")

asyncio.run(listen_to_news())
```
