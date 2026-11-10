/**
 * יומן משתמשים של "הזמנת סרט".
 *
 * מקבל מהאפליקציה דיווח אחד ביום לכל מכשיר, ושומר שורה אחת לכל מכשיר:
 * מזהה, שם (אם הוגדר בהגדרות), סוג מכשיר, כניסה ראשונה, כניסה אחרונה ומספר ימי שימוש.
 * העמודה "הערה" שלך בלבד: הסקריפט לא נוגע בה, וכדאי לכתוב בה מי זה.
 *
 * התקנה: ראה docs בקובץ README.md שבאותה תיקייה.
 */

const SHEET_NAME = "משתמשים";
const HEADERS = ["מזהה מכשיר", "שם", "סוג מכשיר", "כניסה ראשונה", "כניסה אחרונה", "ימי שימוש", "הערה"];
const COL = { id: 1, name: 2, device: 3, first: 4, last: 5, days: 6, note: 7 };
const TZ = "Asia/Jerusalem";

function doPost(e) {
  let payload;
  try {
    payload = JSON.parse(e.postData.contents);
  } catch (err) {
    return text("bad json");
  }

  const id = String(payload.id || "");
  if (!/^[a-z0-9-]{8,40}$/.test(id)) return text("bad id");
  const name = clean(payload.name, 60);
  const device = clean(payload.device, 40);

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const sheet = getSheet();
    const now = Utilities.formatDate(new Date(), TZ, "yyyy-MM-dd HH:mm");
    const last = sheet.getLastRow();
    let row = -1;
    if (last > 1) {
      const ids = sheet.getRange(2, COL.id, last - 1, 1).getValues();
      for (let i = 0; i < ids.length; i++) {
        if (ids[i][0] === id) { row = i + 2; break; }
      }
    }

    if (row === -1) {
      sheet.appendRow([id, name, device, now, now, 1, ""]);
    } else {
      // שם מתעדכן רק אם נשלח שם חדש, כדי לא למחוק שם קודם
      if (name) sheet.getRange(row, COL.name).setValue(name);
      if (device) sheet.getRange(row, COL.device).setValue(device);
      sheet.getRange(row, COL.last).setValue(now);
      const days = Number(sheet.getRange(row, COL.days).getValue()) || 0;
      sheet.getRange(row, COL.days).setValue(days + 1);
    }
  } finally {
    lock.releaseLock();
  }
  return text("ok");
}

// בדיקה מהדפדפן: פתיחת כתובת ה-Web app אמורה להחזיר "פועל"
function doGet() {
  return text("פועל");
}

// הרצה ידנית פעם אחת מתוך העורך, כדי ליצור את הגיליון ואת הכותרות
function setup() {
  getSheet();
}

function getSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.setFrozenRows(1);
    sheet.setRightToLeft(true);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight("bold");
    // ערכים יישמרו כטקסט, כדי שגוגל שיטס לא יהפוך אותם לתאריכים או לנוסחאות
    sheet.getRange("A:E").setNumberFormat("@");
  }
  return sheet;
}

// מנקה קלט: מקצר, מסיר שורות חדשות, ומונע הזרקת נוסחאות (= + - @ בתחילת תא)
function clean(value, max) {
  let s = String(value || "").replace(/[\r\n\t]+/g, " ").trim().slice(0, max);
  if (/^[=+\-@]/.test(s)) s = "'" + s;
  return s;
}

function text(s) {
  return ContentService.createTextOutput(s).setMimeType(ContentService.MimeType.TEXT);
}
