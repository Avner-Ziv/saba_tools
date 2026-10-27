// העדפות משתמש.
//
// המבנה זהה למה שיישמר בשלב 1 ב-Firestore:
//   { general: {...}, modules: { "<moduleId>": {...} } }
//
// נשמרים רק הערכים שהמשתמש שינה. ברירות המחדל באות מקבצי ה-schema,
// כך ששינוי ברירת מחדל בקוד יגיע גם למי שלא נגע בהגדרה.
//
// בשלב 0 השמירה היא בדפדפן (localStorage). בשלב 1 תתווסף מחלקה
// FirestorePrefsStore עם אותן שתי פונקציות, load ו-save, ושום דבר אחר לא ישתנה.

import { setPath } from "./ui.js";

const STORAGE_KEY = "saba_prefs_v1";

export class LocalPrefsStore {
  async load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }

  async save(saved) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
      return true;
    } catch {
      return false;
    }
  }
}

// בונה אובייקט ברירות מחדל מתוך schema
export function defaultsFromSchema(schema) {
  const out = {};
  for (const f of schema.fields || []) {
    if (f.type === "section") continue;
    setPath(out, f.key, structuredClone(f.default));
  }
  return out;
}

export function mergeDeep(base, over) {
  if (Array.isArray(over)) return over.slice();
  if (typeof over !== "object" || over === null) return over === undefined ? base : over;
  const out = (typeof base === "object" && base !== null && !Array.isArray(base)) ? { ...base } : {};
  for (const k of Object.keys(over)) out[k] = mergeDeep(out[k], over[k]);
  return out;
}
