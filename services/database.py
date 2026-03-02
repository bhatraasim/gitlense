from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = AsyncIOMotorClient(settings.MONGODB_URI, tlsAllowInvalidCertificates=True)
db = client[settings.MONGODB_DB_NAME]