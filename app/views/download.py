import logging

from aiohttp import web
from telethon.tl.custom import Message
from telethon.errors import FileMigrateError

from app.util import get_file_name
from app.config import block_downloads
from .base import BaseView

log = logging.getLogger(__name__)


class Download(BaseView):
    async def download_get(self, req: web.Request) -> web.Response:
        return await self.handle_request(req)

    async def download_head(self, req: web.Request) -> web.Response:
        return await self.handle_request(req, head=True)

    async def _safe_download_iter(self, client, message, offset, limit):
        """
        A safe iterator that handles FileMigrateError by switching DC
        and retrying the download without crashing.
        """
        while True:
            try:
                async for chunk in client.iter_download(
                    message,
                    offset=offset,
                    limit=limit - offset  # calculate max bytes to stream
                ):
                    yield chunk
                break

            except FileMigrateError as e:
                log.warning(f"File is located in DC {e.new_dc}, switching…")
                await client._switch_dc(e.new_dc)
                # Retry from same offset
                continue

    async def handle_request(self, req: web.Request, head: bool = False) -> web.Response:
        if block_downloads:
            return web.Response(status=403, text="403: Forbidden" if not head else None)

        file_id = int(req.match_info["id"])
        alias_id = req.match_info["chat"]
        chat = self.chat_ids[alias_id]
        chat_id = chat["chat_id"]

        # Fetch message
        try:
            message: Message = await self.client.get_messages(
                entity=chat_id, ids=file_id
            )
        except Exception:
            log.debug(f"Error fetching message {file_id} in {chat_id}", exc_info=True)
            message = None

        if not message or not message.file:
            log.debug(f"No result for {file_id} in {chat_id}")
            return web.Response(
                status=410,
                text="410: Gone. Resource no longer available!" if not head else None,
            )

        size = message.file.size
        file_name = get_file_name(message, quote_name=False)
        mime_type = message.file.mime_type

        # Range handling
        try:
            offset = req.http_range.start or 0
            limit = req.http_range.stop or size
            if (limit > size) or (offset < 0) or (limit < offset):
                raise ValueError("Invalid byte range")
        except ValueError:
            return web.Response(
                status=416,
                text="416: Range Not Satisfiable" if not head else None,
                headers={"Content-Range": f"bytes */{size}"},
            )

        # Streaming mode
        if not head:
            log.info(
                f"Serving file {message.id} (chat {chat_id}) | Range: {offset}-{limit}"
            )

            async def stream_response():
                async for chunk in self._safe_download_iter(
                    self.client, message, offset, limit
                ):
                    yield chunk

            body = stream_response()

        else:
            body = None

        headers = {
            "Content-Type": mime_type,
            "Content-Range": f"bytes {offset}-{limit}/{size}",
            "Content-Length": str(limit - offset),
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'attachment; filename="{file_name}"',
        }

        status = 206 if offset else 200
        return web.Response(status=status, body=body, headers=headers)
