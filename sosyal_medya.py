import requests
import time
from config import IG_ACCESS_TOKEN, IG_USER_ID, IMGBB_API_KEY

API_VER = "v21.0"

def gorsel_yukle(dosya_yolu):
    if not IMGBB_API_KEY: 
        print("[HATA] IMGBB_API_KEY eksik!")
        return None
    try:
        with open(dosya_yolu, "rb") as f:
            r = requests.post("https://api.imgbb.com/1/upload", params={"key": IMGBB_API_KEY}, files={"image": f}, timeout=30)
        return r.json()["data"]["url"]
    except Exception as e:
        print(f"[HATA] ImgBB yükleme hatası: {e}")
        return None

def konteyner_hazir_mi(konteyner_id, bekleme_suresi=60):
    """Instagram'ın görseli işlemesini bekler."""
    base_url = "https://graph.instagram.com" if IG_ACCESS_TOKEN.startswith("IG") else "https://graph.facebook.com"
    bitis = time.time() + bekleme_suresi
    
    while time.time() < bitis:
        r = requests.get(
            f"{base_url}/{API_VER}/{konteyner_id}",
            params={"fields": "status_code", "access_token": IG_ACCESS_TOKEN}
        ).json()
        
        durum = r.get("status_code")
        if durum == "FINISHED":
            return True
        if durum in ["ERROR", "EXPIRED"]:
            print(f"[HATA] Konteyner durumu: {durum} - {r}")
            return False
        time.sleep(3)
    
    print("[HATA] Konteyner zaman aşımına uğradı.")
    return False

def ig_carousel_paylas(image_urls, caption):
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        print("[HATA] Instagram Token veya ID eksik.")
        return False

    base_url = "https://graph.instagram.com" if IG_ACCESS_TOKEN.startswith("IG") else "https://graph.facebook.com"
    url = f"{base_url}/{API_VER}/{IG_USER_ID}"

    # 1. Alt konteynerleri oluştur
    children = []
    print("  -> Alt konteynerler oluşturuluyor...")
    for img_url in image_urls:
        r = requests.post(f"{url}/media", data={"image_url": img_url, "is_carousel_item": "true", "access_token": IG_ACCESS_TOKEN}).json()
        if "id" not in r:
            print(f"  [HATA] Konteyner oluşturulamadı: {r}")
            return False
        children.append(r["id"])
        time.sleep(1)

    # 2. Alt konteynerlerin FINISHED olmasını bekle
    print("  -> Görsellerin işlenmesi bekleniyor...")
    for cid in children:
        if not konteyner_hazir_mi(cid):
            return False

    # 3. Ana Carousel konteyneri
    print("  -> Ana Carousel oluşturuluyor...")
    r = requests.post(f"{url}/media", data={
        "media_type": "CAROUSEL",
        "children": ",".join(children),
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }).json()
    
    if "id" not in r:
        print(f"  [HATA] Ana Carousel oluşturulamadı: {r}")
        return False
        
    ana_konteyner_id = r["id"]
    
    # Ana konteynerin de hazır olmasını bekle
    if not konteyner_hazir_mi(ana_konteyner_id):
        return False
    
    # 4. Yayınla
    print("  -> Yayınlanıyor...")
    r_pub = requests.post(f"{url}/media_publish", data={"creation_id": ana_konteyner_id, "access_token": IG_ACCESS_TOKEN}).json()
    
    if "id" in r_pub:
        print(f"[+] Başarıyla paylaşıldı! Post ID: {r_pub['id']}")
        return True
    else:
        print(f"[HATA] Yayınlanamadı. Meta API Yanıtı: {r_pub}")
        return False
