import time
import logging
from typing import Coroutine, Union

from aiohttp.web import middleware, HTTPFound, Response, Request
from aiohttp import BasicAuth, hdrs
from aiohttp_session import get_session

# FIXED IMPORT - use app.config instead of .config
from app.config import chat_lock_enabled, is_chat_locked

log = logging.getLogger(__name__)

def _do_basic_auth_check(request: Request) -> Union[None, bool]:
    if "download_" not in request.match_info.route.name:
        return

    auth = None
    auth_header = request.headers.get(hdrs.AUTHORIZATION)
    if auth_header is not None:
        try:
            auth = BasicAuth.decode(auth_header=auth_header)
        except ValueError:
            pass

    if auth is None:
        try:
            auth = BasicAuth.from_url(request.url)
        except ValueError:
            pass

    if not auth:
        return Response(
            body=b"",
            status=401,
            reason="UNAUTHORIZED",
            headers={hdrs.WWW_AUTHENTICATE: 'Basic realm=""'},
        )

    if auth.login is None or auth.password is None:
        return

    if (
        auth.login != request.app["username"]
        or auth.password != request.app["password"]
    ):
        return

    return True

async def _do_cookies_auth_check(request: Request) -> Union[None, bool]:
    session = await get_session(request)
    if not session.get("logged_in", False):
        return

    session["last_at"] = time.time()
    return True

async def _check_chat_lock(request: Request) -> Union[None, bool]:
    """Independent chat lock check - doesn't depend on main auth"""
    if not chat_lock_enabled:
        log.debug("Chat lock not enabled, allowing access")
        return True
        
    chat_alias = request.match_info.get('chat')
    if not chat_alias:
        log.debug("No chat alias in request, allowing access")
        return True
        
    # EXCLUDE LOGO ROUTE from chat lock check
    if request.path.endswith('/logo'):
        log.debug("Logo route accessed, allowing without chat lock check")
        return True
        
    views = request.app.get('views')
    if not views:
        log.debug("No views in app, allowing access")
        return True
        
    if chat_alias not in views.chat_ids:
        log.debug(f"Chat alias {chat_alias} not found in chat_ids, allowing access")
        return True
        
    chat_info = views.chat_ids[chat_alias]
    chat_id = chat_info['chat_id']
    
    log.debug(f"Checking chat lock for chat_id: {chat_id}, alias: {chat_alias}")
    
    # Check if this chat requires separate password
    if not is_chat_locked(chat_id):
        log.debug(f"Chat {chat_id} is not locked, allowing access")
        return True
    
    session = await get_session(request)
    # Check if chat is unlocked in session
    unlocked_chats = session.get('unlocked_chats', {})
    chat_unlock_time = unlocked_chats.get(str(chat_id), 0)
    
    # Check session timeout
    session_timeout = request.app.get("chat_lock_session_lifetime", 30) * 60
    current_time = time.time()
    
    log.debug(f"Session check: unlocked_chats={unlocked_chats}, chat_unlock_time={chat_unlock_time}, current_time={current_time}, timeout={session_timeout}")
    
    if current_time - chat_unlock_time < session_timeout:
        log.debug(f"Chat {chat_id} is unlocked, allowing access")
        return True
    
    # Chat is locked and session expired
    log.debug(f"Chat {chat_id} is LOCKED and requires authentication")
    return False

async def _redirect_to_chat_lock(request: Request) -> Response:
    """Helper to redirect to global chat lock login with original path preserved"""
    chat_alias = request.match_info['chat']
    views = request.app.get('views')
    
    if views and chat_alias in views.chat_ids:
        login_url = request.app.router["chat_lock_login"].url_for()
        
        # Get the full original path including sub-routes
        original_path = request.path  # This gives "/i7s/9/view" or "/i7s/9/downloadPG"
        
        log.debug(f"Redirecting to chat lock login for chat: {chat_alias}, original_path: {original_path}")
        
        redirect_url = login_url.with_query(
            chat_alias=chat_alias,
            next_path=original_path  # Preserve the full original path
        )
        
        log.info(f"Redirecting to chat lock login with preserved path: {original_path}")
        return HTTPFound(redirect_url)
    
    log.warning("Could not find chat info for redirect")
    return HTTPFound('/')

def middleware_factory() -> Coroutine:
    @middleware
    async def factory(request: Request, handler: Coroutine) -> Response:
        log.debug(f"Middleware processing: {request.method} {request.path}")
        
        # First: Handle main site authentication (if enabled)
        if request.app["is_authenticated"] and str(request.rel_url.path) not in [
            "/login",
            "/logout",
            "/favicon.ico",
        ]:
            log.debug("Main auth enabled, checking authentication")
            url = request.app.router["login_page"].url_for()
            if str(request.rel_url) != "/":
                url = url.with_query(redirect_to=str(request.rel_url))

            basic_auth_check_resp = _do_basic_auth_check(request)

            if basic_auth_check_resp is True:
                log.debug("Basic auth passed, checking chat lock")
                # Basic auth passed, now check chat lock
                chat_lock_check = await _check_chat_lock(request)
                if chat_lock_check is False:
                    log.debug("Chat lock failed, redirecting")
                    return await _redirect_to_chat_lock(request)
                log.debug("Both auth and chat lock passed")
                return await handler(request)

            cookies_auth_check_resp = await _do_cookies_auth_check(request)

            if cookies_auth_check_resp is not None:
                log.debug("Cookie auth passed, checking chat lock")
                # Cookie auth passed, now check chat lock
                chat_lock_check = await _check_chat_lock(request)
                if chat_lock_check is False:
                    log.debug("Chat lock failed, redirecting")
                    return await _redirect_to_chat_lock(request)
                log.debug("Both auth and chat lock passed")
                return await handler(request)

            if isinstance(basic_auth_check_resp, Response):
                return basic_auth_check_resp

            return HTTPFound(url)
        
        # Second: Handle chat lock for non-authenticated sites
        # This runs when main site authentication is disabled
        elif not request.app["is_authenticated"]:
            log.debug("Main auth disabled, checking chat lock only")
            chat_lock_check = await _check_chat_lock(request)
            if chat_lock_check is False:
                log.debug("Chat lock failed, redirecting to chat lock login")
                return await _redirect_to_chat_lock(request)
            log.debug("Chat lock passed, allowing access")
        
        log.debug("All checks passed, calling handler")
        return await handler(request)

    return factory
