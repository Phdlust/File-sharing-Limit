# database/database.py

from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI, DB_NAME, START_COMMAND_LIMIT
from datetime import datetime, timedelta
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB Client
mongo_client = AsyncIOMotorClient(DB_URI)
db = mongo_client[DB_NAME]

# Collections
user_collection = db['user_collection']
token_collection = db['tokens']
verification_log_collection = db['verification_logs']

# Default user data structure
default_user = {
    "_id": None,  # User ID
    "limit": START_COMMAND_LIMIT,  # Starting credits
    "is_premium": False,  # Premium status
    "premium_status": None,  # e.g., Silver, Bronze, Gold
    "token_usage": [],  # List of timestamps when tokens were used to increase credits
    "verify_token": "",
    "verified_time": 0
}

async def log_verification(user_id):
    await verification_log_collection.insert_one({
        "user_id": user_id,
        "timestamp": datetime.utcnow()
    })

async def get_verification_count(timeframe):
    current_time = datetime.utcnow()
    
    if timeframe == "24h":
        start_time = current_time - timedelta(hours=24)
    elif timeframe == "today":
        start_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    elif timeframe == "monthly":
        start_time = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        return 0  # Invalid timeframe
    
    count = await verification_log_collection.count_documents({
        "timestamp": {"$gte": start_time, "$lt": current_time}
    })
    
    return count

async def cleanup_old_logs():
    expiry_time = datetime.utcnow() - timedelta(hours=24)
    await verification_log_collection.delete_many({
        "timestamp": {"$lt": expiry_time}
    })

async def get_previous_token(user_id):
    user = await user_collection.find_one({"_id": user_id})
    return user.get("verify_token", None) if user else None

async def set_previous_token(user_id, token):
    await user_collection.update_one({"_id": user_id}, {"$set": {"verify_token": token}})

async def add_user(user_id):
    user = default_user.copy()
    user["_id"] = user_id
    await user_collection.insert_one(user)
    logger.info(f"Added new user with ID: {user_id}")

async def present_user(user_id):
    user = await user_collection.find_one({"_id": user_id})
    return user is not None

async def full_userbase():
    user_docs = user_collection.find()
    user_ids = [doc['_id'] async for doc in user_docs]
    return user_ids

async def del_user(user_id: int):
    await user_collection.delete_one({'_id': user_id})
    logger.info(f"Deleted user with ID: {user_id}")

async def get_user(user_id):
    user = await user_collection.find_one({"_id": user_id})
    if user is None:
        await add_user(user_id)
        user = await user_collection.find_one({"_id": user_id})
    return user

async def update_user(user_id, update_data):
    await user_collection.update_one({"_id": user_id}, {"$set": update_data})
    logger.info(f"Updated user {user_id} with data {update_data}")

async def increase_user_limit(user_id, credits):
    user = await get_user(user_id)
    current_limit = user["limit"]
    new_limit = current_limit + credits
    await user_collection.update_one({"_id": user_id}, {"$set": {"limit": new_limit}})
    logger.info(f"Increased user {user_id} limit by {credits}. New limit: {new_limit}")

async def set_premium_status(user_id, status, credits):
    await user_collection.update_one(
        {"_id": user_id}, 
        {"$set": {"is_premium": True, "premium_status": status, "limit": credits}}
    )
    logger.info(f"Set premium status '{status}' with {credits} credits for user {user_id}")

async def remove_premium_status(user_id):
    await user_collection.update_one(
        {"_id": user_id},
        {"$set": {"is_premium": False, "premium_status": None}}
    )
    logger.info(f"Removed premium status for user {user_id}")

async def get_token_usage(user_id):
    user = await get_user(user_id)
    return user.get("token_usage", [])

async def log_token_usage(user_id):
    current_time = datetime.utcnow()
    await user_collection.update_one(
        {"_id": user_id},
        {"$push": {"token_usage": current_time}}
    )
    logger.info(f"Logged token usage for user {user_id} at {current_time}")

async def can_increase_credits(user_id, credits, time_limit=24):
    user = await get_user(user_id)
    token_usage = user.get("token_usage", [])
    
    # Filter for token usages within the last 24 hours
    recent_usage = [
        usage for usage in token_usage 
        if usage >= datetime.utcnow() - timedelta(hours=time_limit)
    ]
    
    # Calculate total credits used in the last 24 hours
    total_credits_used = len(recent_usage) * 10  # Assuming each token grants 10 credits
    
    if total_credits_used + credits > 20:
        return False
    return True

mongo_client = AsyncIOMotorClient(DB_URI)
db = mongo_client[DB_NAME]

user_collection = db['user_collection']
token_collection = db['tokens']
user_data = db['users']

verification_log_collection = db['verification_logs']

async def log_verification(user_id):
    await verification_log_collection.insert_one({
        "user_id": user_id,
        "timestamp": datetime.utcnow()
    })


async def get_verification_count(timeframe):
    current_time = datetime.utcnow()
    
    if timeframe == "24h":
        start_time = current_time - timedelta(hours=24)
    elif timeframe == "today":
        start_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    elif timeframe == "monthly":
        start_time = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    count = await verification_log_collection.count_documents({
        "timestamp": {"$gte": start_time, "$lt": current_time}
    })
    
    return count

async def cleanup_old_logs():
    expiry_time = datetime.utcnow() - timedelta(hours=24)
    await verification_log_collection.delete_many({
        "timestamp": {"$lt": expiry_time}
    })
    
async def get_previous_token(user_id):
    user_data = await user_collection.find_one({"_id": user_id})
    return user_data.get("previous_token", None)

async def set_previous_token(user_id, token):
    await user_collection.update_one({"_id": user_id}, {"$set": {"previous_token": token}})
    
async def add_user(user_id):
    await user_collection.insert_one({
        "_id": user_id,
        "limit": START_COMMAND_LIMIT
    })
"""
async def present_user(user_id : int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)
    """

async def present_user(user_id):
    user_data = await user_collection.find_one({"_id": user_id})
    return user_data is not None

async def full_userbase():
    user_docs = user_collection.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['_id'])

async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return

async def get_user_limit(user_id):
    user_data = await user_collection.find_one({"_id": user_id})
    if user_data:
        return user_data.get('limit', 0)
    return 0

async def update_user_limit(user_id, new_limit):
    await user_collection.update_one({"_id": user_id}, {"$set": {"limit": new_limit}})

async def store_token(user_id, token):
    await token_collection.insert_one({
        "user_id": user_id,
        "token": token,
        "used": False
    })

async def verify_token(user_id, token):
    token_data = await token_collection.find_one({"user_id": user_id, "token": token, "used": False})
    if token_data:
        await token_collection.update_one({"_id": token_data['_id']}, {"$set": {"used": True}})
        return True
    return False

