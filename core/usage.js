// דיווח שימוש: פעם אחת ביום לכל מכשיר, לגיליון Google של מנהל האפליקציה.
//
// נשלחים: מזהה אקראי של המכשיר, השם שהמשתמש הגדיר (אם הגדיר) וסוג המכשיר.
// לא נשלחים מייל, מספר טלפון או מיקום.
// הכתובת נקבעת ב-core/config.json. אם היא ריקה, לא נשלח כלום.
// כל תקלה כאן נבלעת בשקט: הדיווח אף פעם לא מפריע לשימוש באפליקציה.

const ID_KEY = "saba_device_id";
const DAY_KEY = "saba_last_report";

// force: לשלוח גם אם כבר דווח היום (למשל כשהמשתמש הגדיר שם חדש)
export function reportUsage(url, name, { force = false } = {}) {
  if (!url) return;
  try {
    let id = localStorage.getItem(ID_KEY);
    if (!id) {
      id = newId();
      localStorage.setItem(ID_KEY, id);
    }

    const today = new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Jerusalem" });
    if (!force && localStorage.getItem(DAY_KEY) === today) return;

    fetch(url, {
      method: "POST",
      mode: "no-cors",                       // התשובה לא נקראת, רק נשלחת
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({ id, name: name || "", device: deviceType() }),
      keepalive: true,
    }).then(
      () => { try { localStorage.setItem(DAY_KEY, today); } catch {} },
      () => {}                               // ננסה שוב בכניסה הבאה
    );
  } catch {
    // אין גישה ל-localStorage (גלישה בסתר וכו'): לא מדווחים, כדי לא לספור את אותו אדם כמה פעמים
  }
}

function newId() {
  if (crypto.randomUUID) return crypto.randomUUID();
  return Array.from(crypto.getRandomValues(new Uint8Array(16)),
    b => b.toString(16).padStart(2, "0")).join("");
}

function deviceType() {
  const ua = navigator.userAgent;
  const os =
    /iPhone/.test(ua) ? "iPhone" :
    /iPad/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1) ? "iPad" :
    /Android/.test(ua) ? "Android" :
    /Windows/.test(ua) ? "Windows" :
    /Macintosh/.test(ua) ? "Mac" :
    /Linux/.test(ua) ? "Linux" : "אחר";
  const browser =
    /SamsungBrowser/.test(ua) ? "Samsung" :
    /FBAN|FBAV|Instagram/.test(ua) ? "Facebook" :
    /Edg\//.test(ua) ? "Edge" :
    /CriOS|Chrome\//.test(ua) ? "Chrome" :
    /Safari\//.test(ua) ? "Safari" :
    /Firefox\//.test(ua) ? "Firefox" : "";
  return browser ? os + " / " + browser : os;
}
