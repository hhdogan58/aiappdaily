"""
Haber için görsel bulucu.
Sıra: arXiv HTML şekilleri → GitHub README görselleri → og:image/twitter:image/sayfa içi.
Hiçbiri bulunamazsa boş liste döner; gorsel_uret.py yedek paneli çizer.
"""
import io
import math
import re
from urllib.parse import urljoin, urlparse

import requests
from PIL import Image

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; appdaily-bot/1.0)"}
RASTER = (".png", ".jpg", ".jpeg", ".webp", ".gif")
KARA_LISTE = ("shields.io", "badge", "logo", "avatar", "favicon", "sponsor", "emoji", "icon",
              "travis-ci", "codecov", "star-history", "githubusercontent.com/u/", "buymeacoffee",
              "visitor", "counter", "ko-fi", "pypi.org", "colab-badge", "/workflows/",
              "gravatar", "wp-content/themes", "/emoji/", "twemoji", "doubleclick",
              "googletagmanager", "google-analytics", "facebook.com/tr", "pixel")
MAX_BOYUT = 15 * 1024 * 1024


def _get(url, **kw):
    try:
        return requests.get(url, headers=HEADERS, timeout=20, **kw)
    except Exception:
        return None


def gorsel_indir(url):
    r = _get(url)
    if r is None or r.status_code != 200 or len(r.content) > MAX_BOYUT:
        return None
    try:
        img = Image.open(io.BytesIO(r.content))
        img.load()
        rgba = img.convert("RGBA")
        zemin = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        return Image.alpha_composite(zemin, rgba).convert("RGB")
    except Exception:
        return None


def kalite_skoru(img):
    """0 = kullanma. Yüksek skor = iyi (büyük, oranı makul, boş/beyaz değil)."""
    w, h = img.size
    if w < 400 or h < 250:
        return 0
    oran = w / h
    if oran < 0.5 or oran > 4:
        return 0
    px = list(img.convert("L").resize((64, 64)).getdata())
    if sum(1 for p in px if p > 245) / len(px) > 0.97:
        return 0
    ort = sum(px) / len(px)
    if (sum((p - ort) ** 2 for p in px) / len(px)) ** 0.5 < 8:
        return 0
    return min(w * h, 2_000_000) * (1 - abs(math.log(oran / 1.7)) * 0.15)


def _en_iyileri(url_listesi, adet, kaynak, limit=12):
    sonuc = []
    gorulen_url = set()
    for u in url_listesi[:limit]:
        if u in gorulen_url:
            continue
        gorulen_url.add(u)
        img = gorsel_indir(u)
        if img is None:
            continue
        skor = kalite_skoru(img)
        if skor > 0:
            sonuc.append((skor, {"img": img, "kaynak": kaynak, "url": u}))
    sonuc.sort(key=lambda x: -x[0])
    return [s[1] for s in sonuc[:adet]]


def gorsel_urlleri(metin, taban):
    ham = re.findall(r'<img[^>]+?(?:src|data-src)=["\']([^"\']+)["\']', metin, flags=re.I)
    ham += re.findall(r'!\[[^\]]*\]\(\s*<?([^)\s>]+)', metin)
    gorulen, sonuc = set(), []
    for s in ham:
        u = urljoin(taban, s.strip())
        dusuk = u.lower()
        if u in gorulen or any(k in dusuk for k in KARA_LISTE):
            continue
        yol = urlparse(dusuk).path
        github_asset = "user-attachments/assets" in dusuk or "user-images.githubusercontent.com" in dusuk
        if not (yol.endswith(RASTER) or github_asset):
            continue
        u = re.sub(r"github\.com/([^/]+/[^/]+)/blob/", r"raw.githubusercontent.com/\1/", u).split("?raw=true")[0]
        gorulen.add(u)
        sonuc.append(u)
    return sonuc


def arxiv_id_bul(*metinler):
    for m in metinler:
        bulunan = re.search(r"(\d{4}\.\d{4,5})(?:v\d+)?", m or "")
        if bulunan:
            return bulunan.group(1)
    return None


def arxiv_sekilleri(arxiv_id, adet=2):
    for taban in (f"https://arxiv.org/html/{arxiv_id}", f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"):
        r = _get(taban)
        if r is None or r.status_code != 200:
            continue
        urller = gorsel_urlleri(r.text, r.url.rstrip("/") + "/")
        bulunan = _en_iyileri(urller, adet, "arXiv")
        if bulunan:
            return bulunan
    return []


def github_repo_bul(arxiv_id):
    r = _get(f"https://huggingface.co/papers/{arxiv_id}")
    if r is None or r.status_code != 200:
        return None
    for sahip, repo in re.findall(r"https?://github\.com/([\w.-]+)/([\w.-]+)", r.text):
        if sahip.lower() in {"huggingface", "features", "sponsors", "apps", "orgs", "login"}:
            continue
        return sahip, re.sub(r"\.git$", "", repo)
    return None


def github_gorselleri(sahip, repo, adet=2):
    for ad in ("README.md", "readme.md", "README.MD"):
        taban = f"https://raw.githubusercontent.com/{sahip}/{repo}/HEAD/"
        r = _get(taban + ad)
        if r is not None and r.status_code == 200:
            return _en_iyileri(gorsel_urlleri(r.text, taban), adet, f"GitHub ({sahip}/{repo})")
    return []


def og_gorsel(url, adet=1):
    r = _get(url)
    if r is None or r.status_code != 200:
        return []

    adaylar = []
    adaylar += re.findall(r'property=["\']og:image(?::url)?["\'][^>]+content=["\']([^"\']+)', r.text, re.I)
    adaylar += re.findall(r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::url)?["\']', r.text, re.I)
    adaylar += re.findall(r'name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)', r.text, re.I)
    adaylar += re.findall(r'content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image(?::src)?["\']', r.text, re.I)
    adaylar += gorsel_urlleri(r.text, url)

    gorulen, temiz = set(), []
    for a in adaylar:
        u = urljoin(url, a.strip())
        if u not in gorulen:
            gorulen.add(u)
            temiz.append(u)

    alan = urlparse(url).netloc.replace("www.", "")
    return _en_iyileri(temiz, adet, alan)


def gorselleri_bul(haber, adet=2):
    """haber: kaynaklar.py'den gelen sözlük. [{img, kaynak, url}, ...] döndürür."""
    bulunan = []
    link = haber.get("link", "")
    aid = arxiv_id_bul(link, str(haber.get("id", "")))

    if aid:
        bulunan += arxiv_sekilleri(aid, adet)
        if len(bulunan) < adet:
            repo = github_repo_bul(aid)
            if repo:
                bulunan += github_gorselleri(*repo, adet=adet - len(bulunan))
        if len(bulunan) < adet:
            bulunan += og_gorsel(f"https://arxiv.org/abs/{aid}", adet=adet - len(bulunan))
    elif link:
        bulunan += og_gorsel(link, adet)

    gorulen_url, temiz = set(), []
    for g in bulunan:
        if g["url"] in gorulen_url:
            continue
        gorulen_url.add(g["url"])
        temiz.append(g)
        if len(temiz) >= adet:
            break

    return temiz
