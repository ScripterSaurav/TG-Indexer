import logging
import io
import hashlib
from pathlib import Path
from aiohttp import web
from PIL import Image

from telethon.tl import types, custom
from .base import BaseView

log = logging.getLogger(__name__)

# Absolute fallback
FALLBACK_THUMBNAIL_PATH = Path("app/static/img/fallback_thumbnail.png").resolve()

# Simple in-memory cache
# Structure: { "chat_id:file_id": {etag, body, content_type} }
THUMB_CACHE = {}


class ThumbnailView(BaseView):

    async def thumbnail_get(self, req: web.Request) -> web.Response:
        file_id = int(req.match_info["id"])
        alias_id = req.match_info["chat"]

        chat = self.chat_ids[alias_id]
        chat_id = chat["chat_id"]

        cache_key = f"{chat_id}:{file_id}"

        # ========= CHECK MEMORY CACHE =========
        if cache_key in THUMB_CACHE:
            cached = THUMB_CACHE[cache_key]

            # Check ETag match
            if req.headers.get("If-None-Match") == cached["etag"]:
                return web.Response(status=304)

            return web.Response(
                status=200,
                body=cached["body"],
                headers={
                    "Content-Type": cached["content_type"],
                    "ETag": cached["etag"],
                    "Cache-Control": "public, max-age=86400",
                },
            )

        # ========= GET MESSAGE =========
        try:
            message: custom.Message = await self.client.get_messages(
                entity=chat_id, ids=file_id
            )
        except Exception:
            log.debug(f"Error getting message {file_id}", exc_info=True)
            return self._fallback_response(cache_key)

        if not message or not message.file:
            return self._fallback_response(cache_key)

        # ========= MEDIA TYPE =========
        if message.document:
            media = message.document
            thumbnails = media.thumbs
            location = types.InputDocumentFileLocation
        elif message.photo:
            media = message.photo
            thumbnails = media.sizes
            location = types.InputPhotoFileLocation
        else:
            return self._fallback_response(cache_key)

        if not thumbnails:
            return self._fallback_response(cache_key)

        # ========= SELECT THUMBNAIL =========
        thumb_pos = len(thumbnails) // 2
        try:
            thumbnail: types.PhotoSize = self.client._get_thumb(thumbnails, thumb_pos)
        except:
            return self._fallback_response(cache_key)

        if not thumbnail or isinstance(thumbnail, types.PhotoSizeEmpty):
            return self._fallback_response(cache_key)

        # ========= DOWNLOAD THUMBNAIL =========
        try:
            if isinstance(thumbnail, (types.PhotoCachedSize, types.PhotoStrippedSize)):
                data = self.client._download_cached_photo_size(thumbnail, bytes)
            else:
                input_loc = location(
                    id=media.id,
                    access_hash=media.access_hash,
                    file_reference=media.file_reference,
                    thumb_size=thumbnail.type,
                )

                # iter_download = async generator
                buf = bytearray()
                async for chunk in self.client.iter_download(input_loc):
                    buf.extend(chunk)
                data = bytes(buf)
        except Exception:
            return self._fallback_response(cache_key)

        # ========= CONVERT TO WEBP =========
        webp_data = self._convert_to_webp(data)

        # ========= STORE IN CACHE =========
        etag = hashlib.md5(webp_data).hexdigest()

        THUMB_CACHE[cache_key] = {
            "body": webp_data,
            "etag": etag,
            "content_type": "image/webp",
        }

        # ========= RESPONSE =========
        return web.Response(
            status=200,
            body=webp_data,
            headers={
                "Content-Type": "image/webp",
                "ETag": etag,
                "Cache-Control": "public, max-age=86400",
            },
        )

    # ========= WEBP CONVERSION =========
    def _convert_to_webp(self, data: bytes) -> bytes:
        try:
            img = Image.open(io.BytesIO(data))
            buf = io.BytesIO()
            img.save(buf, format="WEBP", quality=75)
            return buf.getvalue()
        except:
            log.error("WEBP convert failed, returning original", exc_info=True)
            return data  # fallback to original

    # ========= FALLBACK HANDLER =========
    def _fallback_response(self, cache_key):
        try:
            with open(FALLBACK_THUMBNAIL_PATH, "rb") as f:
                data = f.read()
        except:
            data = b""

        webp_data = self._convert_to_webp(data)
        etag = hashlib.md5(webp_data).hexdigest()

        THUMB_CACHE[cache_key] = {
            "body": webp_data,
            "etag": etag,
            "content_type": "image/webp",
        }

        return web.Response(
            status=200,
            body=webp_data,
            headers={
                "Content-Type": "image/webp",
                "ETag": etag,
                "Cache-Control": "public, max-age=86400",
            },
        )
