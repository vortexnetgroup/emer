import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")