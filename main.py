import requests, feedparser, json, time, urllib.parse, os
from bs4 import BeautifulSoup
from datetime import datetime

# --------------------
# 설정
# --------------------
TOPICS = {
    "kpop": ["kpop", "bts", "blackpink", "idol"],
    "kdrama": ["kdrama", "korean drama", "netflix"],
    "kfood": ["korean food", "kimchi", "kbbq"],
    "kbeauty": ["kbeauty", "skincare", "cosmetics"],
    "korea": ["korea", "seoul", "k culture"]
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

def is_recent(item, hours=96):
    now = time.time()
    created = item.get("created", now)
    return (now - created) <= hours * 3600

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
# 키워드 점수
# --------------------
def keyword_score(title, keywords):
    title = title.lower()
    return sum(1 for k in keywords if k in title)


def classify(item):
    title = item["title"].lower()

    best_topic = None
    best_score = 0

    for topic, keywords in TOPICS.items():
        score = keyword_score(title, keywords)
        if score > best_score:
            best_topic = topic
            best_score = score

    return best_topic, best_score

# --------------------
# 점수 계산
# --------------------
def calculate_score(item):
    now = time.time()

    created = item.get("created", now)
    freshness = max(0, 1 - (now - created) / 86400)

    popularity = item.get("score", 0) / 1000
    source_score = SOURCE_WEIGHT.get(item["source"], 0.5)

    return (
        popularity * 0.3 +
        freshness * 0.5 +   # 최신성 강화
        source_score * 0.2
    )

# --------------------
# 중복 제거
# --------------------
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

        # 🔥 최신 필터
        if not is_recent(item):
            continue

        # 🔥 Reddit 품질 필터
        if item["source"] == "reddit":
            if item.get("score", 0) < 50:
                continue

        # 🔥 뉴스 품질 필터
        if item["source"] == "news":
            if "blog" in item["url"]:
                continue

        topic, hit = classify(item)

        # 🔥 키워드 최소 조건
        if not topic or hit < 1:
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

    print("✅ output.json 생성 완료")

    # 뉴스레터 생성
    from newsletter import generate_newsletter
    generate_newsletter()

    # 카드뉴스 생성
    from card_news import generate_card_news
    generate_card_news()


if __name__ == "__main__":
    main()
