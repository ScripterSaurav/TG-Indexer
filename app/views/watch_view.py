# watch_view.py - Add minimal token support
import logging
from urllib.parse import quote, unquote
import re
import aiohttp_jinja2
from aiohttp import web
from telethon.tl import types
from telethon.tl.custom import Message
from markupsafe import Markup

from app.util import get_file_name, get_human_size
from app.config import block_downloads, token_validation_enabled
from app.token_util import generate_download_token  # Add this import
from .base import BaseView


log = logging.getLogger(__name__)


class WatchView(BaseView):
    @aiohttp_jinja2.template("watch.html")
    async def watch(self, req: web.Request) -> web.Response:
        file_id = int(req.match_info["id"])
        alias_id = req.match_info["chat"]
        chat = self.chat_ids[alias_id]
        chat_id = chat["chat_id"]
        try:
            message = await self.client.get_messages(entity=chat_id, ids=file_id)
        except Exception:
            log.debug(f"Error in getting message {file_id} in {chat_id}", exc_info=True)
            message = None

        if not message or not isinstance(message, Message):
            log.debug(f"no valid entry for {file_id} in {chat_id}")
            return {
                "found": False,
                "reason": "Resource you are looking for cannot be retrieved!",
                "authenticated": req.app["is_authenticated"],
            }

        return_val = {
            "authenticated": req.app["is_authenticated"],
            "source_channel_name": chat["title"],
            "source_channel_logo": f"/{alias_id}/logo",
        }

        reply_btns = []
        if message.reply_markup:
            if isinstance(message.reply_markup, types.ReplyInlineMarkup):
                reply_btns = [
                    [
                        {"url": button.url, "text": button.text}
                        for button in button_row.buttons
                        if isinstance(button, types.KeyboardButtonUrl)
                    ]
                    for button_row in message.reply_markup.rows
                ]

        # === MINIMAL CHANGE: Generate token ===
        token = ""
        if token_validation_enabled:
            token = generate_download_token(chat_id, file_id)
        # === END OF CHANGE ===

        if message.file and not isinstance(message.media, types.MessageMediaWebPage):
            file_name = get_file_name(message)
            
            # extract the file name from the message.
            file_name2 = get_file_name(message)
            # Decodes the Encoded file name, especially if it contains URL-encoded characters (like %20 for spaces).
            file_name2_decoded = unquote(file_name2) 
            
            human_file_size = get_human_size(message.file.size)
            media = {"type": message.file.mime_type}
            if "video/" in message.file.mime_type:
                media["video"] = True
            elif "audio/" in message.file.mime_type:
                media["audio"] = True
            elif "image/" in message.file.mime_type:
                media["image"] = True

            # caption 2- Use message raw_text if available, otherwise fallback to file_name
            caption2 = message.raw_text if message.text else file_name2
            # Escape the caption for safe HTML rendering and replace newlines with <br>
            caption_html2 = Markup.escape(caption2).__str__().replace("\n", "<br>")
            

            # Use message raw_text if available, otherwise fallback to file_name2
            caption3 = message.raw_text if message.text else file_name2
            # Remove common video file extensions (.mp4, .mkv, etc.)
            caption3 = re.sub(r'\.(mp4|mkv|avi|mov|flv|wmv)$', '', caption3, flags=re.IGNORECASE)
            # Escape the caption for safe HTML rendering and replace newlines with <br>
            caption_html3 = Markup.escape(caption3).__str__().replace("\n", "<br>")

            # --------------------------------------
            # CAPTION 4 → remove everything after extension AND remove the extension
            # --------------------------------------
            caption4 = message.raw_text if message.text else file_name2
            # clean italics/bold/underline markdown artifacts
            caption4 = caption4.replace("*", "").replace("_", "").replace("`", "")
            # match everything until the extension
            match_ext4 = re.match(r'^(.*?)(?:\.(mkv|mp4|avi|mov|flv|wmv))\b', caption4, flags=re.IGNORECASE)
            if match_ext4:
               # group(1) = everything BEFORE extension (extension removed)
               caption4 = match_ext4.group(1)
            # final cleanup
            caption4 = caption4.strip().rstrip(".- ")
            caption_html4 = Markup.escape(caption4).__str__().replace("\n", "<br>")

            # caption 3- in this Use truncated caption message text (up to 120 chars) or fallback to file_name
            insight = message.raw_text[:120] if message.text else file_name2
            # Escape the caption for safe HTML rendering and replace newlines with <br>
            insight = Markup.escape(insight).__str__().replace("\n", "<br>") 


            # caption 4- Use message raw_text if available, otherwise fallback to file_name2
            insight2 = message.raw_text if message.text else file_name2
            # URL-encode insight2 (e.g., spaces as %20) for safe URL usage
            encoded_insight2 = quote(insight2)  # Encodes special characters
            # Escape insight2 for safe HTML rendering and replace newlines with <br>
            insight2 = Markup.escape(insight2).__str__().replace("\n", "<br>")


            # caption 1- this caption will display empty not fallback to file_name if Captain not available. which will cause error (original)
            if message.text:
                caption = message.raw_text
            else:
                caption = ""

            caption_html = Markup.escape(caption).__str__().replace("\n", "<br>")

            # === MINIMAL CHANGE: Add tokens to URLs ===
            stream_url = f"/{alias_id}/{file_id}/{encoded_insight2}"
            download_url = "#" if block_downloads else f"/{alias_id}/{file_id}/{file_name}"
            external_player_url = f"/{alias_id}/{file_id}/{encoded_insight2}"  # Default without token
            
            if token_validation_enabled and token:
                stream_url = f"{stream_url}?token={token}"
                external_player_url = f"/{token}/{alias_id}/{file_id}/{encoded_insight2}"  # With token in path
                if not block_downloads:
                    download_url = f"{download_url}?token={token}"
            # === END OF CHANGE ===

            return_val.update(
                {
                    "found": True,
                    "name": unquote(file_name),
                    "name2": file_name2_decoded,
                    "file_id": file_id,
                    "chat_id": chat_id,
                    "human_size": human_file_size,
                    "media": media,
                    "caption_html": caption_html,
                    "caption_html2": caption_html2,
                    "caption_html3": caption_html3,
                    "caption_html4": caption_html4,
                    "insight": insight,
                    "insight2": insight2,
                    "title": f"Watch | {caption_html2} | {human_file_size}",
                    "reply_btns": reply_btns,
                    "thumbnail": f"/{alias_id}/{file_id}/thumbnail",
                    "stream_url": stream_url,  # Now includes token if enabled
                    "external_player_url": external_player_url,  # With token in path
                    "download_url2": f"/{alias_id}/{file_id}/download",
                    "download_url": download_url,  # Now includes token if enabled
                    "page_id": alias_id,
                    "block_downloads": block_downloads,
                }
            )
        elif message.message:
            text = message.raw_text
            text_html = Markup.escape(text).__str__().replace("\n", "<br>")
            return_val.update(
                {
                    "found": True,
                    "media": False,
                    "text_html": text_html,
                    "reply_btns": reply_btns,
                    "page_id": alias_id,
                }
            )
        else:
            return_val.update(
                {
                    "found": False,
                    "reason": "Some kind of resource that I cannot display",
                }
            )

        log.debug(f"data for {file_id} in {chat_id} returned as {return_val}")
        return return_val
