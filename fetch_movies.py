import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

URL = "https://www.haifacin.co.il/"

def get_day_name(date_str):
    try:
        parts = date_str.split('.')
        day, month = int(parts[0]), int(parts[1])
        year = int(parts[2]) if len(parts) > 2 else 2026
        if year < 100:
            year += 2000
        dt = datetime(year, month, day)
        days_hebrew = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
        return f"יום {days_hebrew[dt.weekday()]}"
    except:
        return ""

def fetch_movies():
    movies = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Opening Haifa Cinematheque website...")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        # גלילה למטה לטעינת כל הסרטים
        for i in range(4):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)

        # שליפת כל הכרטיסיות
        cards = page.query_selector_all("div, article, a")
        print(f"Total candidate elements found: {len(cards)}")
        
        for card in cards:
            raw_text = card.inner_text().strip()
            # איחוד ירידות שורה ורווחים מיותרים
            normalized_text = " ".join(raw_text.split())
            
            # ביטוי סדיר גמיש לזיהוי: HH:MM DD.MM.YY , אולם
            match = re.search(r'(\d{1,2}:\d{2})\s+(\d{1,2}\.\d{1,2}\.\d{2,4})\s*,\s*([^0-9]+)', normalized_text)
            
            if match:
                time_str = match.group(1)
                date_raw = match.group(2)
                hall_raw = match.group(3).strip()
                
                # חילוץ שם הסרט המופיע לפני התאריך
                title_part = normalized_text[:match.start()].strip()
                lines = [l.strip() for l in title_part.split() if l.strip()]
                
                if not lines:
                    continue
                
                # לקחת את שם הסרט הנקי (עד 6 מילים)
                title = " ".join(lines[-6:])
                title = re.sub(r'[*]', '', title).strip()
                
                # סינון כותרות נגישות ומערכת
                if len(title) < 2 or any(ignore in title for ignore in ["הגעת", "דילוג", "אנטר", "נגישות", "תפריט", "כרטיסים", "אירועי", "סרטי"]):
                    continue

                day_prefix = get_day_name(date_raw)
                date_display = f"{day_prefix}, {date_raw}" if day_prefix else date_raw
                hall_str = "רפפורט" if "רפפורט" in hall_raw or "רפפורט" in title else "סינמטק"

                if not any(m['title'] == title and m['time'] == time_str and m['date'] == date_display for m in movies):
                    movies.append({
                        "title": title,
                        "date": date_display,
                        "time": time_str,
                        "hall": hall_str,
                        "description": f"הקרנה באולם {hall_str}."
                    })

        browser.close()

    print(f"\n==========================================")
    print(f"SUCCESS: Extracted {len(movies)} REAL movies:")
    for idx, m in enumerate(movies, 1):
        print(f"{idx}. {m['title']} | {m['date']} | {m['time']} | {m['hall']}")
    print(f"==========================================\n")

    # שמירת נתוני האמת בלבד
    with open('movies.json', 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_movies()
