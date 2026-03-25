import requests, feedparser, json, time, urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime

# --------------------
# 설정
# --------------------
TOPICS = {
    "kpop": ["kpop", "bts", "blackpink", "idol"],
    "kdrama": ["kdrama", "korean drama"],
    "kfood": ["korean food", "kimchi", "kbbq"],
    "kbeauty": ["kbeauty", "skincare"],
    "korea": ["korea", "seoul"]
}

SOURCE_WEIGHT = {
    "reddit": 0.9,
    "youtube": 1.0,
    "news": 1.0,
    "twitter": 0.7
}

# --------------------
# 유틸
# --------------------
def safe_request(url, headers=None):
    try:
        return requests.get(url, headers=headers, timeout=10)
    except:
        return None

def parse_time(ts):
    try:
        return time.mktime(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").timetuple())
    except:
        return time.time()

# --------------------
# 수집
# --------------------
def fetch_reddit():
    url = "https://www.reddit.com/r/all/hot.json?limit=100"
    headers = {"User-Agent": "Mozilla/5.0"}

    res = safe_request(url, headers)
    if not res:
        return []

    data = res.json()
    results = []

    for p in data["data"]["children"]:
        d = p["data"]
        results.append({
            "source": "reddit",
            "title": d["title"],
            "url": "https://reddit.com" + d["permalink"],
            "score": d["ups"],
            "created": d["created_utc"]
        })

    return results


def fetch_youtube():
    query = urllib.parse.quote("kpop OR kdrama OR kbeauty OR korean")
    url = f"https://www.youtube.com/feeds/videos.xml?search_query={query}"

    feed = feedparser.parse(url)
    results = []

    for e in feed.entries:
        results.append({
            "source": "youtube",
            "title": e.title,
            "url": e.link,
            "created": parse_time(e.published)
        })

    return results


def fetch_news():
    query = urllib.parse.quote("kpop OR kdrama OR kbeauty OR korean food")
    url = f"https://news.google.com/rss/search?q={query}"

    feed = feedparser.parse(url)
    results = []

    for e in feed.entries:
        results.append({
            "source": "news",
            "title": e.title,
            "url": e.link,
            "created": parse_time(e.published)
        })

    return results


def fetch_twitter():
    query = urllib.parse.quote("kpop OR kdrama OR kbeauty")

    NITTERS = [
        "https://nitter.net",
        "https://nitter.it",
        "https://nitter.cz"
    ]

    for base in NITTERS:
        url = f"{base}/search?f=tweets&q={query}"
        res = safe_request(url)

        if not res:
            continue

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
                    "created": time.time()
                })
            except:
                continue

        if results:
            return results

    return []


# --------------------
# 처리
# --------------------
def classify(item):
    title = item["title"].lower()

    for topic, keywords in TOPICS.items():
        for k in keywords:
            if k in title:
                return topic
    return None


def calculate_score(item):
    now = time.time()

    # 최신성
    created = item.get("created", now)
    freshness = max(0, 1 - (now - created) / 86400)

    # 인기도
    popularity = item.get("score", 0) / 1000

    # 소스 신뢰도
    source_score = SOURCE_WEIGHT.get(item["source"], 0.5)

    return (
        popularity * 0.4 +
        freshness * 0.3 +
        source_score * 0.3
    )


def deduplicate(items):
    seen = set()
    result = []

    for i in items:
        if i["url"] not in seen:
            seen.add(i["url"])
            result.append(i)

    return result


# --------------------
# 실행
# --------------------
def main():
    print("📡 데이터 수집 시작...")

    data = (
        fetch_reddit() +
        fetch_youtube() +
        fetch_news() +
        fetch_twitter()
    )

    print(f"수집 완료: {len(data)}개")

    data = deduplicate(data)
    print(f"중복 제거 후: {len(data)}개")

    result = {}

    for item in data:
        topic = classify(item)
        if not topic:
            continue

        item["final_score"] = calculate_score(item)
        result.setdefault(topic, []).append(item)

    for t in result:
        result[t] = sorted(
            result[t],
            key=lambda x: x["final_score"],
            reverse=True
        )[:5]

    with open("data/output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("✅ output.json 생성 완료")


if __name__ == "__main__":
    main()