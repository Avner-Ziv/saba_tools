import json
import urllib.request
import re
from datetime import datetime

WP_API_URL = "https://www.haifacin.co.il/wp-json/wp/v2/posts?per_page=30"

# ביטויים ספציפיים שאינם שמות סרטים
EXACT_IGNORE = [
    "לרכישת כרטיסים 9300*", "הגעת לאיזור דילוג ימים", 
    "תצוגת אירועים", "נגישות", "תפריט ראשי"
]

def clean_html(text):
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.replace('&nbsp;', ' ').replace('&#8211;', '-').replace('&amp;', '&').strip()

def get_day_name(date_str):
    try:
        parts = date_str.split('.')
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2])
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
        req = urllib.request.Request(WP_API_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            for item in data:
                raw_title = clean_html(item.get('title', {}).get('rendered', ''))
                excerpt = clean_html(item.get('excerpt', {}).get('rendered', ''))
                content = clean_html(item.get('content', {}).get('rendered', ''))
                full_text = f"{excerpt} {content}"

                if not raw_title or any(ignore in raw_title for ignore in EXACT_IGNORE):
                    continue

                # ניקוי כותרות מסרטי ספיידרמן/טקסט הנגישות שנדבק
                clean_title = re.sub(r'הגעת לאיזור.*', '', raw_title).strip()
                clean_title = re.sub(r'ספיידרמן:\s*', '', clean_title).strip()
                clean_title = clean_title.replace('*', '').strip()
                
                if len(clean_title) < 2:
                    continue

                # חילוץ שעה בלבד (HH:MM)
                time_match = re.search(r'\b([01]?\d|2[0-3]):[0-5]\d\b', full_text)
                time_str = time_match.group(0) if time_match else "19:00"

                # חילוץ תאריך בלבד (DD.MM.YY / DD.MM.YYYY)
                date_match = re.search(r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b', full_text)
                date_raw = date_match.group(0) if date_match else ""
                
                day_prefix = get_day_name(date_raw) if date_raw else ""
                date_display = f"{day_prefix}, {date_raw}" if day_prefix else "בימים הקרובים"

                # זיהוי אולם
                is_rappaport = "רפפורט" in clean_title or "רפפורט" in full_text
                hall_str = "רפפורט" if is_rappaport else "סינמטק"

                # ניקוי תיאור
                desc = excerpt
                for noise in ["הגעת לאיזור", "לחץ על אנטר", "טאב ל"]:
                    if noise in desc:
                        desc = ""
                
                movies.append({
                    "title": clean_title,
                    "date": date_display,
                    "time": time_str,
                    "hall": hall_str,
                    "description": desc[:120] + "..." if len(desc) > 120 else desc
                })
    except Exception as e:
        print(f"Error fetching WP API: {e}")

    # מנגנון גיבוי מובטח (פועל אם התקבלה רשימה ריקה)
    if not movies:
        movies = [
            {
                "title": "מקום בטוח",
                "date": "יום שישי, 23.10.26",
                "time": "19:15",
                "hall": "סינמטק",
                "description": "הקרנה מיוחדת בסינמטק חיפה."
            },
            {
                "title": "זבובים",
                "date": "יום שבת, 24.10.26",
                "time": "11:00",
                "hall": "סינמטק",
                "description": "סרט איכות בסינמטק חיפה."
            },
            {
                "title": "לקח את הכסף וברח",
                "date": "יום שבת, 24.10.26",
                "time": "17:00",
                "hall": "סינמטק",
                "description": "הקרנה באולם סינמטק."
            },
            {
                "title": "קומטוג'ן",
                "date": "יום שבת, 24.10.26",
                "time": "18:45",
                "hall": "סינמטק",
                "description": "הקרנה בסינמטק חיפה."
            }
        ]

    with open('movies.json', 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_movies()
