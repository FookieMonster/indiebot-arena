import os

MONGO_DB_URI = os.environ.get("MONGO_DB_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "test_db")
LANGUAGE = "ja"

DEBUG = os.getenv("DEBUG", "False").lower() in ["true", "1", "yes"]
LOCAL_TESTING = os.getenv("LOCAL_TESTING", "False").lower() in ["true", "1", "yes"]

if LOCAL_TESTING:
  MAX_NEW_TOKENS = 20
else:
  MAX_NEW_TOKENS = 512