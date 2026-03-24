from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    TOKEN = os.getenv('BOT_TOKEN')
    DATABASE_URL = os.getenv('DATABASE_URL')
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'notes')
    ADMIN_CHANNEL_ID = int(os.getenv('ADMIN_CHANNEL_ID', '0'))
    ADMIN_IDS = [
        int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()
    ]


config = Config()
