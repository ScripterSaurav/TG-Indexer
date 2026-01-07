import logging
import os

from typing import List

from aiohttp import web
from aiohttp.web_routedef import RouteDef
from telethon.tl.types import Channel, Chat, User

from .config import index_settings
from .views import Views
from .views.api_view import ApiView

log = logging.getLogger(__name__)


def get_common_routes(handler: Views, alias_id: str) -> List[RouteDef]:
    p = "/{chat:" + alias_id + "}"
    return [
        web.get(p, handler.index, name=f"index_{alias_id}"),
        web.get(p + r"/logo", handler.logo, name=f"logo_{alias_id}"),
        web.get(p + r"/{id:\d+}/watch", handler.watch, name=f"watch_{alias_id}"),
        web.get(
            p + r"/{id:\d+}/thumbnail",
            handler.thumbnail_get,
            name=f"thumbnail_get_{alias_id}",
        ),
        web.get(
            p + r"/{id:\d+}/{filename}",
            handler.download_get,
            name=f"download_get_{alias_id}",
        ),
        web.head(
            p + r"/{id:\d+}/{filename}",
            handler.download_head,
            name=f"download_head_{alias_id}",
        ),
        # === ROUTE FOR TOKEN-FIRST ExternalPlayer URLs ===
        web.get(
            r"/{token}/{chat:" + alias_id + r"}/{id:\d+}/{filename}",
            handler.download_get,
            name=f"download_token_first_{alias_id}",
        ),
    ] 


async def robots_txt(request):
    """Serve the robots.txt file."""
    robots_path = os.path.join(os.path.dirname(__file__), 'static', 'robots.txt')
    try:
        with open(robots_path, 'r') as f:
            content = f.read()
        return web.Response(text=content, content_type='text/plain')
    except FileNotFoundError:
        return web.Response(text="User-agent: *\nDisallow:", content_type='text/plain')



async def sitemap_xml(request):
    """Generate and serve the sitemap.xml file with pagination and priorities."""
    base_url = request.scheme + "://" + request.host
    views = request.app.get("views")
    
    # Static URLs with priorities
    urls = [
        f"<url><loc>{base_url}/</loc><priority>1.0</priority></url>",  # Home (highest priority)
        f"<url><loc>{base_url}/plycreator</loc><priority>0.8</priority></url>",  # Plycreator Page
        f"<url><loc>{base_url}/contact</loc><priority>0.8</priority></url>",  # Contact Page
    ]

    # Loop through all alias_ids
    for alias_id, chat_info in views.chat_ids.items():
        # Add alias route
        urls.append(f"<url><loc>{base_url}/{alias_id}</loc><priority>0.6</priority></url>")  # Alias route with medium priority
        
        offset_id = 0  # Start fetching from the latest message
        while True:
            # Fetch messages with pagination
            messages = await views.client.get_messages(chat_info["chat_id"], limit=100, offset_id=offset_id)
            if not messages:
                break  # Stop if no more messages
            
            for message in messages:
                if message.file:
                    filename = message.file.name if message.file.name else "Unknown File"
                    file_id = message.id
                    
                    # File URL with just the filename as priority
                    urls.append(
                        f"<url><loc>{base_url}/{alias_id}/{file_id}</loc>"
                        f"<lastmod>{message.date.strftime('%Y-%m-%d')}</lastmod>"
                        f"<priority>0.5</priority></url>"
                    )
                    
                    # View/Download URL with priority
                    urls.append(
                        f"<url><loc>{base_url}/{alias_id}/{file_id}/view</loc>"
                        f"<lastmod>{message.date.strftime('%Y-%m-%d')}</lastmod>"
                        f"<priority>0.5</priority></url>"
                    )
            
            # Update offset_id to fetch the next batch of messages
            offset_id = messages[-1].id

    # Generate sitemap XML structure
    sitemap_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) +
        "\n</urlset>"
    )

    return web.Response(text=sitemap_content, content_type="application/xml")




async def setup_routes(app: web.Application, handler: Views):
    # If handler doesn't already expose ApiView methods, mix them in dynamically
    if not isinstance(handler, ApiView):
        handler.__class__ = type("ViewsWithApi", (handler.__class__, ApiView), {})
        log.debug("Mixed ApiView into Views handler")

    # Attach handler to app for global access (used by sitemap, etc.)
    app["views"] = handler

    client = handler.client
    index_all = index_settings["index_all"]
    index_private = index_settings["index_private"]
    index_group = index_settings["index_group"]
    index_channel = index_settings["index_channel"]
    exclude_chats = index_settings["exclude_chats"]
    include_chats = index_settings["include_chats"]
    routes = [
        web.get("/", handler.home, name="home"),
        web.get("/login", handler.login_get, name="login_page"),
        web.post("/login", handler.login_post, name="login_handle"),
        web.get("/logout", handler.logout_get, name="logout"),
        web.get("/favicon.ico", handler.faviconicon, name="favicon"), 
        web.get("/robots.txt", robots_txt, name="robots_txt"),  # New route for robots.txt
        web.get("/sitemap.xml", sitemap_xml, name="sitemap_xml"),  # New sitemap route
        web.get("/report", handler.video_report, name="video_report"),  # Add the new route here
        web.get("/contact", handler.contact_us, name="contact_us"),
        web.get("/about", handler.about, name="about"),
        web.get(r"/{chat}/{id}/downloadPG", handler.downloadPG, name="download_page"),
        web.get("/search", handler.global_search, name="global_search"),

        # Global chat lock login
        web.get('/chat_lock_login', handler.chat_lock_login_get, name='chat_lock_login'),
        web.post('/chat_lock_login', handler.chat_lock_login_post, name='chat_lock_login_post'),
        web.get('/chat_lock_logout', handler.chat_lock_logout, name='chat_lock_logout'),
        web.get('/{chat}/logout', handler.chat_specific_logout, name='chat_specific_logout'),  # New: Logout from specific chat only
        
        # Global JSON API endpoints
        web.get("/api", handler.root, name="api_root"),
        web.get("/api/chats", handler.chats, name="api_chats"),
        web.get("/api/search", handler.search, name="api_search"),
        web.get("/api/{chat}/items", handler.chat_items, name="api_chat_items"),
        # === NEW ROUTE: Search for specific item across all pages ===
        web.get("/api/{chat}/item", handler.search_item, name="api_search_item"),
    ]

    if index_all:
        # print(await client.get_dialogs())
        # dialogs = await client.get_dialogs()
        # for chat in dialogs:
        async for chat in client.iter_dialogs():
            alias_id = None
            if chat.id in exclude_chats:
                continue

            entity = chat.entity

            if isinstance(entity, User) and not index_private:
                log.debug(f"{chat.title}, private: {index_private}")
                continue
            elif isinstance(entity, Channel) and not index_channel:
                log.debug(f"{chat.title}, channel: {index_channel}")
                continue
            elif isinstance(entity, Chat) and not index_group:
                log.debug(f"{chat.title}, group: {index_group}")
                continue

            alias_id = handler.generate_alias_id(chat)
            routes.extend(get_common_routes(handler, alias_id))
            log.debug(f"Index added for {chat.id} at /{alias_id}")

    else:
        for chat_id in include_chats:
            chat = await client.get_entity(chat_id)
            alias_id = handler.generate_alias_id(chat)
            routes.extend(
                get_common_routes(handler, alias_id)
            )  # returns list() of common routes
            log.debug(f"Index added for {chat.id} at /{alias_id}")
    routes.append(web.view(r"/{wildcard:.*}", handler.wildcard, name="wildcard"))
    app.add_routes(routes)
