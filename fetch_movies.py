"""
שולף את לוח ההקרנות של סינמטק חיפה ושומר אותו ב-movies.json.

איך זה עובד:
האתר טוען את רשימת ההקרנות מהכתובת /includes/events.php. היא מקבלת תאריך
ומחזירה HTML עם כ-16 ההקרנות הבאות החל מאותו תאריך. הסקריפט מתחיל מהיום,
וכל פעם ממשיך מהתאריך של ההקרנה האחרונה שקיבל, עד שמכסה DAYS_AHEAD ימים.
אחר כך הוא נכנס לעמוד של כל סרט (פעם אחת לכל סרט) ולוקח משם תקציר קצר
ושורת פרטים ("93 דקות, אנגלית, כתוביות בעברית").

אין כאן נתוני דמה. אם נמצאו פחות מ-MIN_SCREENINGS הקרנות, הסקריפט נכשל
ולא נוגע בקובץ הקיים, כדי שהאפליקציה תמשיך להציג את הרשימה האחרונה התקינה.
"""

import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE = "https://www.haifacin.co.il"
EVENTS_URL = BASE + "/includes/events.php"
OUTPUT_FILE = "movies.json"

DAYS_AHEAD = 35        # כמה ימים קדימה לשלוף
MIN_SCREENINGS = 3     # פחות מזה = משהו נשבר, לא דורסים את הקובץ
MAX_REQUESTS = 40      # בלם ביטחון ללולאת התאריכים
SYNOPSIS_MAX = 260     # אורך מקסימלי לתקציר בכרטיס

TZ = ZoneInfo("Asia/Jerusalem")
WEEKDAYS_HE = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]

# "23.10.26 19:15  , סינמטק חיפה"  -> תאריך, שעה, אולם
DETAILS_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})\s+(\d{1,2}):(\d{2})\s*,\s*(.+)")
RUNTIME_RE = re.compile(r"^\d{2,3}\s*דקות")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "he-IL,he;q=0.9",
})


def get(url, params=None):
    """בקשת GET עם שני ניסיונות חוזרים. מדפיס סטטוס ואורך כדי שיהיה קל לאבחן חסימות."""
    last_err = None
    for attempt in range(3):
        try:
            r = session.get(url, params=params, timeout=30)
            print(f"  GET {r.url[:110]} -> {r.status_code}, {len(r.content)} bytes")
            r.raise_for_status()
            r.encoding = "utf-8"
            return r.text
        except requests.RequestException as e:
            last_err = e
            print(f"  attempt {attempt + 1} failed: {e}")
            time.sleep(3 * (attempt + 1))
    raise last_err


def classify_hall(hall_raw):
    """מחזיר מפתח אולם: rappaport / cinematheque / other."""
    if "רפפורט" in hall_raw:
        return "rappaport"
    if "סינמטק" in hall_raw:
        return "cinematheque"
    return "other"


def parse_events_html(html):
    """מפרק HTML של רשימת הקרנות (מדף הבית או מ-events.php) לרשימת מילונים."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for box in soup.select(".portfolio-wrapper"):
        title_el = box.select_one("h3.portfolio-title")
        details_el = box.select_one("h4.portfolio-details")
        if not title_el or not details_el:
            continue

        title = " ".join(title_el.get_text().split())
        details = " ".join(details_el.get_text().split())
        m = DETAILS_RE.search(details)
        if not title or not m:
            print(f"  skipped unparsed item: {title!r} / {details!r}")
            continue

        d, mo, y, hh, mm, hall_raw = m.groups()
        year = int(y) + 2000 if int(y) < 100 else int(y)
        try:
            starts = datetime(year, int(mo), int(d), int(hh), int(mm), tzinfo=TZ)
        except ValueError:
            print(f"  skipped bad date: {details!r}")
            continue

        more = box.select_one("a.ethos-more")
        buy = box.select_one("a.ethos-buy")
        details_url = more["href"] if more and more.has_attr("href") else ""
        buy_url = buy["href"] if buy and buy.has_attr("href") else ""

        ev = re.search(r"/Event/(\d+)", details_url)
        sc = re.search(r"event=(\d+)", buy_url)
        event_id = ev.group(1) if ev else ""
        screening_id = sc.group(1) if sc else f"{event_id}-{starts:%Y%m%d%H%M}"

        hall_raw = hall_raw.strip()
        results.append({
            "id": screening_id,
            "event_id": event_id,
            "title": title,
            "starts_at": starts.isoformat(),
            "date": f"{starts:%d.%m.%Y}",
            "weekday": f"יום {WEEKDAYS_HE[starts.weekday()]}",
            "time": f"{starts:%H:%M}",
            "hall_key": classify_hall(hall_raw),
            "hall_raw": hall_raw,
            "details_url": details_url,
            "buy_url": buy_url,
        })
    return results


def fetch_schedule(today, end_date):
    """עובר על התאריכים מהיום ועד end_date ואוסף את כל ההקרנות."""
    found = {}
    cursor = today
    for _ in range(MAX_REQUESTS):
        if cursor > end_date:
            break
        html = get(EVENTS_URL, params={
            "ajax": 1, "lang": "heb", "date": f"{cursor:%d.%m.%Y}",
            "category": "undefined", "start": 0, "limit": 7, "shownEvents": "",
        })
        batch = parse_events_html(html)
        if not batch:
            break  # אין הקרנות נוספות בהמשך
        for s in batch:
            found.setdefault(s["id"], s)

        last_day = max(datetime.fromisoformat(s["starts_at"]).date() for s in batch)
        # ממשיכים מהיום האחרון שהתקבל (אולי לא כל ההקרנות שלו נכנסו). אם כל
        # התוצאות היו מאותו יום, מתקדמים יום אחד כדי לא להיתקע.
        cursor = last_day if last_day > cursor else cursor + timedelta(days=1)
        time.sleep(0.5)
    return list(found.values())


def fetch_movie_info(details_url):
    """תקציר קצר ושורת פרטים מעמוד הסרט. מחזיר מחרוזות ריקות אם לא נמצא."""
    html = get(details_url)
    soup = BeautifulSoup(html, "html.parser")
    body = soup.select_one('[id$="_ec_body_heb_0"]')
    if not body:
        return "", ""

    paragraphs = [" ".join(p.get_text().split()) for p in body.find_all("p")]
    paragraphs = [p for p in paragraphs if p]

    info = next((p for p in paragraphs if RUNTIME_RE.match(p)), "")
    synopsis = next(
        (p for p in paragraphs
         if len(p) >= 80 and not RUNTIME_RE.match(p) and not p.startswith("כרטיס")),
        "",
    )
    return shorten(synopsis), info


def shorten(text):
    """מקצר טקסט לסוף משפט, לכל היותר SYNOPSIS_MAX תווים."""
    if len(text) <= SYNOPSIS_MAX:
        return text
    cut = text[:SYNOPSIS_MAX]
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    if end > SYNOPSIS_MAX * 0.5:
        return cut[:end + 1]
    return cut[:cut.rfind(" ")] + "…"


def main():
    now = datetime.now(TZ)
    today = now.date()
    end_date = today + timedelta(days=DAYS_AHEAD)
    print(f"Fetching Haifa Cinematheque schedule {today} .. {end_date}")

    try:
        screenings = fetch_schedule(today, end_date)
    except requests.RequestException as e:
        print(f"ERROR: could not reach the site: {e}")
        sys.exit(1)

    # רק הקרנות שעוד לא התחילו ובטווח הזמן, ממוינות לפי מועד
    screenings = [
        s for s in screenings
        if now <= datetime.fromisoformat(s["starts_at"])
        and datetime.fromisoformat(s["starts_at"]).date() <= end_date
    ]
    screenings.sort(key=lambda s: s["starts_at"])
    print(f"Found {len(screenings)} upcoming screenings")

    if len(screenings) < MIN_SCREENINGS:
        print(f"ERROR: fewer than {MIN_SCREENINGS} screenings found. "
              f"Keeping the existing {OUTPUT_FILE} untouched.")
        sys.exit(1)

    # תקציר לכל סרט, פעם אחת לכל event_id
    info_cache = {}
    for s in screenings:
        key = s["event_id"]
        if key not in info_cache:
            try:
                info_cache[key] = fetch_movie_info(s["details_url"]) if s["details_url"] else ("", "")
            except requests.RequestException as e:
                print(f"  no details for {s['title']}: {e}")
                info_cache[key] = ("", "")
            time.sleep(0.3)
        s["synopsis"], s["info"] = info_cache[key]

    data = {
        "updated_at": now.isoformat(timespec="minutes"),
        "source": BASE,
        "screenings": screenings,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    halls = {}
    for s in screenings:
        halls[s["hall_raw"]] = halls.get(s["hall_raw"], 0) + 1
    print(f"Wrote {len(screenings)} screenings to {OUTPUT_FILE}. Halls: {halls}")


if __name__ == "__main__":
    main()
