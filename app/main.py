# main.py (updated)
import asyncio
import pathlib
import logging

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from .telegram import Client
from .routes import setup_routes
from .views import Views, middleware_factory
from .botCode import start_bot  # Import the bot's async start function
from .config import (
    host,
    port,
    session_string,
    api_id,
    api_hash,
    authenticated,
    username,
    password,
    SESSION_COOKIE_LIFETIME,
    SECRET_KEY,
    chat_lock_enabled,        
    chat_lock_session_lifetime,
)

log = logging.getLogger(__name__)

class Indexer:

    TEMPLATES_ROOT = pathlib.Path(__file__).parent / "templates"
    STATIC_ROOT = pathlib.Path(__file__).parent / "static"
    
    def __init__(self):
        middlewares = []

        # ===== SESSION / AUTH MIDDLEWARE =====
        if authenticated or chat_lock_enabled:  # main authentication + chat lock 
            middlewares.append(
                session_middleware(
                    EncryptedCookieStorage(
                        secret_key=SECRET_KEY.encode(),
                        max_age=60 * SESSION_COOKIE_LIFETIME,
                        cookie_name="TG_INDEX_SESSION",
                        secure=True,
                    )
                )
            )

        middlewares.append(middleware_factory())
        self.loop = asyncio.get_event_loop()

        # ===== WEB SERVER APP =====
        self.server = web.Application(middlewares=middlewares)

        # Add static route - it maps all static files to the /static/ URL prefix.
        self.server.router.add_static('/static/', self.STATIC_ROOT, name='static')

        self.server.on_startup.append(self.startup)
        self.server.on_cleanup.append(self.cleanup)

        # ===== TELETHON USER CLIENT =====
        self.tg_client = Client(session_string, api_id, api_hash)

        self.server["is_authenticated"] = authenticated
        self.server["username"] = username
        self.server["password"] = password

        # chat lock authentication
        self.server["chat_lock_enabled"] = chat_lock_enabled
        self.server["chat_lock_session_lifetime"] = chat_lock_session_lifetime

    async def startup(self, server: web.Application):
        await self.tg_client.start()
        log.debug("telegram client started!")

        # Start the bot - ONLY CHANGE MADE HERE
        asyncio.create_task(start_bot())
        log.debug("Bot started successfully!")

        views = Views(self.tg_client)
        server["views"] = views
        
        await setup_routes(server, views)

        loader = jinja2.FileSystemLoader(str(self.TEMPLATES_ROOT))
        aiohttp_jinja2.setup(server, loader=loader)

    async def cleanup(self, server: web.Application):
        await self.tg_client.disconnect()
        log.debug("Telegram user client disconnected!")

    def run(self):
        web.run_app(self.server, host=host, port=port, loop=self.loop)
