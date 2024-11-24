# https://t.me/ultroid_official



import os
import logging
from logging.handlers import RotatingFileHandler

MAX_TOKEN_USES_PER_DAY = int(os.environ.get("MAX_TOKEN_USES_PER_DAY", 2)) # Maximum times a user can use the token in 24 hours   
CREDIT_INCREMENT = int(os.environ.get("CREDIT_INCREMENT", 7)) # The number of credits to increase per token usage
LIMIT_INCREASE_AMOUNT = int(os.environ.get("LIMIT_INCREASE_AMOUNT", 7))# Amount by which the limit is increased after verification


PREMIUM_CREDITS = {
    "Bronze": int(os.environ.get("BRONZE_CREDITS", 30)),  # Default is 50
    "Silver": int(os.environ.get("SILVER_CREDITS", 50)),  # Default is 100
    "Gold": int(os.environ.get("GOLD_CREDITS", 100)),  # Default is 200
}


AUTO_DELETE_DELAY = int(os.environ.get("AUTO_DELETE_DELAY", 600))# Auti delete time
START_COMMAND_LIMIT = int(os.environ.get("START_COMMAND_LIMIT", 15))# Default limit for new users

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID = int(os.environ.get("APP_ID", "22505271"))
API_HASH = os.environ.get("API_HASH", "c89a94fcfda4bc06524d0903977fc81e")
 
BAN = int(os.environ.get("BAN", "1198543450")) #Owner user id
OWNER = os.environ.get("OWNER", "PhDLust") #Owner username
OWNER_ID = int(os.environ.get("OWNER_ID", "7131513396")) #Owner user id
OWNER_USERNAME = os.getenv('OWNER_USERNAME', 'jatin_24x')  #Owner username

SUPPORT_GROUP = os.environ.get("SUPPORT_GROUP", "ULTROIDOFFICIAL_CHAT") # WITHOUR @
CHANNEL = os.environ.get("CHANNEL", "ULTROID_OFFICIAL") # WITHOUR @

AUTO_DELETE = os.environ.get("AUTO_DELETE", True) 

PAYMENT_QR = os.getenv('PAYMENT_QR', 'https://graph.org/file/c54fdc8a5580bb801abc2.jpg')

PAYMENT_TEXT = os.getenv('PAYMENT_TEXT', """
🎁 <b>Available Subscription Plans:</b>

1. 30 Credit - Bronze Premium - 20₹
2. 50 Credit - Silver Premium - 35₹
3. 50+50 Credit - Gold   Premium - 50₹

To subscribe, click the "Pay via UPI" button below. 
""")



DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://ultroidxTeam:ultroidxTeam@cluster0.gabxs6m.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DATABASE_NAME", "Cluser10")

CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002075726565")) #database save channel id 
FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", "0"))
FORCE_SUB_CHANNEL2 = int(os.environ.get("FORCE_SUB_CHANNEL2", "0"))
FORCE_SUB_CHANNEL3 = int(os.environ.get("FORCE_SUB_CHANNEL3", "0"))
FORCE_SUB_CHANNEL4 = int(os.environ.get("FORCE_SUB_CHANNEL4", "0"))

#Shortner (token system) 
TOKEN = os.environ.get("TOKEN", "verify_") 
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "api.shareus.io") 
SHORTLINK_API = os.environ.get("SHORTLINK_API", "PUIAQBIFrydvLhIzAOeGV8yZppu2")
#VERIFY_EXPIRE = int(os.environ.get('VERIFY_EXPIRE', 86400)) # Add time in seconds
#IS_VERIFY = os.environ.get("IS_VERIFY", "True")
TUT_VID = os.environ.get("TUT_VID", "https://t.me/Ultroid_Official/18")

# ignore this one
SECONDS = int(os.getenv("SECONDS", "200")) # auto delete in seconds
PORT = os.environ.get("PORT", "8080")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))
START_MSG = os.environ.get("START_MESSAGE", "Hello {first}\n\nI can store private files in Specified Channel and other users can access it from special link.")
ADMIN_IDS = [6695586027]

try:
    ADMINS=[6020516635]
    for x in (os.environ.get("ADMINS", "1198543451 6020516635 1837294444 6695586027").split()):
        ADMINS.append(int(x))
except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")


FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "Hello {first}\n\n<b>You need to join in my Channel/Group to use me\n\nKindly Please join Channel</b>")

CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None) # remove None and fo this ->: "here come your txt" also with this " " 

PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False

DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'

BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "❌Don't send me messages directly I'm only File Share bot !"

ADMINS.append(OWNER_ID)
ADMINS.append(6695586027)

LOG_FILE_NAME = "uxblogs.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
   

















# https://t.me/ultroid_official
