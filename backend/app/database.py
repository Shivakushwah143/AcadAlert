from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "acadalert")

# Create MongoDB client
client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]

# Collections
students_collection = database["students"]
predictions_collection = database["predictions"]
uploads_collection = database["uploads"]

# Function to check database connection
async def check_db_connection():
    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False