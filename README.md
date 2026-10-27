# Saba Tools

אפליקציית ווב פשוטה לטלפון. כרגע יש בה מודול אחד: הזמנת כרטיסים לסינמטק חיפה בוואטסאפ.

כתובת: https://avner-ziv.github.io/saba_tools/

## מבנה

```
index.html                      מעטפת האפליקציה וכל העיצוב
core/
  app.js                        ניתוב, טעינת מודולים, הגדרות
  prefs.js                      שמירת העדפות (כרגע בדפדפן; בשלב 1 Firestore)
  settings.js                   מסך הגדרות שנבנה מקבצי schema
  ui.js                         כלים קטנים
  general.schema.json           הגדרות כלליות (שם, גודל טקסט)
modules/
  index.json                    רשימת המודולים הפעילים
  cinema-haifa/
    module.json                 שם, אייקון, קובץ נתונים, הגדרות קבועות (מספר וואטסאפ, אולמות)
    prefs.schema.json           ההגדרות של המשתמש למודול
    view.js                     המסך עצמו ובניית הודעת ההזמנה
scrapers/
  cinema_haifa.py               שולף את לוח ההקרנות לקובץ data/cinema-haifa.json
data/
  cinema-haifa.json             נוצר אוטומטית, לא עורכים ידנית
.github/workflows/update_movies.yml   מריץ את הסורקים פעמיים ביום
```

## העדפות

ההעדפות נשמרות במבנה:

```json
{ "general": { ... }, "modules": { "cinema-haifa": { ... } } }
```

נשמרים רק ערכים שהמשתמש שינה. כל השאר נלקח מברירות המחדל שב-schema. אם הדפדפן נמחק, המשתמש חוזר לברירות המחדל.

סוגי שדות ב-schema: `section`, `text`, `number` (min, max), `choice` (options), `multichoice` (options, minSelected), `boolean`.

## הוספת מודול

1. יוצרים תיקייה `modules/<id>/` עם `module.json`, `prefs.schema.json` ו-`view.js` (הפונקציה `render` מקבלת `data`, `prefs`, `general`, `config`).
2. מוסיפים את `<id>` לרשימה ב-`modules/index.json`.
3. כותבים סורק ב-`scrapers/` שכותב ל-`data/<id>.json`, ונכשל (exit 1) בלי לדרוס את הקובץ אם התוצאה חשודה.
4. ב-workflow מעתיקים את צעד הסורק ומוסיפים אותו לבדיקת הכישלון בסוף.

## אחרי שינוי קוד

מעלים את המספר ב-`core/app.js?v=` שבתחתית `index.html`, כדי שטלפונים לא יטענו גרסה ישנה מהזיכרון.

## כשהרשימה מפסיקה להתעדכן

1. בלשונית Actions: האם הריצה האחרונה נכשלה? הלוג של צעד הסורק מראה קוד HTTP וכמה הקרנות נמצאו.
2. האם התזמון כובה? ב-repo ציבורי GitHub מכבה תזמון אחרי 60 יום בלי פעילות. מפעילים מחדש מעמוד ה-workflow.
3. אם האתר של הסינמטק שינה מבנה, הסורק מחפש `.portfolio-wrapper`, `h3.portfolio-title` ו-`h4.portfolio-details`.
