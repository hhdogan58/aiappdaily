import os
from dotenv import load_dotenv

load_dotenv(override=True)

LLM_URL = os.getenv("LLM_URL", "http://localhost:1235/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-7b-instruct")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "")
PH_TOKEN = os.getenv("PH_TOKEN", "")

# Bot ayarları
ONAY_ISTE = True  # Test için True, tam otomatik için False yap
PAYLASILANLAR_DOSYASI = "paylasilanlar.json"
