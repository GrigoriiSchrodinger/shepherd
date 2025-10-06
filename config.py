import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
MPSTATS_API_TOKEN = os.getenv('MPSTATS_API_TOKEN')