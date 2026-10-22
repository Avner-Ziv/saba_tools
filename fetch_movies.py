import json
import urllib.request
import re
from datetime import datetime

# פנייה ל-API הנתונים של סינמטק חיפה
API_URL = "https://www.haifacin.co.il/api/events/getEvents"

def get_day_name(date_str):
    days = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return days[dt.weekday()]
    except:
        return ""

def fetch_movies():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json'
    }
    
    movies = []
    
    try:
        req = urllib.request.Request(API_URL, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            events = data if isinstance(data, list) else data.get('events', data.get('data', []))
            
            for item in events:
                title = item.get('title') or item.get('name') or item.get('event_name')
                if not title:
                    continue

                date_raw = item.get('date') or item.get('start_date') or ""
                time_str = item.get('time') or item.get('start_time') or ""
                hall_str = item.get('hall') or item.get('venue') or item.get('location') or "סינמטק"
                description = item.get('short_description') or item.get('description') or item.get('summary') or ""
                
                # ניקוי תגיות HTML מהתיאור
                description = re.sub(r'<[^>]+>', '', description).strip()
                if len(description) > 100:
                    description = description[:97] + "..."

                # הפקת יום בשבוע
                day_name = get_day_name(date_raw) if date_raw else ""
                date_display = f"יום {day_name}, {date_raw}" if day_name else date_raw

                movies.append({
                    "title": title.strip(),
                    "date": date_display if date_display else "בימים הקרובים",
                    "time": time_str if time_str else "לפי לוח ההקרנות",
                    "hall": hall_str,
                    "description": description
                })
    except Exception as e:
        print(f"Direct API Fetching Error: {e}")

    # אם הפנייה ל-API חסומה, מתבצעת סריקה חלופית מדף הבית
    if not movies:
        try:
            req_html = urllib.request.Request("https://www.haifacin.co.il/", headers=headers)
            with urllib.request.urlopen(req_html) as res:
                html = res.read().decode('utf-8')
                # חילוץ נתונים מובנים מקוד המקור של הדף
                matches = re.findall(r'"title":\s*"([^"]+)".*?"date":\s*"([^"]+)".*?"time":\s*"([^"]+)"', html)
                for title, date_str, time_str in matches[:15]:
                    movies.append({
                        "title": title,
                        "date": date_str,
                        "time": time_str,
                        "hall": "סינמטק",
                        "description": ""
                    })
        except Exception as ex:
            print(f"Fallback Error: {ex}")

    with open('movies.json', 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_movies()
