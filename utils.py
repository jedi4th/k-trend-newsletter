import time
from datetime import datetime

def safe_request(url, headers=None):
    import requests
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res
    except:
        return None
    return None


def parse_time(ts):
    try:
        return time.mktime(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").timetuple())
    except:
        return time.time()