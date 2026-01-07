# downloadPG.py - Updated with token-first URLs
import logging
import re
from urllib.parse import unquote, quote

from aiohttp import web
import aiohttp_jinja2
from markupsafe import Markup
from telethon.tl.custom import Message

from app.util import get_file_name, get_human_size
from app.config import token_validation_enabled
from app.token_util import generate_download_token
from .base import BaseView

log = logging.getLogger(__name__)

class DownloadPGView(BaseView):
    @aiohttp_jinja2.template("downloadPG.html")
    async def downloadPG(self, req: web.Request) -> dict:
        try:
            alias_id = req.match_info["chat"]
            file_id = int(req.match_info["id"])
        except (KeyError, ValueError):
            log.warning("Invalid request parameters")
            return {"error": "Invalid request parameters"}

        chat_info = self.chat_ids.get(alias_id)
        if not chat_info:
            log.warning(f"Alias ID '{alias_id}' not found in chat_ids")
            return {"error": "Chat not found"}

        chat_id = chat_info["chat_id"]

        try:
            message: Message = await self.client.get_messages(chat_id, ids=file_id)
        except Exception:
            log.exception(f"Failed to get message {file_id} from chat {chat_id}")
            return {"error": "File not found"}

        if not message or not message.file:
            return {"error": "Invalid or missing file"}

        file_name = get_file_name(message)
        file_name_decoded = unquote(file_name)
        file_name_encoded = quote(file_name)

        # === UPDATED: Use token-first URLs ===
        token = ""
        if token_validation_enabled:
            token = generate_download_token(chat_id, file_id)
        
        download_url = f"/{alias_id}/{file_id}/{file_name_encoded}"
        stream_url = f"/{alias_id}/{file_id}/{file_name_encoded}"
        external_player_url = f"/{alias_id}/{file_id}/{file_name_encoded}"  # Default without token
        
        if token_validation_enabled and token:
            download_url = f"{download_url}?token={token}"
            stream_url = f"{stream_url}?token={token}"
            external_player_url = f"/{token}/{alias_id}/{file_id}/{file_name_encoded}"
        # === END OF CHANGE ===

        # Raw caption
        raw_caption = message.raw_text or file_name_decoded
        escaped_caption = Markup.escape(raw_caption).replace("\n", "<br>")

        # ----------------------------------
        # CAPTION2 → remove everything after extension, THEN remove extension
        # ----------------------------------
        caption2 = raw_caption

        # Fix italics/bold issues
        caption2 = caption2.replace("*", "").replace("_", "").replace("`", "")

        # Match "anything + extension" and STOP there
        match_ext = re.match(r'^(.*?\.(mkv|mp4))\b', caption2, flags=re.IGNORECASE)

        if match_ext:
            caption2 = match_ext.group(1)  # KEEP full filename including extension

        # Final cleanup
        caption2 = caption2.strip().rstrip(".- ")

        # ----------------------------------

        # Short title without extension (your original code)
        caption_no_ext = re.sub(
            r'\.(mp4|mkv|avi|mov|flv|wmv)$', 
            '', 
            raw_caption, 
            flags=re.IGNORECASE
        )
        title_text = Markup.escape(caption_no_ext)

        return {
            "title": f"Download | {title_text}",
            "file_name": file_name_decoded,
            "file_size": get_human_size(message.file.size),
            "download_url": download_url,
            "stream_url": stream_url,
            "external_player_url": external_player_url,
            "thumbnail": f"/{alias_id}/{file_id}/thumbnail",
            "caption": escaped_caption,
            "caption2": caption2,
            "file_id": file_id,
            "chat_id": chat_id,
            "alias_id": alias_id,
            "name": chat_info["title"],
            "logo": f"/{alias_id}/logo",
            "page_url": f"/{alias_id}/{file_id}/downloadPG",
        }
