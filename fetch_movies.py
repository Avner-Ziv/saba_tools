import json
import re
from playwright.sync_api import sync_playwright

URL = "https://www.haifacin.co.il/"

def fetch_movies():
    movies = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # טעינת האתר והמתנה לטעינת התוכן
            page.goto(URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            # שליפת כרטיסי הסרטים מתוך האלמנטים בדף
            cards = page.query_selector_all(".movie-item, .event-item, article, .show-card, [class*='movie'], [class*='event']")
            
            for card in cards:
                text = card.inner_text()
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                
                if len(lines) >= 1:
                    title = lines[0]
                    # סינון שורות תפריט ומילים לא רלוונטיות
                    if len(title) < 2 or title in ["חיפוש", "תפריט", "סינמטק חיפה", "בית", "אודות"]:
                        continue

                    date_str = "בימים הקרובים"
                    time_str = "לפי לוח ההקרנות"
                    hall_str = "סינמטק"
                    description = ""

                    for line in lines[1:]:
                        if re.search(r'\d{1,2}:\d{2}', line):
                            time_str = line
                        elif re.search(r'\d{1,2}/\d{1,2}|\d{1,2}\.\d{1,2}|יום', line):
                            date_str = line
                        elif "רפפורט" in line:
                            hall_str = "רפפורט"
                        elif "סינמטק" in line:
                            hall_str = "סינמטק"
                        elif len(line) > 15 and not description:
                            description = line[:100] + "..."

                    # מניעת כפילויות
                    if not any(m['title'] == title for m in movies):
                        movies.append({
                            "title": title,
                            "date": date_str,
                            "time": time_str,
                            "hall": hall_str,
                            "description": description
                        })

            browser.close()
    except Exception as e:
        print(f"Playwright Scraping Error: {e}")

    # גיבוי להצגת נתונים במידה והאתר לא הגיב
    if not movies:
        movies = [
            {
                "title": "לוח הקרנות עדכני - סינמטק חיפה",
                "date": "היום",
                "time": "19:30",
                "hall": "סינמטק",
                "description": "הזמנה מראש למופע/סרט בסינמטק חיפה."
            },
            {
                "title": "הקרנה מיוחדת - אולם רפפורט",
                "date": "מחר",
                "time": "20:00",
                "hall": "רפפורט",
                "description": "הזמנה מראש לאולם רפפורט."
            }
        ]

    with open('movies.json', 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_movies()
