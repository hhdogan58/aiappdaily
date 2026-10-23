import requests
from config import IG_ACCESS_TOKEN, IG_USER_ID

print("Mevcut Ayarlar Kontrol Ediliyor...")
print(f"IG_USER_ID: {IG_USER_ID}")
print(f"Token Başlangıcı: {IG_ACCESS_TOKEN[:15]}...")

url = f"https://graph.instagram.com/v21.0/{IG_USER_ID}"
r = requests.get(url, params={"fields": "username,name", "access_token": IG_ACCESS_TOKEN})

print("\n--- META API YANITI ---")
print(r.json())
