# API Documentation

A clean JSON API for accessing and streaming media files from Telegram channels with intelligent metadata parsing and grouping.

## Base URL

```
/api
```

## Endpoints

### 1. API Root
**GET** `/api`

Returns API status and available endpoints.

**Response:**
```json
{
  "status": "ok",
  "version": 2,
  "endpoints": {
    "status": "/api",
    "chats": "/api/chats",
    "chat_items": "/api/{alias}/items?page=1&search=",
    "search": "/api/search?q=term&page=1",
    "thumbnail": "/{chat}/{id}/thumbnail",
    "download": "/{chat}/{id}/{filename}",
    "stream": "/{chat}/{id}/{filename}"
  },
  "authenticated": true
}
```

---

### 2. List Available Chats
**GET** `/api/chats`

Returns all configured Telegram chats/channels.

**Response:**
```json
{
  "count": 2,
  "items": [
    {
      "alias": "MNH",
      "title": "Movies Channel",
      "logo_url": "/MNH/logo",
      "index_url": "/api/MNH/items"
    },
    {
      "alias": "JHQ",
      "title": "Series Channel",
      "logo_url": "/JHQ/logo",
      "index_url": "/api/JHQ/items"
    }
  ]
}
```

---

### 3. Get Chat Items
**GET** `/api/{alias}/items`

Retrieve paginated items from a specific chat with optional search.

**Parameters:**
- `page` (optional, default: 1) - Page number
- `search` (optional) - Search query

**Example:** `GET /api/MNH/items?page=1&search=2024`

**Response:**
```json
{
  "chat": {
    "alias": "MNH",
    "title": "Movies Channel",
    "logo_url": "/MNH/logo"
  },
  "page": 1,
  "per_page": 50,
  "prev_page": null,
  "next_page": 2,
  "block_downloads": false,
  "results": [
    {
      "title": "Inception",
      "year": 2010,
      "type": "movie",
      "languages": ["English"],
      "sources": [
        {
          "file_id": 12345,
          "caption": "Inception (2010) 1080p HEVC",
          "quality": "1080p HEVC",
          "human_size": "1.2 GB",
          "thumbnail_url": "/movies/12345/thumbnail",
          "stream_url": "/MNH/12345/Inception.2010.1080p.HEVC.mkv",
          "download_url": "/MNH/12345/Inception.2010.1080p.HEVC.mkv"
        }
      ]
    }
  ]
}
```

---

### 4. Search Specific Item
**GET** `/api/{chat}/item?title=...&year=...`

Search Within Chat Across All Page

**Response:**
```json
{
  "chat": {
    "alias": "GKQ",
    "title": "Chinese Movie",
    "logo_url": "/GKQ/logo"
  },
  "query": {
    "title": "Crazy Fist",
    "year": 2021
  },
  "found": true,
  "total_items_found": 3,
  "total_groups": 1,
  "results": [
    {
      "title": "Crazy Fist",
      "year": 2021,
      "type": "movie",
      "languages": [
        "Hindi",
        "Dual Audio",
        "Chinese"
      ],
      "sources": [
        {
          "file_id": 214,
          "caption": "Crazy Fist (2021) 1080p HDRip Chinese Movie ORG. Dual Audio [Hindi or Chinese]AAC 5.1 x264 ESubs.Mkv",
          "quality": "1080p",
          "human_size": "1.85 GB",
          "thumbnail_url": "/GKQ/214/thumbnail",
          "stream_url": "/GKQ/214/%40Highway100Bittu%F0%9F%87%AE%F0%9F%87%B3Crazy_Fist_2021_1080p_HDRip_Dual_Audio_Hin.mkv?token=MjIyMzQ1ODE5MjoyMTQ6MTc2NTQyNjcxMjo0VXQ0aHF4SnlJOUgwT1Q2ZFpjc3llU3MyT0lDY3gzOXFYUjhiVWcwaU04PQ==",
          "download_url": "/GKQ/214/%40Highway100Bittu%F0%9F%87%AE%F0%9F%87%B3Crazy_Fist_2021_1080p_HDRip_Dual_Audio_Hin.mkv?token=MjIyMzQ1ODE5MjoyMTQ6MTc2NTQyNjcxMjo0VXQ0aHF4SnlJOUgwT1Q2ZFpjc3llU3MyT0lDY3gzOXFYUjhiVWcwaU04PQ=="
        },
        {
          "file_id": 213,
          "caption": "Crazy Fist (2021) 720p HDRip Chinese Movie ORG. Dual Audio [Hindi or Chinese]AAC 5.1 x264 ESubs.Mkv",
          "quality": "720p",
          "human_size": "874.89 MB",
          "thumbnail_url": "/GKQ/213/thumbnail",
          "stream_url": "/GKQ/213/%40Highway100Bittu%F0%9F%87%AE%F0%9F%87%B3Crazy_Fist_2021_720p_HDRip_Dual_Audio_Hind.mkv?token=MjIyMzQ1ODE5MjoyMTM6MTc2NTQyNjcxMjpQVnJKR2NRcFFXclBhaTlHNkxsbE5neGlNR3hSZ1lUNnY5M2taN1JOa1RnPQ==",
          "download_url": "/GKQ/213/%40Highway100Bittu%F0%9F%87%AE%F0%9F%87%B3Crazy_Fist_2021_720p_HDRip_Dual_Audio_Hind.mkv?token=MjIyMzQ1ODE5MjoyMTM6MTc2NTQyNjcxMjpQVnJKR2NRcFFXclBhaTlHNkxsbE5neGlNR3hSZ1lUNnY5M2taN1JOa1RnPQ=="
        }
  ],
  "block_downloads": false
}
```

---

### 5. Global Search
**GET** `/api/search`

Search across all chats.

**Parameters:**
- `q` (required) - Search query
- `page` (optional, default: 1) - Page number

**Example:** `GET /api/search?q=avengers&page=1`

**Response:**
```json
{
  "query": "avengers",
  "page": 1,
  "per_page": 50,
  "results": [
    {
      "title": "Avengers: Endgame",
      "year": 2019,
      "type": "movie",
      "languages": ["English", "Hindi"],
      "sources": [
        {
          "file_id": 67890,
          "caption": "Avengers: Endgame (2019) 2160p 10bit",
          "quality": "2160p 10bit",
          "human_size": "4.5 GB",
          "thumbnail_url": "/movies/67890/thumbnail",
          "stream_url": "/movies/67890/Avengers.Endgame.2019.2160p.10bit.mkv",
          "download_url": "/movies/67890/Avengers.Endgame.2019.2160p.10bit.mkv"
        }
      ]
    }
  ],
  "block_downloads": false
}
```

---

## File URLs

### Thumbnail
**GET** `/{chat}/{id}/thumbnail`

Returns the thumbnail image for a file.

### Download
**GET** `/{chat}/{id}/{filename}`

Downloads the file directly.

### Stream
**GET** `/{chat}/{id}/{filename}`

Streams the file with support for range requests (partial content).

---

## Metadata Features

### Automatic Detection
The API automatically detects and extracts:
- **Title** (cleaned from file/caption)
- **Year** (extracted from parentheses)
- **Quality** (2160p, 1080p HEVC, 720p 10bit, etc.)
- **Type** (movie or series)
- **Season/Episode** (for series)
- **Languages** (Hindi, English, Tamil, etc.)
- **File size** (human-readable format)

### Quality Sorting Order
Files are sorted by quality in this order:
1. 2160p 10bit
2. 2160p HEVC
3. 2160p
4. 1080p 10bit
5. 1080p HEVC
6. 1080p
7. 720p 10bit
8. 720p HEVC
9. 720p
10. 480p 10bit
11. 480p HEVC
12. 480p
13. 360p
14. unknown

### Grouping Logic
- **Movies**: Grouped by title and year, with multiple quality sources
- **Series**: Grouped by title and season, with episodes sorted numerically
- **Episode ranges**: Support for multi-episode files (e.g., E01-E08)

### Language Detection
Supports 18 languages including:
- Hindi, English, Tamil, Telugu, Malayalam, Kannada
- Chinese, Korean, Japanese
- Spanish, French, German, Italian
- Portuguese, Russian, Arabic, Bengali
- Dual Audio, Multi Audio

---

## Query Parameters

### Pagination
- `page`: Page number (default: 1)
- Results per page: Configurable in settings (default: 50)

### Search
- `search` (chat_items): Search within a specific chat
- `q` (global search): Search across all chats

---

## Configuration Flags

The API response includes these configuration flags:
- `block_downloads`: If true, download URLs will be `null`
- `authenticated`: Authentication status

---

## Response Format

All responses include CORS headers for cross-origin requests and return JSON with appropriate HTTP status codes.

### Error Responses
```json
{
  "error": "error_code",
  "status": 400
}
```

Common error codes:
- `chat_not_found` - Invalid chat alias
- `message_not_found` - Message ID doesn't exist
- `file_not_found` - Message has no file
- `fetch_failed` - Failed to fetch from Telegram
- `missing_query` - Search query required
- `unsupported_file_type` - File type excluded (stickers, etc.)

---

## Notes

1. **File Types**: Certain MIME types are excluded (stickers, webp, etc.)
2. **Token Support**: If enabled, download URLs include authentication tokens
3. **Cleaned Captions**: Captions are cleaned to remove metadata after file extensions
4. **Smart Grouping**: Files are intelligently grouped based on cleaned titles and metadata
5. **Episode Ranges**: Supports both single episodes and multi-episode ranges

---

## Example Usage

```javascript
// Get all chats
fetch('/api/chats')
  .then(res => res.json())
  .then(data => console.log(data));

// Search for movies
fetch('/api/search?q=batman&page=1')
  .then(res => res.json())
  .then(data => {
    data.results.forEach(item => {
      console.log(`${item.title} (${item.year})`);
      item.sources.forEach(source => {
        console.log(`  Quality: ${source.quality}, Size: ${source.human_size}`);
        console.log(`  Stream: ${source.stream_url}`);
      });
    });
  });
```
