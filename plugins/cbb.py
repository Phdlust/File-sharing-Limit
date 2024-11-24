# ultroidofficial : YT

from pyrogram import __version__, Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from bot import Bot
from config import *
from database.database import *
from plugins.cmd import *

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    if data == "about":
        await query.message.edit_text(
            text=f"<b>○ Creator : <a href='tg://user?id={OWNER_ID}'>This Person</a>\n"
                 f"○ Language : <code>Python3</code>\n"
                 f"○ Library : <a href='https://docs.pyrogram.org/'>Pyrogram asyncio {__version__}</a>\n"
                 f"○ Source Code : <a href='https://youtu.be/BeNBEYc-q7Y'>Click here</a>\n"
                 f"○ Channel : @{CHANNEL}\n"
                 f"○ Support Group : @{SUPPORT_GROUP}</b>",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🔒 Close", callback_data="close")
                    ]
                ]
            )
        )
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except Exception as e:
            print(f"Error deleting reply-to message: {e}")

    elif data == "upi_info":
        await upi_info(client, query.message)  # Ensure upi_info is defined

    elif data == "show_plans":
        await show_plans(client, query.message)  # Ensure show_plans is defined

    data = query.data

    if data == "count_stats":  # Handle count stats from callback query
        admin_id = query.from_user.id

        if admin_id not in ADMINS:
            await query.answer("❌ You are not authorized to use this command.", show_alert=True)
            return

        summary_message = await generate_token_stats()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Reset Stats", callback_data="reset_stats")],
            [InlineKeyboardButton("🔒 Close", callback_data="close")]
        ])

        await query.message.edit_text(summary_message, reply_markup=keyboard)

    elif data == "reset_stats":
        # Check if the user is an admin
        admin_id = query.from_user.id
        if admin_id not in ADMINS:
            await query.answer("❌ You are not authorized to perform this action.", show_alert=True)
            return

        try:
            # Reset token stats in the database
            await phdlust.update_many({}, {"$set": {"token_use_count": 0, "last_token_use_time": None}})
            await query.answer("✅ Token statistics have been reset.", show_alert=True)
            await query.message.edit_text("📊 Token statistics have been reset by the admin.")
        except Exception as e:
            print(f"Error resetting token statistics: {e}")
            await query.answer("❌ An error occurred while resetting stats.", show_alert=True)       
        
    
    elif data == "check_tokens":
        user_id = query.from_user.id
        is_admin = user_id in ADMINS


        today_tokens = await get_today_token_count()
        total_tokens = await get_total_token_count()
        user_tokens = await get_user_token_count(user_id)

        if is_admin:

            users = await full_userbase()
            user_token_details = ""
            for user in users[:100]:  # Limit to first 100 users for brevity
                tokens = await get_user_token_count(user)
                user_token_details += f"User ID: {user} - Tokens: {tokens}\n"
            response = (
                f"<b>🔹 Admin Token Statistics 🔹</b>\n\n"
                f"<b>Today's Token Count:</b> {today_tokens}\n"
                f"<b>Total Token Count:</b> {total_tokens}\n\n"
                f"<b>Top Users:</b>\n{user_token_details}"
            )
        else:
            # For regular users
            response = (
                f"<b>📊 Your Token Statistics 📊</b>\n\n"
                f"<b>Today's Token Count:</b> {today_tokens}\n"
                f"<b>Total Token Count:</b> {total_tokens}\n"
                f"<b>Your Token Count:</b> {user_tokens}"
            )

        await query.answer()
        await query.message.edit_text(
            text=response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Close", callback_data="close")]]
            )
        )
