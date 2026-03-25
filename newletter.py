import json
from datetime import datetime


def summarize(title):
    return title[:80]


def generate_hook(title, topic):
    title_lower = title.lower()

    if topic == "kpop":
        return f"K-POP 이슈: {title[:40]}"
    elif topic == "kdrama":
        return f"K-DRAMA 화제: {title[:40]}"
    elif topic == "kbeauty":
        return f"K-BEAUTY 트렌드: {title[:40]}"
    elif topic == "kfood":
        return f"K-FOOD 인기: {title[:40]}"
    else:
        return f"KOREA 트렌드: {title[:40]}"


def generate_newsletter():
    with open("data/output.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    today = datetime.now().strftime("%Y-%m-%d")

    content = []
    content.append(f"[K-TREND AI INPUT - {today}]\n")

    for topic, items in data.items():
        content.append(f"\n=== {topic.upper()} ===\n")

        for i, item in enumerate(items, 1):
            title = item["title"]
            url = item["url"]
            source = item["source"]

            summary = summarize(title)
            hook = generate_hook(title, topic)

            content.append(f"{i}.")
            content.append(f"TITLE: {title}")
            content.append(f"SUMMARY: {summary}")
            content.append(f"HOOK: {hook}")
            content.append(f"SOURCE: {source}")
            content.append(f"LINK: {url}\n")

    newsletter_text = "\n".join(content)

    with open("data/newsletter.txt", "w", encoding="utf-8") as f:
        f.write(newsletter_text)

    print("✅ AI용 newsletter.txt 생성 완료")


if __name__ == "__main__":
    generate_newsletter()
