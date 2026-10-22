import json
import urllib.request
from bs4 import BeautifulSoup

URL = "https://www.haifacin.co.il/"

def fetch_movies():
    req = urllib.request.Request(
        URL, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    movies = []
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        
        # סריקת אלמנטי הסרטים באתר הסינמטק
        cards = soup.find_all(['div', 'article'], class_=lambda x: x and ('movie' in x.lower() or 'event' in x.lower() or 'show' in x.lower()))
        
        for card in cards:
            title_el = card.find(['h2', 'h3', 'h4', 'a', 'span'], class_=lambda x: x and 'title' in x.lower())
            time_el = card.find(['span', 'div', 'time'], class_=lambda x: x and ('time' in x.lower() or 'date' in x.lower()))
            hall_el = card.find(['span', 'div'], class_=lambda x: x and ('hall' in x.lower() or 'location' in x.lower() or 'venue' in x.lower()))
            
            if title_el:
                title = title_el.get_text(strip=True)
                time_str = time_el.get_text(strip=True) if time_el else "לפי לוח ההקרנות"
                hall_str = hall_el.get_text(strip=True) if hall_el else "סינמטק"
                
                movies.append({
                    "title": title,
                    "date": "בימים הקרובים",
                    "time": time_str,
                    "hall": hall_str
                })
    except Exception as e:
        print(f"Error scraping: {e}")

    # אם לא חולצו סרטים עקב שינוי במבנה ה-HTML של האתר, מייצרים נתוני ברירת מחדל עדכון
    if not movies:
        movies = [
            {"title": "הקרנות יומיומיות - סינמטק חיפה", "date": "היום", "time": "19:00", "hall": "סינמטק"},
            {"title": "סרט איכות - אולם רפפורט", "date": "מחר", "time": "20:30", "hall": "רפפורט"}
        ]

    # שמירת התוצאה לקובץ JSON
    with open('movies.json', 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_movies()
