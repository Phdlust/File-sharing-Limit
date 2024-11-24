from bot import Bot
from pyrogram import filters, Client
from config import *
from database.database import *
from helper_func import *
from datetime import datetime
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton 
from pyrogram.enums import ParseMode
import asyncio
import logging
import os
from io import StringIO


# Set up logging
logger = logging.getLogger(__name__)

# Function to delete a message after a specified delay
async def delete_message_after_delay(message: Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")

async def generate_token_stats():
    try:
        # Fetching token statistics from the database
        total_token_count = await phdlust.count_documents({"token_use_count": {"$gt": 0}})

        total_verifications = await phdlust.aggregate([
            {"$group": {"_id": None, "total_verifications": {"$sum": "$token_use_count"}}}
        ]).to_list(None)
        total_verifications_count = total_verifications[0]['total_verifications'] if total_verifications else 0

        last_24_hours = datetime.now() - timedelta(hours=24)
        last_24_hours_data = await phdlust.count_documents({
            "last_token_use_time": {"$gte": last_24_hours}
        })

        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        day_data = await phdlust.count_documents({
            "last_token_use_time": {"$gte": start_of_day}
        })

        # Summary message
        summary_message = (
            "📊 **Token Verification Stats** 📊\n\n"
            f"🔹 Total users who verified tokens: {total_token_count}\n"
            f"🔹 Total tokens verified: {total_verifications_count}\n"
            f"🔹 Tokens in last 24 hours: {last_24_hours_data}\n"
            f"🔹 Token verifications today: {day_data}\n"
        )

        return summary_message
    except Exception as e:
        logging.error(f"Error fetching token statistics: {e}")
        return "An error occurred while fetching token statistics. Please try again later."


# Command to display token statistics
@Client.on_message(filters.command('count') & filters.private)
async def token_stats_command(client: Client, message: Message):
    admin_id = message.from_user.id

    if admin_id not in ADMINS:
        await message.reply_text("❌ You are not authorized to use this command.")
        return

    summary_message = await generate_token_stats()

    # Inline Keyboard with Reset and Close Buttons
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Reset Stats", callback_data="reset_stats")],
        [InlineKeyboardButton("🔒 Close", callback_data="close")]
    ])

    await message.reply_text(summary_message, reply_markup=keyboard)

def is_admin(user_id):
    return user_id in ADMINS

# Command to update variables using the /admin command
@Client.on_message(filters.command("config") & filters.user(ADMINS))
async def admin_command(client, message: Message):
    # Extract the command and arguments
    command_args = message.text.split()
    
    if len(command_args) < 3:
        await message.reply("Usage: /admin variable_name new_value")
        return

    var_name = command_args[1].upper()
    new_value = " ".join(command_args[2:])
    
    if var_name == "TOKEN":
        os.environ["TOKEN"] = new_value
        await message.reply(f"Token updated to: {new_value}")
    
    elif var_name == "SHORTLINK_URL":
        os.environ["SHORTLINK_URL"] = new_value
        await message.reply(f"Shortlink URL updated to: {new_value}")
    
    elif var_name == "SHORTLINK_API":
        os.environ["SHORTLINK_API"] = new_value
        await message.reply(f"Shortlink API updated to: {new_value}")
    
    elif var_name == "TUT_VID":
        os.environ["TUT_VID"] = new_value
        await message.reply(f"Tut Video URL updated to: {new_value}")
    
    else:
        await message.reply("Invalid variable name. Valid options are: TOKEN, SHORTLINK_URL, SHORTLINK_API, TUT_VID")

@Client.on_message(filters.command('creditreport') & filters.private & filters.user(ADMINS))
async def generate_credit_report(client: Client, message: Message):

    try:

        users = await phdlust.find({}, {"_id": 1, "limit": 1}).to_list(length=None)
        

        sorted_users = sorted(users, key=lambda x: x.get("limit", 0), reverse=True)
        top_10_users = sorted_users[:10]


        output = StringIO()
        output.write("User ID, Remaining Credits\n")
        for user in sorted_users:
            output.write(f"{user['_id']}, {user.get('limit', 0)}\n")


        file_path = "/tmp/user_credits_report.txt"
        with open(file_path, "w") as file:
            file.write(output.getvalue())

        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption="📊 Here is the detailed credit report of all users, sorted by remaining credits."
        )


        top_10_summary = "🏆 **Top 10 Users by Credits** 🏆\n\n"
        top_10_summary += "Rank | User ID     | Credits\n"
        top_10_summary += "-----@Ultroid_official------\n"
        
        for idx, user in enumerate(top_10_users, start=1):
            top_10_summary += f"{idx:<4} | {user['_id']:<10} | {user.get('limit', 0):>7}\n"

        await message.reply_text(top_10_summary)


        os.remove(file_path)

    except Exception as e:
        logger.error(f"Error in generating credit report: {e}")
        await message.reply_text("❌ An error occurred while generating the credit report.")



@Client.on_message(filters.command('givecredits') & filters.private)
async def give_credits(client: Client, message: Message):

    admin_id = message.from_user.id

    # Check if the user is an admin
    if admin_id not in ADMINS:
        await message.reply_text("❌ You are not authorized to use this command.")
        return

    # Ensure the command has the correct format
    try:
        command_parts = message.text.split()
        if len(command_parts) != 3:
            await message.reply_text("❌ Invalid command format. Use: /givecredits <user_id> <credits>")
            return

        user_id = int(command_parts[1])
        credits_to_add = int(command_parts[2])


        user_data = await phdlust.find_one({"_id": user_id})
        if not user_data:
            await message.reply_text(f"❌ User with ID {user_id} not found.")
            return

        # Update the user's credit limit
        await phdlust.update_one(
            {"_id": user_id},
            {"$inc": {"limit": credits_to_add}}
        )

        await message.reply_text(f"✅ Successfully added {credits_to_add} credits to user {user_id}.")

    except ValueError:
        await message.reply_text("❌ Invalid user ID or credits value. Please enter valid numbers.")
    except Exception as e:
        logger.error(f"Error while giving credits: {e}")
        await message.reply_text("❌ An error occurred while processing your request. Please try again later.")


@Client.on_message(filters.command('addcredits') & filters.private & filters.user(ADMINS))
async def add_credits(client: Client, message: Message):
    user_id = message.from_user.id

    if len(message.command) != 2:
        await message.reply_text("Usage: /addcredits credits")
        return

    try:
        credits_to_add = int(message.command[1])
        
        if credits_to_add <= 0 or credits_to_add > 20:
            await message.reply_text("You can only add between 1 and 20 credits at a time.")
            return
        
        can_add = await can_increase_credits(user_id, credits_to_add)
        if not can_add:
            await message.reply_text("You've reached the credit increase limit for today (20 credits). Try again later.")
            return

        await increase_user_limit(user_id, credits_to_add)
        await log_token_usage(user_id, credits_to_add)
        await message.reply_text(f"✅ Successfully added {credits_to_add} credits to your account.")

    except ValueError:
        await message.reply_text("Invalid number of credits. Please enter a valid integer.")
    except Exception as e:
        logger.error(f"Error in add_credits: {e}")
        await message.reply_text("An error occurred while adding credits.")


@Client.on_message(filters.command('givepr') & filters.user(ADMINS))
async def give_premium_status(client: Client, message: Message):
    if len(message.command) != 4:
        await message.reply_text("Usage: /givepr user_id credits premium_status")
        return
    
    try:
        user_id = int(message.command[1])
        credits = int(message.command[2])
        premium_status = message.command[3].capitalize()
        
        if premium_status not in ['Bronze', 'Silver', 'Gold']:
            await message.reply_text("Invalid premium status. Choose from Bronze, Silver, Gold.")
            return
        

        premium_credits = PREMIUM_CREDITS
        
        if credits != premium_credits[premium_status]:
            await message.reply_text("Invalid credit amount for the specified premium status.")
            return
        
        await set_premium_status(user_id, premium_status, credits)
        await message.reply_text(f"Assigned {premium_status} status with {credits} credits to user {user_id}.")
        

        try:
            await client.send_message(
                chat_id=user_id,
                text=f"You have been granted {premium_status} status with {credits} credits by an admin."
            )
            logger.info(f"Notified user {user_id} about premium status assignment.")
        except Exception as e:
            logger.warning(f"Could not notify user {user_id}: {e}")
        
    except ValueError:
        await message.reply_text("Invalid arguments. Ensure user_id and credits are integers.")
    except Exception as e:
        logger.error(f"Error in give_premium_status: {e}")
        await message.reply_text("An error occurred while assigning premium status.")


@Client.on_message(filters.command('profile') & filters.private)
async def check_premium_status(client: Client, message: Message):
    user_id = message.from_user.id


    user = await phdlust.find_one({"_id": user_id})

    if user is None:
        await message.reply_text("You are not registered in our database. Please use /start to register.")
        return

    # Check if the user has premium status
    is_premium = user.get("is_premium", False)
    limit = user.get("limit", 0)

    if is_premium:

        premium_status = user.get("premium_status", "Unknown")
        await message.reply_text(
            f"🏆 <b>Premium Status: {premium_status}</b>\n💳 <b>Credits: {limit}</b>",
            parse_mode=ParseMode.HTML
        )
    else:

        await message.reply_text(
            f"You are not a premium user.\n<b>Credits:</b> {limit}\nBecome a Premium user: /plans",
            parse_mode=ParseMode.HTML
        )


    asyncio.create_task(delete_message_after_delay(message, AUTO_DELETE_DELAY))


@Client.on_message(filters.command('check') & filters.private)
async def check_command(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        user = await get_user(user_id)
        user_limit = user.get("limit", START_COMMAND_LIMIT)
        await message.reply_text(f"💳 <b>Your current limit is {user_limit} credits.</b>", parse_mode=ParseMode.HTML)
        asyncio.create_task(delete_message_after_delay(message, AUTO_DELETE_DELAY))
    except Exception as e:
        logger.error(f"Error in check_command: {e}")
        error_message = await message.reply_text("An error occurred while checking your limit.")
        asyncio.create_task(delete_message_after_delay(error_message, AUTO_DELETE_DELAY))

"""
@Client.on_message(filters.command('count') & filters.private)
async def token_stats(client: Client, message: Message):

    admin_id = message.from_user.id

    # Check if the user is an admin
    if admin_id not in ADMINS:  # Make sure ADMINS is a list of your admin user IDs
        await message.reply_text("❌ You are not authorized to use this command.")
        return

    try:

        total_token_count = await phdlust.count_documents({"token_use_count": {"$gt": 0}})


        total_verifications = await phdlust.aggregate([
            {"$group": {"_id": None, "total_verifications": {"$sum": "$token_use_count"}}}
        ]).to_list(None)
        total_verifications_count = total_verifications[0]['total_verifications'] if total_verifications else 0


        last_24_hours = datetime.now() - timedelta(hours=24)
        last_24_hours_data = await phdlust.count_documents({
            "last_token_use_time": {"$gte": last_24_hours}
        })


        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        day_data = await phdlust.count_documents({
            "last_token_use_time": {"$gte": start_of_day}
        })


        summary_message = (
            "📊 **Token Verification Stats** 📊\n\n"
            f"🔹 Total users who verified tokens: {total_token_count}\n"
            f"🔹 Total tokens verified: {total_verifications_count}\n"
            f"🔹 Tokens in last 24 hours: {last_24_hours_data}\n"
            f"🔹 Token verifications today: {day_data}\n"
        )

        # Inline Keyboard with Reset Button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Reset Stats", callback_data="reset_stats")],
            [InlineKeyboardButton("🔒 Close", callback_data="close")]
        ])

        await message.reply_text(summary_message, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error fetching token statistics: {e}")
        await message.reply_text("An error occurred while fetching token statistics. Please try again later.")
"""

@Client.on_message(filters.command('plans') & filters.private)
async def show_plans(client: Client, message: Message):
    plans_text = PAYMENT_TEXT 
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Pay via UPI", callback_data="upi_info")],
            [InlineKeyboardButton("Contact Support", url=f"https://t.me/{OWNER}")],
            [InlineKeyboardButton("🔒 Close", callback_data="close")]
        ]
    )

    await message.reply(plans_text, reply_markup=buttons, parse_mode=ParseMode.HTML)

@Client.on_message(filters.command("admin") & filters.private)
async def admin_panel(client: Client, message: Message):
    admin_id = message.from_user.id

    # Check if the user is an admin
    if admin_id not in ADMINS:
        await message.reply_text("❌ You are not authorized to access the Admin Panel.")
        return

    # Send the Admin Panel
    await message.reply_text(
        text="🔧 Admin Panel 🔧\n\nChoose an action:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔄 Reset Stats", callback_data="reset_stats")],
                [InlineKeyboardButton("📊 count ", callback_data="count_stats")],
                [InlineKeyboardButton("🔒 Close", callback_data="close")]
            ]
        )
    )

@Client.on_message(filters.command('upi') & filters.private)
async def upi_info(client: Client, message: Message):
    try:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=PAYMENT_QR,
            caption=PAYMENT_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Contact Owner", url=f"https://t.me/{OWNER}"),
                        InlineKeyboardButton("🔒 Close", callback_data="close")
                    ]
                ]
            )
        )
    except Exception as e:
        await message.reply_text("Sorry, I couldn't send the UPI information. Please try again later.")
        logger.error(f"Error occurred while sending UPI info: {e}")


@Client.on_message(filters.command('help') & filters.private)
async def help_command(client: Client, message: Message):
    help_text = """
📖 <b>Available Commands:</b>

/start - Start the bot and see welcome message.
/help - Show this help message.
/check - Check your current credit limit.
/profile - Check your premium status and remaining credits.
/batch - Create link for more than one posts.
/genlink - Create link for one post.
/stats - Check your bot uptime.
/users - View bot statistics (Admins only).
/broadcast - Broadcast any messages to bot users (Admins only).
/addcredits credits - Add credits to your account (Admins only).
/givecredits user_id credits - Give credits to a user (Admins only).
/givepr user_id credits premium_status - Give premium status to a user (Admins only).
/count - Show token usage statistics (Admins only).
/creditreport - give txt file and top 10 user (Admins only).
/plans - Show available premium plans.
/upi - Show UPI payment options.
/admin - check or reset count.
"""
    await message.reply(help_text, parse_mode=ParseMode.HTML)

