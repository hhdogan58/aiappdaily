import requests
from config import IG_ACCESS_TOKEN, IG_USER_ID

# Son paylaşımından dönen Post ID'yi buraya gir
POST_ID = "17978895702129316" 

base_url = "https://graph.instagram.com" if IG_ACCESS_TOKEN.startswith("IG") else "https://graph.facebook.com"
url = f"{base_url}/v21.0/{POST_ID}"

# 1. Bu gönderinin gerçekten var olup olmadığını kontrol et
r = requests.get(url, params={"fields": "id,media_type,media_url,permalink,caption", "access_token": IG_ACCESS_TOKEN})
print("Gönderi Sorgu Sonucu:")
print(r.json())

# 2. Hesabın yayınlama kotasını kontrol et
quota_url = f"{base_url}/v21.0/{IG_USER_ID}/content_publishing_limit"
r2 = requests.get(quota_url, params={"access_token": IG_ACCESS_TOKEN})
print("\nYayınlama Kotası:")
print(r2.json())

# 3. Son oluşturduğun görsel URL'sinin durumunu kontrol et (ImgBB URL'sini buraya gir)
IMG_URL = "SON_OLUSTURDUGUN_GORSEL_URLSI"
r3 = requests.head(IMG_URL, allow_redirects=True)
print("\nGörsel URL Durumu:")
print("HTTP Kodu:", r3.status_code)
print("Content-Type:", r3.headers.get("Content-Type"))