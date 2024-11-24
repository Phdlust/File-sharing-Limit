#ultroidxTeam (admin - TG )
#import logging
import random
import base64
import re
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL2, FORCE_SUB_CHANNEL3, FORCE_SUB_CHANNEL4, ADMINS
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait
from database.database import *

async def is_subscribed(filter, client, update):
    if not (FORCE_SUB_CHANNEL or FORCE_SUB_CHANNEL2 or FORCE_SUB_CHANNEL3 or FORCE_SUB_CHANNEL4):
        return True

    user_id = update.from_user.id

    if user_id in ADMINS:
        return True

    member_status = ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER

    for channel_id in [FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL2, FORCE_SUB_CHANNEL3, FORCE_SUB_CHANNEL4]:
        if not channel_id:
            continue

        try:
            member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
        except UserNotParticipant:
            return False

        if member.status not in member_status:
            return False

    return True

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string

def generate_token(length=10):
    """Generates a random alphanumeric token."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def get_shortlink(url, api, link):
    """Generates a shortened URL using Shortzy."""
    try:
        shortened_link = await shortzy.convert(link)
        return shortened_link
    except Exception as e:
        logger.error(f"Error generating short link: {str(e)}")
        return link  # Fallback to original link if shortening fails

async def notify_user(client, user_id, message):
    """Helper function to send a notification to a user."""
    try:
        await client.send_message(chat_id=user_id, text=message)
        logger.info(f"Notified user {user_id} about premium status assignment.")
    except Exception as e:
        logger.warning(f"Could not notify user {user_id}: {e}")

      


# Increase or decrease user credits
async def increase_user_limit(user_id, increment):
    user_data = await users_collection.find_one({"user_id": user_id})
    if not user_data:
        logger.warning(f"User {user_id} not found in the database.")
        return

    new_limit = user_data.get("credits", 0) + increment
    if new_limit < 0:
        new_limit = 0

    await users_collection.update_one({"user_id": user_id}, {"$set": {"credits": new_limit}})

    logger.info(f"User {user_id}'s credit limit updated to {new_limit}.")
    
# Function to check premium status
def check_premium_status(user_data):
    credits = user_data.get("credits", 0)
    if credits >= PREMIUM_TIERS.get('gold', 0):
        return "gold"
    elif credits >= PREMIUM_TIERS.get('silver', 0):
        return "silver"
    elif credits >= PREMIUM_TIERS.get('bronze', 0):
        return "bronze"
    return "normal"


# Function to auto-remove premium if credits are too low
async def auto_remove_premium(user_id):
    user_data = await users_collection.find_one({"user_id": user_id})
    if user_data.get("is_premium", False) and user_data.get("credits", 0) < 20:
        # Remove premium status
        user_data["is_premium"] = False
        user_data["premium_status"] = "normal"
        await users_collection.update_one({"user_id": user_id}, {"$set": user_data})
        logger.info(f"Removed premium status for user {user_id}.")
        return True
    return False

"""
async def decode(base64_string):
    # Determine if it's a 'limit' link or a regular start link
    if base64_string.startswith("verify_"):
        base64_string = base64_string.replace("verify_", "", 1)  # Remove the 'limit_' prefix

    # Standard base64 decoding process
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("utf-8")

    try:
        string_bytes = base64.urlsafe_b64decode(base64_bytes)
        string = string_bytes.decode("utf-8")  # Decode with utf-8
    except UnicodeDecodeError:
        # Handle decoding errors for any special cases
        string = string_bytes.decode("latin-1")  # Fallback decoding
    
    return string
"""

async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except:
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

subscribed = filters.create(is_subscribed)
