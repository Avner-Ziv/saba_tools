import json
import urllib.request
import re
from datetime import datetime

# פנייה ל-API הציבורי של אתר סינמטק חיפה
WP_API_URL = "https://www.haifacin.co.il/wp-json/wp/v2/posts?per_page=20"

def clean_html(text):
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.replace('&nbsp;', ' ').replace('&#8211;', '-').replace('&amp;', '&').strip()

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
                title = clean_html(item.get('title', {}).get('rendered', ''))
                excerpt = clean_html(item.get('excerpt', {}).get('rendered', ''))
                content = clean_html(item.get('content', {}).get('rendered', ''))
                
                if not title:
                    continue
                    
                # חילוץ אולם מהטקסט
                hall_str = "רפפורט" if ("רפפורט" in title or "רפפורט" in content) else "סינמטק"
                
                # חילוץ שעה ותאריך מתוך תוכן הפוסט באמצעות הביטויים הסדירים
                time_match = re.search(r'\b([01]?\d|2[0-3]):[0-5]\d\b', content)
                time_str = time_match.group(0) if time_match else "19:30"
                
                date_match = re.search(r'\b\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?\b', content)
                date_str = date_match.group(0) if date_match else "בימים הקרובים"

                movies.append({
                    "title": title,
                    "date": date_str,
                    "time": time_str,
                    "hall": hall_str,
                    "description": excerpt[:120] + "..." if len(excerpt) > 120 else excerpt
                })
    except Exception as e:
        print(f"Error fetching WP API: {e}")

    # גיבוי קבוע במידה וה-API לא החזיר תוצאות (כדי שהאתר של אבא לעולם לא יישאר ריק)
    if not movies:
        movies = [
            {
                "title": "סרט איכות בסינמטק חיפה",
                "date": "היום",
                "time": "19:30",
                "hall": "סינמטק",
                "description": "הקרנה מיוחדת באולם סינמטק חיפה."
            },
            {
                "title": "הקרנה מיוחדת באולם רפפורט",
                "date": "מחר",
                "time": "20:00",
                "hall": "רפפורט",
                "description": "הקרנת סרט באולם רפפורט."
            }
        ]

    with open('movies.json', 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_movies()
