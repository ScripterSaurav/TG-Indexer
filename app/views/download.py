# download.py - Updated with support for both token formats
import logging
from aiohttp import web
from telethon.tl.custom import Message

from app.util import get_file_name
from app.config import block_downloads, token_validation_enabled
from app.token_util import validate_download_token, extract_token_from_path  # Add this import
from .base import BaseView

log = logging.getLogger(__name__)


class Download(BaseView):

    async def download_get(self, req: web.Request) -> web.Response:
        return await self.handle_request(req)

    async def download_head(self, req: web.Request) -> web.Response:
        return await self.handle_request(req, head=True)

    async def handle_request(self, req: web.Request, head: bool = False) -> web.Response:
        # Block downloads if configured
        if block_downloads:
            return web.Response(status=403, text="403: Forbidden" if not head else None)

        file_id = int(req.match_info["id"])
        alias_id = req.match_info["chat"]
        chat = self.chat_ids[alias_id]
        chat_id = chat["chat_id"]

        # === UPDATED: Support both query param and path tokens ===
        if token_validation_enabled:
            # First try query parameter
            token = req.query.get("token")
            
            # If no query token, check if token is in path (for external players)
            if not token:
                token = extract_token_from_path(req.path)
            
            if not validate_download_token(token, chat_id, file_id):
                log.warning(f"Invalid token for download: chat={chat_id}, file={file_id}")
                # Return early to prevent any Telegram API calls
                return web.Response(
                    status=403, 
                    text="403: Forbidden - Invalid or expired token" if not head else None
                )
        # === END OF UPDATE ===

        # get tg message - only proceed if token is valid or token validation is disabled
        try:
            message: Message = await self.client.get_messages(
                entity=chat_id, ids=file_id
            )
        except Exception:
            log.debug(f"Error in getting message {file_id} in {chat_id}", exc_info=True)
            message = None

        if not message or not message.file:
            log.debug(f"No file result for {file_id} in {chat_id}")
            return web.Response(
                status=410,
                text="410: Gone",
            )

        media = message.media
        file_size = message.file.size
        file_name = get_file_name(message, quote_name=False)
        mime_type = message.file.mime_type

        # -------------------------------------------------------------------
        # RANGE PARSING (correct + safe)
        # -------------------------------------------------------------------
        range_header = req.headers.get("Range")

        if range_header:
            # Example: "bytes=1000-2000"
            range_header = range_header.strip().replace("bytes=", "")
            start_str, end_str = range_header.split("-")

            start = int(start_str)
            end = int(end_str) if end_str else file_size - 1

            if start < 0 or end >= file_size or start > end:
                return web.Response(
                    status=416,
                    headers={"Content-Range": f"bytes */{file_size}"},
                )

            status = 206
        else:
            start = 0
            end = file_size - 1
            status = 200

        content_length = (end - start) + 1

        # -------------------------------------------------------------------
        # DOWNLOAD FROM TELETHON
        # -------------------------------------------------------------------
        if not head:
            try:
                # Create the download generator
                body = self.client.download(media, file_size, start, end)
                log.info(f"Serving file {file_name} ; Range={start}-{end}")
            except Exception as e:
                log.error(f"Error creating download stream: {e}")
                return web.Response(
                    status=500,
                    text="500: Internal Server Error"
                )
        else:
            body = None

        # -------------------------------------------------------------------
        # HEADERS
        # -------------------------------------------------------------------
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": mime_type,
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Content-Length": str(content_length),
            "Content-Range": f"bytes {start}-{end}/{file_size}",
        }

        return web.Response(
            status=status,
            body=body,
            headers=headers
        )
