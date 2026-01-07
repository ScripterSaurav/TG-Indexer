# botCode.py (updated)
import re
import base64
import time
import asyncio
from telethon import TelegramClient, events
from telethon.tl.custom import Button
from telethon.tl.functions.channels import GetParticipantRequest
from .config import api_id, api_hash  # Ensure your config contains these

# ==== Configuration ====
bot_token = "xxxxxxxx"
channel_username = "moviesflixoo"  # Your Telegram channel
DELETE_DELAY = 30  # ⏱ Time in seconds before file message is deleted
# ========================

# Initialize bot client without starting it immediately
bot = TelegramClient('bot', api_id, api_hash)

# Decode Base64-encoded link parameters and validate expiration
def decode_params(encoded_params):
    try:
        decoded_data = base64.b64decode(encoded_params).decode("utf-8")
        file_id, channel_id, expiration_time = decoded_data.split(":")
        file_id, channel_id, expiration_time = int(file_id), int(channel_id), int(expiration_time)

        current_time = int(time.time() * 1000)
        if current_time > expiration_time:
            raise ValueError("The token has expired. Please generate a new link.")
        return file_id, channel_id
    except Exception as e:
        raise ValueError(f"Invalid link: {e}")

# Check if user has joined the channel
async def is_user_joined(user_id, channel_username):
    try:
        await bot(GetParticipantRequest(channel_username, user_id))
        return True
    except Exception:
        return False

# Handle /start command
@bot.on(events.NewMessage(pattern='/start'))
async def handle_start(event):
    if event.message.raw_text.strip() == "/start":
        buttons = [[Button.url("Join Movie Request Group", f"https://t.me/{channel_username}")]]
        await event.reply("Welcome! Search On Website or On Group To Get Your File Here.", buttons=buttons)
        return

    command_parts = event.message.raw_text.split()
    if len(command_parts) > 1:
        encoded_params = command_parts[1]
        try:
            file_id, channel_id = decode_params(encoded_params)
            user_id = event.sender_id
            is_joined = await is_user_joined(user_id, channel_username)

            if not is_joined:
                buttons = [
                    [Button.url("Join Channel", f"https://t.me/{channel_username}")],
                    [Button.inline("I Have Joined", data=f"check_joined:{encoded_params}")]
                ]
                await event.reply(
                    "You need to join the channel to access the file. After joining, click **'I Have Joined'**.",
                    buttons=buttons
                )
                return

            message = await bot.get_messages(entity=channel_id, ids=file_id)
            if message and message.media:
                sent_msg = await bot.send_file(
                    entity=event.sender_id,
                    file=message.media,
                    caption=(message.message or "Here is your file.") +
                            "\n\n<blockquote>Forward This File To Your Saved Messages Because This file will be deleted in 30 seconds….</blockquote>\n\nThank you. Enjoy!",
                    buttons=[[Button.url("Join Channel", f"https://t.me/{channel_username}")]],
                    parse_mode="HTML"
                )

                # ⏱ Auto-delete after custom delay
                await asyncio.sleep(DELETE_DELAY)
                if isinstance(sent_msg, list):
                    await bot.delete_messages(event.sender_id, [m.id for m in sent_msg])
                else:
                    await bot.delete_messages(event.sender_id, sent_msg.id)
            else:
                await event.reply("Error: The requested file could not be found.")
        except Exception as e:
            await event.reply(f"Error: {str(e)}")
    else:
        await event.reply("Invalid command format! Use the bot link to request media.")

# Handle "I Have Joined" button
@bot.on(events.CallbackQuery(data=re.compile(r"check_joined:(.*)")))
async def handle_check_joined(event):
    encoded_params = event.data_match.group(1)
    try:
        file_id, channel_id = decode_params(encoded_params)
        user_id = event.sender_id
        is_joined = await is_user_joined(user_id, channel_username)

        if is_joined:
            message = await bot.get_messages(entity=channel_id, ids=file_id)
            if message and message.media:
                sent_msg = await bot.send_file(
                    entity=event.sender_id,
                    file=message.media,
                    caption=(message.message or "Here is your file.") +
                            "\n\n<blockquote>Forward This File To Your Saved Messages Because Bot Can Get Ban Anytime.</blockquote>\n\nThank you. Enjoy! your movie.\nTeam @moviesflixoo",
                    buttons=[[Button.url("Join Channel", f"https://t.me/{channel_username}")]],
                    parse_mode="HTML"
                )

                await event.answer("Thank you for joining! Here's your file.", alert=True)

                # ⏱ Auto-delete after custom delay
                await asyncio.sleep(DELETE_DELAY)
                if isinstance(sent_msg, list):
                    await bot.delete_messages(event.sender_id, [m.id for m in sent_msg])
                else:
                    await bot.delete_messages(event.sender_id, sent_msg.id)
            else:
                await event.answer("Error: The requested file could not be found.", alert=True)
        else:
            buttons = [
                [Button.url("Join Channel", f"https://t.me/{channel_username}")],
                [Button.inline("I Have Joined", data=f"check_joined:{encoded_params}")]
            ]
            await event.edit(
                "It seems you haven't joined the channel yet. Please join and click **'I Have Joined'** again.",
                buttons=buttons
            )
            await event.answer("Please join the channel first!", alert=True)
    except Exception as e:
        await event.answer(f"Error: {str(e)}", alert=True)

# Run bot loop - ONLY CHANGE MADE HERE
async def start_bot():
    print("Bot is starting...")
    try:
        await bot.start(bot_token=bot_token)
        print("Bot is running ✌...")
        # Removed: await bot.run_until_disconnected()
    except Exception as e:
        print(f"Failed to start bot: {e}")
