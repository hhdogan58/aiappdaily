import feedparser
import requests
import re
import base64
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin
from bs4 import BeautifulSoup
from config import PH_TOKEN

HF_DAILY_PAPERS_API = "https://huggingface.co/api/daily_papers"


def _link_normalize(url):
    if not url:
        return ""
    try:
        p = urlparse(url.strip())
        q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith(("utm_", "fbclid", "gclid", "ref", "source", "mc_"))]
        p = p._replace(query=urlencode(q, doseq=True), fragment="")
        return urlunparse(p).rstrip("/")
    except Exception:
        return url.strip()


def _haber_id(entry, link):
    norm = _link_normalize(link)
    if norm:
        return norm
    return _link_normalize(entry.get("id", ""))


def rss_cek(url, kaynak_adi, limit=5):
    feed = feedparser.parse(url)
    sonuc = []
    for e in feed.entries[:limit]:
        link = e.get("link", "")
        sonuc.append({
            "kaynak": kaynak_adi,
            "id": _haber_id(e, link),
            "link": link,
            "baslik": e.title,
            "ozet": e.get("summary", ""),
        })
    return sonuc


def ph_urunleri_cek(limit=5):
    if not PH_TOKEN:
        return []
    sorgu = """query { posts(first: %d, order: VOTES, topic: "artificial-intelligence") { edges { node { id name tagline description url votesCount } } } }""" % limit
    try:
        r = requests.post("https://api.producthunt.com/v2/api/graphql",
                          json={"query": sorgu},
                          headers={"Authorization": f"Bearer {PH_TOKEN}"},
                          timeout=30)
        sonuc = []
        for n in r.json()["data"]["posts"]["edges"]:
            node = n["node"]
            link = node.get("url", "")
            sonuc.append({
                "kaynak": "Product Hunt",
                "id": _link_normalize(link),
                "baslik": node["name"],
                "ozet": node["tagline"],
                "aciklama": node.get("description", ""),
                "link": link,
            })
        return sonuc
    except Exception:
        return []


# ───────────────────── HUGGING FACE ─────────────────────
def hf_gunluk_makaleler(limit=5, sort="trending"):
    try:
        r = requests.get(HF_DAILY_PAPERS_API, params={"limit": limit, "sort": sort}, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[UYARI] HF Daily Papers alınamadı: {e}")
        return []


def hf_makale_haberleri(limit=3):
    makaleler = hf_gunluk_makaleler(limit)
    haberler = []
    for item in makaleler:
        paper = item.get("paper", {})
        arxiv_id = paper.get("id", "")
        if not arxiv_id:
            continue
        thumbnail = item.get("thumbnail") or paper.get("thumbnail")
        haberler.append({
            "kaynak": "Hugging Face Papers",
            "id": f"hf_paper_{arxiv_id}",
            "baslik": paper.get("title", ""),
            "link": f"https://huggingface.co/papers/{arxiv_id}",
            "ozet": paper.get("summary", "")[:800],
            "thumbnail": thumbnail,
            "upvotes": paper.get("upvotes", 0),
            "github_repo": paper.get("githubRepo"),
            "ai_summary": paper.get("ai_summary", ""),
        })
    return haberler


# ───────────────────── GITHUB TRENDING ─────────────────────
def _readme_gorselleri(sahip, repo):
    """GitHub API'sini kullanarak README'deki görselleri bulur (token gerekmez, limit 60/saat)."""
    goruler = []
    # 1. README içeriğini çek
    api_url = f"https://api.github.com/repos/{sahip}/{repo}/readme"
    try:
        r = requests.get(api_url, headers={"Accept": "application/vnd.github.v3+json"}, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        icerik = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
    except Exception:
        return []

    # 2. Markdown ve HTML görsellerini ayıkla
    # Markdown: ![alt](url) / HTML: <img src="url">
    md_imgs = re.findall(r'!\[[^\]]*\]\(\s*<?([^)>\s]+)', icerik)
    html_imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', icerik, re.I)
    ham_urller = md_imgs + html_imgs

    # 3. Göreli URL'leri mutlak yap ve sadece resim uzantılı olanları al
    taban = f"https://raw.githubusercontent.com/{sahip}/{repo}/HEAD/"
    for u in ham_urller:
        mutlak = urljoin(taban, u.strip())
        if not mutlak.lower().split("?")[0].endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            continue
        if mutlak not in goruler:
            goruler.append(mutlak)

    return goruler


def github_trending_repo_cek(limit=5):
    """GitHub Trending (haftalık) sayfasını kazıyarak repo listesi döndürür."""
    try:
        r = requests.get("https://github.com/trending?since=weekly", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        repolar = []
        
        # Her bir repo article.Box-row içinde
        for article in soup.select("article.Box-row")[:limit]:
            # Repo adı (h2 > a)
            h2 = article.select_one("h2 a")
            if not h2:
                continue
            repo_yolu = h2.get("href", "").strip("/")  # örn: "owner/repo"
            
            # Açıklama (p.col-9)
            p = article.select_one("p.col-9")
            aciklama = p.text.strip() if p else ""
            
            # Yıldız sayısı (son sütundaki a)
            yildiz = 0
            stars_tag = article.select("a.Link--muted")
            if stars_tag:
                # Genelde sonuncu Link--muted yıldız sayısıdır
                star_text = stars_tag[-1].text.strip().replace(",", "")
                try:
                    yildiz = int(star_text)
                except ValueError:
                    pass
            
            # README görsellerini çek
            sahip, repo_adi = repo_yolu.split("/")
            gorseller = _readme_gorselleri(sahip, repo_adi)
            
            repolar.append({
                "kaynak": "GitHub Trending",
                "id": f"github_{repo_yolu}",
                "baslik": f"{repo_yolu}: {aciklama[:80]}...",
                "link": f"https://github.com/{repo_yolu}",
                "ozet": aciklama,
                "gorseller": gorseller,  # Carousel için görsel listesi
                "yildiz": yildiz,
            })
        return repolar
    except Exception as e:
        print(f"[HATA] GitHub Trending kazınamadı: {e}")
        return []
