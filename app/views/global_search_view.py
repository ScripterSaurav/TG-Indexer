import logging
import re
from typing import List
from urllib.parse import quote

import aiohttp_jinja2
from aiohttp import web
from telethon.tl import types, custom

from app.config import results_per_page, block_downloads
from app.util import get_file_name, get_human_size
from .base import BaseView

log = logging.getLogger(__name__)

class GlobalSearchView(BaseView):
    @aiohttp_jinja2.template("global_search.html")
    async def global_search(self, req: web.Request) -> web.Response:
        log_msg = ""
        try:
            offset_val = int(req.query.get("page", "1"))
        except Exception:
            offset_val = 1

        log_msg += f"page: {offset_val} | "
        try:
            search_query = req.query.get("q", "").strip()
        except Exception:
            search_query = ""

        if not search_query:
            return {
                "item_list": [],
                "prev_page": None,
                "cur_page": 1,
                "next_page": None,
                "search": "",
                "title": "Global Search - watchOflix",
                "authenticated": req.app["is_authenticated"],
                "block_downloads": block_downloads,
            }

        log_msg += f"global search query: {search_query} | "
        offset_val = max(offset_val - 1, 0)
        
        all_results = []
        
        # Search across all channels
        for alias_id, chat in self.chat_ids.items():
            try:
                kwargs = {
                    "entity": chat["chat_id"],
                    "limit": results_per_page,
                    "add_offset": results_per_page * offset_val,
                    "search": search_query,
                }

                messages: List[custom.Message] = await self.client.get_messages(**kwargs) or []

            except Exception:
                log.debug(f"failed to get messages from {chat['title']}", exc_info=True)
                messages = []

            for m in messages:
                # Apply the same filters as in IndexView
                if m.media and isinstance(m.media, types.MessageMediaDocument) and m.media.document.mime_type == "application/x-tgsticker":
                    continue
                elif m.file and m.file.mime_type == "image/webp":
                    continue
                elif m.file and m.file.mime_type == "video/mp4" and (m.file.name or "").endswith("animation.gif.mp4"):
                    continue
                elif m.file and m.file.mime_type.startswith("audio/"):
                    continue
                elif m.file and m.file.mime_type == "application/zip":
                    continue
                    
                entry = None
                if m.file and not isinstance(m.media, types.MessageMediaWebPage) and m.file.mime_type not in ["image/jpeg", "image/png"]:
                    filename = get_file_name(m, quote_name=False)
                    
                    # Use the full caption name or fallback filename
                    caption = m.text if m.text else filename
                    caption = re.sub(r'(\*\*|`|__)', '', caption)

                    # Remove file extensions for cleaner display
                    caption2 = m.text if m.text else filename
                    caption2 = caption2.replace('.mkv', '').replace('.MKV', '') 
                    caption2 = caption2.replace('.mp4', '').replace('.MP4', '')
                    caption2 = re.sub(r'(\*\*|`|__)', '', caption2)

                    # Insight for display
                    insight = m.text[:120] if m.text else filename
                    insight = re.sub(r'(?<![a-zA-Z0-9])_|_(?![a-zA-Z0-9])|[^\w\s.:\'+\-()\[\]]', '', insight)
                    insight = re.sub(r'\s+', ' ', insight).strip()
                    
                    entry = dict(
                        file_id=m.id,
                        media=True,
                        thumbnail=f"/{alias_id}/{m.id}/thumbnail",
                        mime_type=m.file.mime_type,
                        filename=filename,
                        caption=caption,
                        caption2=caption2,
                        insight=insight,
                        human_size=get_human_size(m.file.size),
                        channel_name=chat["title"],
                        channel_alias=alias_id,
                        url=f"/{alias_id}/{m.id}/watch",
                        download=f"{alias_id}/{m.id}/{quote(filename)}",
                        download2=f"{alias_id}/{m.id}/{insight}",
                    ) 
                elif m.message and m.message.startswith("🤔"):
                    continue
                elif m.message and m.message.strip():
                    continue
                elif m.message:
                    message = re.sub(r'(?<![a-zA-Z0-9])_|_(?![a-zA-Z0-9])|[^\w\s.:\'+\-()\[\]]', '', m.message)
                    message = re.sub(r'\s+', ' ', m.message).strip()

                    entry = dict(
                        file_id=m.id,
                        media=False,
                        mime_type="text/plain",
                        insight=message[:100],
                        caption=message,
                        channel_name=chat["title"],
                        channel_alias=alias_id,
                        url=f"/{alias_id}/{m.id}/watch",
                    )
                
                if entry:
                    all_results.append(entry)

        log_msg += f"found {len(all_results)} results across all channels | "
        log.debug(log_msg)

        # Sort results by relevance (you can implement more sophisticated sorting)
        # For now, just return as is

        prev_page = None
        next_page = None
        
        if offset_val > 0:
            query = {"page": offset_val, "q": search_query}
            prev_page = {"url": str(req.rel_url.with_query(query)), "no": offset_val}

        if len(all_results) >= results_per_page:
            query = {"page": offset_val + 2, "q": search_query}
            next_page = {
                "url": str(req.rel_url.with_query(query)),
                "no": offset_val + 2,
            }

        return {
            "item_list": all_results,
            "prev_page": prev_page,
            "cur_page": offset_val + 1,
            "next_page": next_page,
            "search": search_query,
            "title": f"Global Search: {search_query} - watchOflix",
            "authenticated": req.app["is_authenticated"],
            "block_downloads": block_downloads,
            "m3u_option": ""
            if not req.app["is_authenticated"]
            else f"{req.app['username']}:{req.app['password']}@",
        }
