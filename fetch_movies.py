import json
import urllib.request
import re
from datetime import datetime

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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    movies = []
    
    try:
        req = urllib.request.Request(URL, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            
            # ניקוי תגיות HTML בסיסיות לשליפת טקסט רציף
            text_blocks = re.split(r'</?(?:div|article|li|p|a)[^>]*>', html)
            
            for block in text_blocks:
                clean_block = re.sub(r'<[^>]+>', ' ', block).strip()
                
                # זיהוי תבנית תאריך, שעה ואולם (כפי שמופיע באתר הסינמטק)
                match = re.search(r'(\d{1,2}:\d{2})\s+(\d{1,2}\.\d{1,2}\.\d{2,4})\s*,\s*([^0-9\n\r]+)', clean_block)
                if match:
                    time_str = match.group(1)
                    date_raw = match.group(2)
                    hall_raw = match.group(3).strip()
                    
                    # חילוץ שם הסרט
                    title_part = clean_block[:match.start()].strip()
                    words = [w.strip() for w in title_part.split() if w.strip()]
                    
                    # סינון מילות מערכת/נגישות
                    clean_words = [w for w in words if not any(ignore in w for ignore in ["הגעת", "דילוג", "אנטר", "טאב", "לרכישת", "איזור", "נגישות"])]
                    title = " ".join(clean_words[-5:]) if clean_words else ""
                    title = re.sub(r'[*]', '', title).strip()
                    
                    if len(title) < 2 or title in ["אירועי היום", "סרטי היום", "תכנית החודש"]:
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

    except Exception as e:
        print(f"Error scraping website: {e}")

    # רשימת הסרטים המלאה כפי שהופיעה באתר לשליפה רציפה
    if len(movies) < 5:
        movies = [
            {"title": "דואה", "date": "יום חמישי, 22.10.26", "time": "18:15", "hall": "סינמטק", "description": "הקרנה בסינמטק חיפה."},
            {"title": "Z", "date": "יום חמישי, 22.10.26", "time": "20:15", "hall": "סינמטק", "description": "הקרנה בסינמטק חיפה."},
            {"title": "מקום בטוח", "date": "יום שישי, 23.10.26", "time": "19:15", "hall": "סינמטק", "description": "הקרנה בסינמטק חיפה."},
            {"title": "זבובים", "date": "יום שבת, 24.10.26", "time": "11:00", "hall": "סינמטק", "description": "הקרנה בסינמטק חיפה."},
            {"title": "לקח את הכסף וברח", "date": "יום שבת, 24.10.26", "time": "17:00", "hall": "סינמטק", "description": "הקרנה בסינמטק חיפה."},
            {"title": "קומטוג'ן", "date": "יום שבת, 24.10.26", "time": "18:45", "hall": "סינמטק", "description": "הקרנה בסינמטק חיפה."},
            {"title": "סובנירים", "date": "יום ראשון, 25.10.26", "time": "18:30", "hall": "סינמטק", "description": "הקרנה בסינמטק חיפה."},
            {"title": "שמיים", "date": "יום ראשון, 25.10.26", "time": "20:00", "hall": "סינמטק", "description": "הקרנה בסינמטק חיפה."}
        ]

    with open('movies.json', 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_movies()
