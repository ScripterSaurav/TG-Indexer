import time
from aiohttp import web
import aiohttp_jinja2
from aiohttp_session import get_session
from .base import BaseView

from app.config import get_chat_password, is_chat_locked

class ChatLockView(BaseView):
    @aiohttp_jinja2.template("chat_lock_login.html")
    async def chat_lock_login_get(self, req: web.Request) -> web.Response:
        """Global chat lock login page"""
        chat_alias = req.query.get('chat_alias', '')
        error = req.query.get('error', '')
        next_path = req.query.get('next_path', '')
        
        # If next_path is homepage, just redirect there immediately
        if next_path == '/':
            return web.HTTPFound('/')
        
        # Get chat info using alias
        chat_name = "This Channel"
        chat_id = None
        
        if chat_alias and chat_alias in self.chat_ids:
            chat_info = self.chat_ids[chat_alias]
            chat_name = chat_info['title']
            chat_id = chat_info['chat_id']
        else:
            # If we can't find the chat, show generic message
            return {
                "chat_id": None,
                "chat_alias": "",
                "chat_name": "Unknown Channel",
                "error": "Channel not found",
                "next_path": next_path,
                "authenticated": req.app["is_authenticated"]
            }
        
        return {
            "chat_id": chat_id,
            "chat_alias": chat_alias,
            "chat_name": chat_name,
            "error": error,
            "next_path": next_path,
            "authenticated": req.app["is_authenticated"]
        }

    async def chat_lock_login_post(self, req: web.Request) -> web.Response:
        """Verify chat-specific password"""
        post_data = await req.post()
        password = post_data.get('password', '')
        chat_alias = post_data.get('chat_alias', '')
        next_path = post_data.get('next_path', '')
        
        if not chat_alias or chat_alias not in self.chat_ids:
            return await self._login_error(req, "Invalid channel", chat_alias, next_path)
        
        chat_info = self.chat_ids[chat_alias]
        chat_id = chat_info['chat_id']
        
        correct_password = get_chat_password(chat_id)
        if not correct_password:
            return await self._login_error(req, "Channel not locked", chat_alias, next_path)
        
        if password == correct_password:
            session = await get_session(req)
            if 'unlocked_chats' not in session:
                session['unlocked_chats'] = {}
            session['unlocked_chats'][str(chat_id)] = time.time()
            
            # FIX: Force session to save changes
            session.changed()
            
            # Redirect to the original requested path, or channel index as fallback
            if next_path:
                return web.HTTPFound(next_path)
            else:
                return web.HTTPFound(f'/{chat_alias}')
        else:
            return await self._login_error(req, "Wrong password", chat_alias, next_path)
    
    async def _login_error(self, req, error, chat_alias=None, next_path=None):
        """Helper for login errors"""
        from aiohttp import web
        
        login_url = req.app.router["chat_lock_login"].url_for()
        query_params = {'error': error}
        if chat_alias:
            query_params['chat_alias'] = chat_alias
        if next_path:
            query_params['next_path'] = next_path
            
        return web.HTTPFound(login_url.with_query(**query_params))
    
    async def chat_lock_logout(self, req: web.Request) -> web.Response:
        """Clear ALL chat lock sessions (global logout)"""
        session = await get_session(req)
        session.pop('unlocked_chats', None)
        
        # FIX: Force session to save changes
        session.changed()
        
        return web.HTTPFound('/')
    
    async def chat_specific_logout(self, req: web.Request) -> web.Response:
        """Logout from specific chat only, keep other chats unlocked"""
        session = await get_session(req)
        
        # Get chat_alias from route parameter
        chat_alias = req.match_info['chat']
        
        # Remove only this specific chat from unlocked_chats
        if chat_alias and chat_alias in self.chat_ids:
            chat_info = self.chat_ids[chat_alias]
            chat_id = str(chat_info['chat_id'])
            
            if 'unlocked_chats' in session and chat_id in session['unlocked_chats']:
                # Create a new dictionary without the chat we're logging out from
                current_unlocked = session.get('unlocked_chats', {})
                updated_unlocked = {k: v for k, v in current_unlocked.items() if k != chat_id}
                
                # Assign the new dictionary back to session
                session['unlocked_chats'] = updated_unlocked
                
                # FIX: Force session to save changes
                session.changed()
        
        # Redirect to homepage after logout
        return web.HTTPFound('/')
