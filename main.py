import requests
import feedparser
import json
from difflib import SequenceMatcher
import random

# =========================
# 🔑 설정값
# =========================
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"

# =========================
# 📡 1. 유튜브 (조회수 기반)
# =========================
def get_youtube_trends():
    keywords = [
        "kpop", "kdrama", "kbeauty", "korean food",
        "buldak", "tteokbokki", "korean street food"
    ]

    results = []

    for kw in keywords:
        try:
            search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={kw}&type=video&maxResults=5&key={YOUTUBE_API_KEY}"
            res = requests.get(search_url).json()

            for item in res.get("items", []):
                video_id = item["id"]["videoId"]

                stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={YOUTUBE_API_KEY}"
                stats = requests.get(stats_url).json()

                try:
                    view_count = int(stats["items"][0]["statistics"]["viewCount"])
                except:
                    view_count = 0

                if view_count > 30000:
                    results.append({
                        "title": item["snippet"]["title"],
                        "summary": f"YouTube 조회수 {view_count}",
                        "link": f"https://youtube.com/watch?v={video_id}",
                        "source": "youtube"
                    })
        except:
            continue

    return results

# =========================
# 📡 2. TikTok 우회 (Google Trends + 키워드)
# =========================
def get_trend_keywords():
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    feed = feedparser.parse(url)

    results = []
    for entry in feed.entries[:10]:
        results.append({
            "title": entry.title,
            "summary": "Google Trends",
            "link": entry.link,
            "source": "trends"
        })
    return results

# =========================
# 📡 3. 뉴스
# =========================
def get_news():
    url = "https://news.google.com/rss/search?q=kpop+kdrama+kbeauty+korean+food&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)

    results = []
    for entry in feed.entries[:20]:
        results.append({
            "title": entry.title,
            "summary": entry.summary,
            "link": entry.link,
            "source": "news"
        })
    return results

# =========================
# 🧠 중복 제거
# =========================
def is_similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.75

def deduplicate(news):
    unique = []
    for item in news:
        if not any(is_similar(item["title"], u["title"]) for u in unique):
            unique.append(item)
    return unique

# =========================
# 🔥 바이럴 필터
# =========================
VIRAL_KEYWORDS = [
    "viral", "trend", "tiktok", "buzz", "hot", "challenge"
]

def viral_score(text):
    text = text.lower()
    return sum(1 for k in VIRAL_KEYWORDS if k in text)

def filter_news(news):
    filtered = []
    for item in news:
        score = viral_score(item["title"] + " " + item["summary"])

        # YouTube는 조회수로 이미 필터됨 → 통과
        if item["source"] == "youtube":
            filtered.append(item)
        elif score >= 1:
            filtered.append(item)

    return filtered

# =========================
# 📊 카테고리 분류
# =========================
CATEGORY_KEYWORDS = {
    "KPOP": ["kpop", "idol", "bts", "blackpink"],
    "KDRAMA": ["drama", "netflix", "series"],
    "KBEAUTY": ["beauty", "skincare", "makeup"],
    "KFOOD": ["food", "ramen", "buldak", "tteokbokki", "korean bbq"],
    "KOREA": ["korea", "korean"]
}

def categorize(news):
    categorized = {k: [] for k in CATEGORY_KEYWORDS.keys()}

    for item in news:
        text = (item["title"] + " " + item["summary"]).lower()

        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(k in text for k in keywords):
                categorized[cat].append(item)
                break

    return categorized

# =========================
# 💾 저장
# =========================
def save_output(data):
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ output.json 생성 완료")

# =========================
# 🧠 뉴스레터 텍스트
# =========================
def generate_newsletter(data):
    text = "[K-TREND AI INPUT]\n\n"

    for category, items in data.items():
        if not items:
            continue

        text += f"=== {category} ===\n\n"

        for i, item in enumerate(items[:5], 1):
            text += f"{i}.\n"
            text += f"TITLE: {item['title']}\n"
            text += f"SUMMARY: {item['summary']}\n"
            text += f"LINK: {item['link']}\n\n"

    with open("newsletter.txt", "w", encoding="utf-8") as f:
        f.write(text)

    print("✅ newsletter.txt 생성 완료")

# =========================
# 🚀 메인 실행
# =========================
def main():
    print("📡 트렌드 수집 시작...")

    youtube = get_youtube_trends()
    trends = get_trend_keywords()
    news = get_news()

    all_data = youtube + trends + news

    print(f"수집: {len(all_data)}")

    all_data = deduplicate(all_data)
    print(f"중복 제거: {len(all_data)}")

    all_data = filter_news(all_data)
    print(f"필터링: {len(all_data)}")

    categorized = categorize(all_data)

    save_output(categorized)
    generate_newsletter(categorized)


if __name__ == "__main__":
    main()
