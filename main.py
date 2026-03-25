import requests, json, time, urllib.parse, os
from bs4 import BeautifulSoup
import feedparser

# --------------------
# 키워드
# --------------------
TOPICS = {
    "kpop": ["kpop", "idol", "comeback", "debut", "performance"],
    "kdrama": ["kdrama", "netflix", "series", "episode"],
    "kbeauty": ["kbeauty", "skincare", "makeup"],
    "kfood": ["korean food", "kbbq", "kimchi"],
    "korea": ["korea", "seoul", "travel"]
}

TREND_KEYWORDS = [
    "viral", "trending", "insane", "crazy",
    "obsessed", "reaction", "tiktok", "shorts",
    "wtf", "omg", "blowing up"
]

SOURCE_WEIGHT = {
    "reddit": 1.2,
    "youtube": 1.1,
    "twitter": 1.3,
    "social": 1.0
}

# --------------------
# 유틸
# --------------------
def safe_request(url, headers=None):
    try:
        return requests.get(url, headers=headers, timeout=10)
    except:
        return None

# --------------------
# Reddit
# --------------------
def fetch_reddit():
    try:
        url = "https://www.reddit.com/r/all/hot.json?limit=100"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = safe_request(url, headers)

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
# YouTube (안정)
# --------------------
def fetch_youtube():
    try:
        query = urllib.parse.quote("kpop kdrama kbeauty korean")
        url = f"https://www.youtube.com/feeds/videos.xml?search_query={query}"
        feed = feedparser.parse(url)

        return [{
            "source": "youtube",
            "title": e.title,
            "url": e.link,
            "score": 100,
            "created": time.time()
        } for e in feed.entries]
    except:
        return []

# --------------------
# Twitter (Nitter)
# --------------------
def fetch_twitter():
    try:
        base = "https://nitter.net"
        query = urllib.parse.quote("kpop OR kdrama OR kbeauty viral")
        url = f"{base}/search?f=tweets&q={query}"

        res = safe_request(url)
        soup = BeautifulSoup(res.text, "html.parser")

        results = []

        for item in soup.select(".timeline-item"):
            try:
                text = item.select_one(".tweet-content").text.strip()
                link = item.select_one("a")["href"]

                results.append({
                    "source": "twitter",
                    "title": text,
                    "url": base + link,
                    "score": 150,
                    "created": time.time()
                })
            except:
                continue

        return results
    except:
        return []

# --------------------
# Social Searcher (fallback)
# --------------------
def fetch_social_searcher():
    try:
        query = "kpop OR kdrama OR kbeauty"
        url = f"https://www.social-searcher.com/search/?q={query}"

        res = safe_request(url)
        soup = BeautifulSoup(res.text, "html.parser")

        results = []

        for item in soup.select(".search-result"):
            text = item.text.strip()

            results.append({
                "source": "social",
                "title": text[:150],
                "url": url,
                "score": 80,
                "created": time.time()
            })

        return results
    except:
        return []

# --------------------
# 점수 계산
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
    source_score = SOURCE_WEIGHT.get(item["source"], 0.5)

    return (
        popularity * 0.4 +
        trend * 0.4 +
        source_score * 0.2
    )

# --------------------
# 실행
# --------------------
def main():
    print("📡 SNS 풀수집 시작...")

    data = []
    data += fetch_reddit()
    data += fetch_youtube()
    data += fetch_twitter()
    data += fetch_social_searcher()

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

    print("✅ SNS 기반 output.json 생성 완료")

    from newsletter import generate_newsletter
    generate_newsletter()


if __name__ == "__main__":
    main()
