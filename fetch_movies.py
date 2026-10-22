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

        # גלילה למטה 4 פעמים כדי לטעון את כל הסרטים הדינמיים (Infinite Scroll)
        for i in range(4):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)

        # שליפת כל כרטיסי הסרטים
        cards = page.query_selector_all("div, article, a")
        print(f"Found {len(cards)} elements on page. Processing...")
        
        for card in cards:
            text = card.inner_text().strip()
            
            # תבנית תאריך, שעה ואולם
            match = re.search(r'(\d{1,2}:\d{2})\s+(\d{1,2}\.\d{1,2}\.\d{2,4})\s*,\s*([^0-9\n\r]+)', text)
            
            if match:
                time_str = match.group(1)
                date_raw = match.group(2)
                hall_raw = match.group(3).strip()
                
                title_part = text[:match.start()].strip()
                lines = [l.strip() for l in title_part.split('\n') if l.strip()]
                
                if not lines:
                    continue
                
                title = lines[-1]
                title = re.sub(r'[*]', '', title).strip()
                
                if len(title) < 2 or any(ignore in title for ignore in ["הגעת", "דילוג", "אנטר", "נגישות", "תפריט", "כרטיסים"]):
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

    print(f"\nSUCCESS: Extracted {len(movies)} REAL movies from site:")
    for idx, m in enumerate(movies, 1):
        print(f"{idx}. {m['title']} | {m['date']} | {m['time']} | {m['hall']}")

    # שמירה נקייה לחלוטין בלבד - ללא שום נתוני גיבוי!
    with open('movies.json', 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_movies()
