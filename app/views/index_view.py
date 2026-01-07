# index_view.py - Add minimal token support
import logging
import re
from typing import List
from urllib.parse import quote

import aiohttp_jinja2
from aiohttp import web
from telethon.tl import types, custom

from app.config import results_per_page, block_downloads, token_validation_enabled
from app.util import get_file_name, get_human_size
from app.token_util import generate_download_token  # Add this import
from .base import BaseView

log = logging.getLogger(__name__)

class IndexView(BaseView):
    @aiohttp_jinja2.template("index.html")
    async def index(self, req: web.Request) -> web.Response:
        alias_id = req.match_info["chat"]
        chat = self.chat_ids[alias_id]
        log_msg = ""
        try:
            offset_val = int(req.query.get("page", "1"))
        except Exception:
            offset_val = 1

        log_msg += f"page: {offset_val} | "
        try:
            search_query = req.query.get("search", "")
        except Exception:
            search_query = ""

        log_msg += f"search query: {search_query} | "
        offset_val = max(offset_val - 1, 0)
        
        try:
            kwargs = {
                "entity": chat["chat_id"],
                "limit": results_per_page,
                "add_offset": results_per_page * offset_val,
            }
            if search_query:
                kwargs.update({"search": search_query})

            messages: List[custom.Message] = await self.client.get_messages(**kwargs) or []

        except Exception:
            log.debug("failed to get messages", exc_info=True)
            messages = []

        log_msg += f"found {len(messages)} results | "
        log.debug(log_msg)
        results = []
        
        for m in messages:
            if m.media and isinstance(m.media, types.MessageMediaDocument) and m.media.document.mime_type == "application/x-tgsticker":
                # Skip sticker messages
                continue
            elif m.file and m.file.mime_type == "image/webp":
                # Skip regular sticker images (webp files)
                continue
            elif m.file and m.file.mime_type == "video/mp4" and (m.file.name or "").endswith("animation.gif.mp4"):
                # Skip Telegram gif-style sticker messages (animation.gif.mp4)
                continue
            elif m.file and m.file.mime_type.startswith("audio/"):
                # Skip audio files
                continue
            elif m.file and m.file.mime_type == "application/zip":
                # Skip zip files
                continue
                
            entry = None
            if m.file and not isinstance(m.media, types.MessageMediaWebPage) and m.file.mime_type not in ["image/jpeg", "image/png"]:
                filename = get_file_name(m, quote_name=False)
                
                # Use the full caption name or fallback filename, no length limit unlike insight
                caption = m.text if m.text else filename
                # Remove '**' and '`' __ characters from the caption 
                caption = re.sub(r'(\*\*|`|__)', '', caption)

                
                # remove file extension Use the full caption name or fallback filename, no length limit unlike insight
                caption2 = m.text if m.text else filename
                # Remove common file extensions like .mp4, .mp3, .mkv, etc.
                caption2 = caption2.replace('.mkv', '').replace('.MKV', '') 
                caption2 = caption2.replace('.mp4', '').replace('.MP4', '')
                # Remove '**' and '`' __ characters from the caption 
                caption2 = re.sub(r'(\*\*|`|__)', '', caption2)

                # ---- CLEAN CAPTION3 (remove trash after extension, then remove extension) ----
                caption3 = m.text if m.text else filename
                # --- STEP 0: Normalize formatting (fix italic/bold breaking .mkv matching) ---
                caption3 = caption3.replace("*", "").replace("_", "").replace("`", "")
                # --- STEP 1: remove everything AFTER the extension (.mkv, .mp4) ---
                match_ext = re.match(r'^(.*?)(?:\.(mkv|mp4))\b', caption3, flags=re.IGNORECASE)
                if match_ext:
                    caption3 = match_ext.group(1)  # keep text before extension
                # --- STEP 2: remove extension itself ---
                caption3 = re.sub(r'\.(mkv|mp4)$', '', caption3, flags=re.IGNORECASE)
                # --- STEP 3: final cleanup ---
                caption3 = caption3.strip().rstrip(".- ")

                # Caption Length Limit to display for insight
                insight = m.text[:120] if m.text else filename
                # Remove special characters and emojis from the insight
                insight = re.sub(r'(?<![a-zA-Z0-9])_|_(?![a-zA-Z0-9])|[^\w\s.:\'+\-()\[\]]', '', insight)
                insight = re.sub(r'\s+', ' ', insight).strip()  # Replace multiple spaces with a single space and trim leading/trailing spaces
                
                # === MINIMAL CHANGE: Generate token for download URLs ===
                download_url = f"{alias_id}/{m.id}/{quote(filename)}"
                download_url2 = f"{alias_id}/{m.id}/{insight}"
                
                if token_validation_enabled:
                    token = generate_download_token(chat["chat_id"], m.id)
                    download_url = f"{download_url}?token={token}"
                    download_url2 = f"{download_url2}?token={token}"
                # === END OF CHANGE ===
                
                entry = dict(
                    file_id=m.id,
                    media=True,
                    thumbnail=f"/{alias_id}/{m.id}/thumbnail",
                    mime_type=m.file.mime_type,
                    filename=filename,
                    caption=caption,
                    caption2=caption2,
                    caption3=caption3,
                    insight=insight,
                    human_size=get_human_size(m.file.size),
                    watchPage=f"/{alias_id}/{m.id}/watch",
                    downloadPage=f"/{alias_id}/{m.id}/downloadPG",
                    download=download_url,  # Now includes token if enabled
                    download2=download_url2,  # Now includes token if enabled
                ) 
            elif m.message and m.message.startswith("🤔"):
                # Skip emoji messages
                continue
            elif m.message and m.message.strip():
                # Skip text messages
                continue
            elif m.message:
                # Handle empty or plain text messages with character cleaning (The entire block serves to handle text messages that do not contain any media.)
                # Remove special characters and emojis from the message
                message = re.sub(r'(?<![a-zA-Z0-9])_|_(?![a-zA-Z0-9])|[^\w\s.:\'+\-()\[\]]', '', m.message)
                message = re.sub(r'\s+', ' ', m.message).strip()  # Replace multiple spaces with a single space and trim leading/trailing spaces

                entry = dict(
                    file_id=m.id,
                    media=False,
                    mime_type="text/plain",
                    insight=message[:100],
                    caption=message,
                    watchPage=f"/{alias_id}/{m.id}/watch",
                )
            if entry:
                results.append(entry)

        prev_page = None
        next_page = None
        if offset_val:
            query = {"page": offset_val + 1}
            if search_query:
                query.update({"search": search_query})
            prev_page = {"url": str(req.rel_url.with_query(query)), "no": offset_val}

        if len(messages) == results_per_page:
            query = {"page": offset_val + 2}
            if search_query:
                query.update({"search": search_query})
            next_page = {
                "url": str(req.rel_url.with_query(query)),
                "no": offset_val + 2,
            }

        return {
            "item_list": results,
            "prev_page": prev_page,
            "cur_page": offset_val + 1,
            "next_page": next_page,
            "search": search_query,
            "name": chat["title"],
            "logo": f"/{alias_id}/logo",
            "title": "watchOflix | searching in " + chat["title"],
            "authenticated": req.app["is_authenticated"],
            "block_downloads": block_downloads,
            "m3u_option": ""
            if not req.app["is_authenticated"]
            else f"{req.app['username']}:{req.app['password']}@",
        }
