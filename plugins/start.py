import asyncio
import base64
import logging
import os
import random
import string
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from config import *
#from helper_func import decode, get_messages, get_shortlink , generate_token , notify_user , delete_message_after_delay , increase_user_limit , check_premium_status , auto_remove_premium 
from helper_func import *
from database.database import *
import uuid
from shortzy import Shortzy
import pytz

# Initialize the bot
Bot = Client(
    "PremiumBot",
    api_id=APP_ID,
    api_hash=API_HASH,
    bot_token=TG_BOT_TOKEN
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Shortzy for URL shortening
shortzy = Shortzy(api_key=SHORTLINK_API, base_site=SHORTLINK_URL)

async def get_shortlink(url, api, link):
    try:
        verification_link = await shortzy.convert(link)
        return verification_link
    except Exception as e:
        logger.error(f"Error generating short link: {str(e)}")
        return link

async def delete_message_after_delay(message: Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")


@Client.on_message(filters.command('start') & filters.private  & subscribed)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text

    #user_id = message.from_user.id

    if not await present_user(user_id):
        try:
            await add_user(user_id)
            logger.info(f"Added new user with ID: {user_id}")
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")

    user_data = await phdlust.find_one({"_id": user_id})
    if not user_data:
        try:
            await phdlust.insert_one({
                "_id": user_id,
                "limit": START_COMMAND_LIMIT,
                "previous_token": None,
                "is_premium": False,
                "token_use_count": 0,  # Initialize token use count
                "last_token_use_time": None  # Initialize token use time
            })
            logger.info(f"User {user_id} added to the database.")
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            await message.reply_text("An error occurred while registering you. Please try again later.")
            return


    user_data = await phdlust.find_one({"_id": user_id})
    user_limit = user_data.get("limit", START_COMMAND_LIMIT)
    previous_token = user_data.get("previous_token")
    is_premium = user_data.get("is_premium", False)
    token_use_count = user_data.get("token_use_count", 0)
    last_token_use_time = user_data.get("last_token_use_time", None)


    if not previous_token:
        previous_token = str(uuid.uuid4())
        await phdlust.update_one(
            {"_id": user_id}, {"$set": {"previous_token": previous_token}}, upsert=True
        )


    verification_link = f"https://t.me/{client.username}?start={TOKEN}{previous_token}"
    shortened_link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, verification_link)


    if len(text) > 7 and TOKEN in text:
        provided_token = text.split(TOKEN, 1)[1]
        current_time = datetime.now()

        try:
            if provided_token == previous_token:
                current_time = datetime.now()
                if last_token_use_time:
                    time_diff = current_time - last_token_use_time
                else:
                    time_diff = timedelta(days=1)  # First-time use

                # Reset token usage count after 24 hours
                if time_diff > timedelta(hours=24):
                    token_use_count = 0

                # Check if the user has exceeded the max token usage
                if token_use_count >= MAX_TOKEN_USES_PER_DAY:
                    error_message = await message.reply_text(
                        f"❌ You have already used your verification token {MAX_TOKEN_USES_PER_DAY} times in the past 24 hours. "
                        f"Please try again later or purchase premium for unlimited access."
                    )
                    #asyncio.create_task(delete_message_after_delay(error_message, AUTO_DELETE_DELAY))
                    return


                await phdlust.update_one(
                    {"_id": user_id},
                    {
                        "$inc": {"limit": CREDIT_INCREMENT, "token_use_count": 1},
                        "$set": {"last_token_use_time": current_time}
                    }
                )
                logger.info(f"Token used by user {user_id}. New token use count: {token_use_count + 1}")
                confirmation_message = await message.reply_text(
                    f"✅ Your limit has been successfully increased by {CREDIT_INCREMENT} credits! \n"
                    f"Use /check to view your current limit."
                )
                #asyncio.create_task(delete_message_after_delay(confirmation_message, AUTO_DELETE_DELAY))
                return
            else:
                error_message = await message.reply_text("❌ Invalid verification token. Please try again.")
                #asyncio.create_task(delete_message_after_delay(error_message, AUTO_DELETE_DELAY))
                return

        except Exception as e:
            logger.error(f"Error processing verification token: {e}")
            await message.reply_text("An error occurred. Please try again later.")
            return

    if user_limit <= 0:
        limit_message = (
            "⚠️ Your credit limit has been reached.\n\n"
	    "🎁 Available Subscription Plans: /plans\n\n"
            "Use the following link to increase your limit by 20 credits (limited to two times in 24 hours) , Get Subscription to overcome limit:"
        )
        buttons = [
            [InlineKeyboardButton(text='Increase LIMIT', url=shortened_link)],
            [InlineKeyboardButton('Verification Tutorial', url=TUT_VID)]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(limit_message, reply_markup=reply_markup, protect_content=False, quote=True)
        #if AUTO_DELETE:
	 #   asyncio.create_task(delete_message_after_delay(message, AUTO_DELETE_DELAY))
        return


    await phdlust.update_one({"_id": user_id}, {"$inc": {"limit": -1}})
    #logger.info(f"Deducted 1 credit from user {user_id}. New limit: {user_limit - 1}")

    if is_premium and user_limit - 1 < 20:

        await phdlust.update_one({"_id": user_id}, {"$set": {"is_premium": False}})
        #logger.info(f"Removed premium status for user {user_id} due to low credits.")
        await message.reply("Your premium status has been removed as your credits dropped below 20.")

	
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except IndexError:
            return
        
        string = await decode(base64_string)
        argument = string.split("-")
        
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except Exception as e:
                logger.error(f"Error parsing arguments: {e}")
                return
            
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = list(range(start, end - 1, -1))
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                logger.error(f"Error parsing arguments: {e}")
                return
        
        temp_msg = await message.reply("Please wait...")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("Something went wrong..!")
            logger.error(f"Error getting messages: {e}")
            return
        await temp_msg.delete()
	
        for msg in messages:
            caption = (
                CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html,
                    filename=msg.document.file_name
                )
                if bool(CUSTOM_CAPTION) and bool(msg.document)
                else "" if not msg.caption else msg.caption.html
            )
        
            reply_markup = msg.reply_markup if not DISABLE_CHANNEL_BUTTON else None
        
            try:
                phdlust_send = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                #if AUTO_DELETE:
                asyncio.create_task(delete_message_after_delay(phdlust_send, AUTO_DELETE_DELAY))
                
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                phdlust_send = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                #if AUTO_DELETE:
                asyncio.create_task(delete_message_after_delay(phdlust_send, AUTO_DELETE_DELAY))
            except Exception as e:
                logger.error(f"Error copying message: {e}")
                pass
        return
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("😊 About Me", callback_data="about"),
                    InlineKeyboardButton("🔒 Close", callback_data="close")
                ]
            ]
        )
        welcome_message = await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )
        #asyncio.create_task(delete_message_after_delay(welcome_message, AUTO_DELETE_DELAY))
        return


#=========================================================================================##

WAIT_MSG = """"<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a replay to any telegram message with out any spaces.</code>"""

#=====================================================================================##

    
    
@Client.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton(text="Join Channel", url=client.invitelink),
            InlineKeyboardButton(text="Join Channel", url=client.invitelink2),
        ],
        [
            InlineKeyboardButton(text="Join Channel", url=client.invitelink3),
            #InlineKeyboardButton(text="Join Channel", url=client.invitelink4),
        ]
    ]
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = 'Try Again',
                    url = f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )



@Client.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Client.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()


