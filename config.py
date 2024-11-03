import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ZARINPAL_MERCHANT = os.getenv('ZARINPAL_MERCHANT')
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_IDS = [7158312257]