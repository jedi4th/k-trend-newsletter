import requests, json, time, urllib.parse, os
import feedparser

# --------------------
# 키워드
# --------------------
TOPICS = {
    "kpop": ["kpop", "idol", "comeback"],
    "kdrama": ["kdrama", "netflix", "series"],
    "kbeauty": ["kbeauty", "skincare"],
    "kfood": ["korean food", "kbbq"],
    "korea": ["korea", "seoul"]
}

TREND_KEYWORDS = [
    "viral", "trending", "insane", "crazy",
    "reaction", "tiktok", "shorts"
]

# --------------------
# Reddit API
# --------------------
def fetch_reddit():
    url = "https://www.reddit.com/search.json?q=kpop%20OR%20kdrama%20OR%20kbeauty&limit=50"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()

        return [{
            "source": "reddit",
            "title": p["data"]["title"],
            "url": "https://reddit.com" + p["data"]["permalink"],
            "score": p["data"]["ups"],
            "created": p["data"]["created_utc"]
        } for p in data["data"]["children"]]
    except:
        return []

# --------------------
# YouTube RSS
# --------------------
def fetch_youtube():
    query = urllib.parse.quote("kpop kdrama kbeauty korean")
    url = f"https://www.youtube.com/feeds/videos.xml?search_query={query}"

    feed = feedparser.parse(url)

    return [{
        "source": "youtube",
        "title": e.title,
        "url": e.link,
        "score": 120,
        "created": time.time()
    } for e in feed.entries]

# --------------------
# X (Twitter) RSS via Nitter
# --------------------
def fetch_twitter_rss():
    try:
        query = urllib.parse.quote("kpop OR kdrama OR kbeauty")
        url = f"https://nitter.net/search/rss?f=tweets&q={query}"

        feed = feedparser.parse(url)

        return [{
            "source": "twitter",
            "title": e.title,
            "url": e.link,
            "score": 150,
            "created": time.time()
        } for e in feed.entries]
    except:
        return []

# --------------------
# Google Trends
# --------------------
def fetch_trends():
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    feed = feedparser.parse(url)

    return [{
        "source": "trends",
        "title": e.title,
        "url": e.link,
        "score": 200,
        "created": time.time()
    } for e in feed.entries]

# --------------------
# 점수
# --------------------
def keyword_score(title, keywords):
    title = title.lower()
    return sum(1 for k in keywords if k in title)

def trend_score(title):
    title = title.lower()
    return sum(2 for k in TREND_KEYWORDS if k in title)

def classify(item):
    title = item["title"].lower()

    best_topic = None
    best_score = 0

    for topic, keywords in TOPICS.items():
        score = keyword_score(title, keywords)
        if score > best_score:
            best_topic = topic
            best_score = score

    return best_topic

def calculate_score(item):
    popularity = item.get("score", 100) / 1000
    trend = trend_score(item["title"])

    return popularity * 0.5 + trend * 0.5

# --------------------
# 실행
# --------------------
def main():
    print("📡 SNS 통합 수집 시작...")

    data = []
    data += fetch_reddit()
    data += fetch_youtube()
    data += fetch_twitter_rss()
    data += fetch_trends()

    print(f"수집 완료: {len(data)}개")

    # 중복 제거
    seen = set()
    unique = []

    for i in data:
        if i["url"] not in seen:
            seen.add(i["url"])
            unique.append(i)

    print(f"중복 제거 후: {len(unique)}개")

    result = {}

    for item in unique:
        topic = classify(item)
        if not topic:
            continue

        item["topic"] = topic
        item["final_score"] = calculate_score(item)

        result.setdefault(topic, []).append(item)

    for t in result:
        result[t] = sorted(
            result[t],
            key=lambda x: x["final_score"],
            reverse=True
        )[:5]

    os.makedirs("data", exist_ok=True)

    with open("data/output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("✅ SNS 통합 output.json 생성 완료")

    from newsletter import generate_newsletter
    generate_newsletter()


if __name__ == "__main__":
    main()
