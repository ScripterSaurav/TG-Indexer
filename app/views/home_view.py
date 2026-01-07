from aiohttp import web
import aiohttp_jinja2

from .base import BaseView
from app.config import is_chat_locked, chat_lock_enabled  # ADD chat_lock_enabled IMPORT


class HomeView(BaseView):
    @aiohttp_jinja2.template("home.html")
    async def home(self, req: web.Request) -> web.Response:
        if len(self.chat_ids) == 1:
            (chat,) = self.chat_ids.values()
            return web.HTTPFound(f"{chat['alias_id']}")

        # Create chats list with lock status
        chats = []
        for alias_id, chat in self.chat_ids.items():
            chat_id = chat['chat_id']
            
            # Check if this chat is locked - ONLY if chat lock is globally enabled
            is_locked = chat_lock_enabled and is_chat_locked(chat_id)
            
            chats.append({
                "page_id": chat["alias_id"],
                "name": chat["title"],
                "url": f"/{chat['alias_id']}",
                "is_locked": is_locked  # ADD LOCK STATUS
            })

        return {
            "chats": chats,
            "authenticated": req.app["is_authenticated"],
        }
