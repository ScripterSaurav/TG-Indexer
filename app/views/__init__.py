import base64
import hashlib
from typing import Dict, Union

from telethon.tl.types import Chat, User, Channel

from ..config import SHORT_URL_LEN
from ..telegram import Client
from .home_view import HomeView
from .wildcard_view import WildcardView
from .download import Download
from .index_view import IndexView
from .watch_view import WatchView
from .logo_view import LogoView
from .thumbnail_view import ThumbnailView
from .login_view import LoginView
from .logout_view import LogoutView
from .faviconicon_view import FaviconIconView
from .middlewhere import middleware_factory
from .pages_view import ReportView, ContactView, AboutView
from .downloadPG import DownloadPGView
from .chat_lock_view import ChatLockView
from .global_search_view import GlobalSearchView

TELEGRAM_CHAT = Union[Chat, User, Channel]


class Views(
    HomeView,
    Download,
    IndexView,
    WatchView,
    LogoView,
    ThumbnailView,
    WildcardView,
    LoginView,
    LogoutView,
    FaviconIconView,
    DownloadPGView,
    ChatLockView,
    GlobalSearchView,
):
    def __init__(self, client: Client):
        self.client = client
        self.url_len = SHORT_URL_LEN
        self.chat_ids: Dict[str, Dict[str, str]] = {}

    def generate_alias_id(self, chat: TELEGRAM_CHAT) -> str:
        chat_id = chat.id
        title = chat.title

        while True:
            orig_id = f"{chat_id}"  # the original id
            unique_hash = hashlib.md5(orig_id.encode()).digest()
            alias_id = base64.b64encode(unique_hash, b"__").decode()[: self.url_len]

            if alias_id in self.chat_ids:
                self.url_len += (
                    1  # increment url_len just incase the hash is already used.
                )
                continue
            elif (
                self.url_len > SHORT_URL_LEN
            ):  # reset url_len to initial if hash was unique.
                self.url_len = SHORT_URL_LEN

            self.chat_ids[alias_id] = {
                "chat_id": chat_id,
                "alias_id": alias_id,
                "title": title,
            }

            return alias_id
