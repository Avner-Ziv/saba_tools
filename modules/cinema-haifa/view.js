// מודול סינמטק חיפה: רשימת הקרנות לפי ימים וכפתור הזמנה בוואטסאפ.
//
// render(container, { data, prefs, general, config })
//   data    - התוכן של data/cinema-haifa.json
//   prefs   - ההעדפות של המשתמש למודול הזה (לפי prefs.schema.json)
//   general - ההעדפות הכלליות (displayName ועוד)
//   config  - ה-config מתוך module.json

import { el, message } from "../../core/ui.js";

export function render(container, { data, prefs, general, config }) {
  container.replaceChildren();

  // תמיכה גם בפורמט הישן (מערך פשוט)
  const screenings = Array.isArray(data) ? data : (data.screenings || []);

  if (data.updated_at) {
    const updated = new Date(data.updated_at);
    container.appendChild(el("div", "updated",
      "הרשימה עודכנה: " + updated.toLocaleDateString("he-IL") + " בשעה " +
      updated.toLocaleTimeString("he-IL", { hour: "2-digit", minute: "2-digit" })));
    const staleHours = config.staleAfterHours || 48;
    if ((Date.now() - updated.getTime()) / 36e5 > staleHours) {
      container.appendChild(el("div", "warning",
        "שים לב: הרשימה לא התעדכנה כבר כמה ימים. כדאי לוודא את המועד מול הסינמטק."));
    }
  }

  const now = Date.now();
  const halls = prefs.halls || [];
  const earliest = prefs.earliestTime || "";

  const upcoming = screenings
    .filter(s => !s.starts_at || new Date(s.starts_at).getTime() > now)
    .sort((a, b) => (a.starts_at || "").localeCompare(b.starts_at || ""));

  const shown = upcoming.filter(s =>
    halls.includes(hallKey(s, config)) && (!earliest || (s.time || "") >= earliest));

  const filterNote = describeFilters(prefs, config);
  if (filterNote) {
    const note = el("div", "note", filterNote + " ");
    const link = el("a", null, "לשינוי");
    link.href = "#/settings";
    note.appendChild(link);
    container.appendChild(note);
  }

  if (upcoming.length === 0) {
    container.appendChild(el("p", "message", "לא נמצאו הקרנות קרובות כרגע."));
    return;
  }
  if (shown.length === 0) {
    container.appendChild(el("p", "message", "אין הקרנות קרובות שמתאימות להגדרות שלך."));
    return;
  }

  const today = new Date();
  const todayKey = dayKey(today);
  const tomorrowKey = dayKey(new Date(today.getTime() + 864e5));

  let currentDay = null;
  for (const s of shown) {
    const d = s.starts_at ? new Date(s.starts_at) : null;
    const key = d ? dayKey(d) : s.date;
    if (key !== currentDay) {
      currentDay = key;
      const header = el("div", "day-header", s.weekday + ", " + s.date);
      if (key === todayKey) header.appendChild(el("span", "tag", "היום"));
      else if (key === tomorrowKey) header.appendChild(el("span", "tag", "מחר"));
      container.appendChild(header);
    }
    container.appendChild(card(s, prefs, general, config));
  }
}

// cinematheque / rappaport / other
function hallKey(s, config) {
  return config.halls && config.halls[s.hall_key] ? s.hall_key : "other";
}

function seatsFor(s, prefs, config) {
  const key = hallKey(s, config);
  if (key === "other") return null;
  const seat = (prefs.seats || {})[key] || {};
  return {
    name: config.halls[key].name,
    row: (seat.row || "").trim(),
    seats: (seat.seats || "").trim(),
  };
}

function card(s, prefs, general, config) {
  const hall = seatsFor(s, prefs, config);
  const c = el("div", "movie-card " + hallKey(s, config));

  c.appendChild(el("div", "movie-time", "⏰ " + s.time));
  c.appendChild(el("div", "movie-title", s.title));

  const info = el("div", "movie-info", "🏛️ אולם: " + (hall ? hall.name : s.hall_raw));
  if (hall && hall.row && hall.seats) {
    // הטווח בתוך span שלא נשבר, כדי ש-17-18 לא יתפצל בין שורות
    info.append(" (שורה " + hall.row + ", כיסאות ", el("span", "nowrap", hall.seats), ")");
  }
  c.appendChild(info);

  if (prefs.showSynopsis !== false) {
    if (s.info) c.appendChild(el("div", "movie-meta", s.info));
    if (s.synopsis) c.appendChild(el("div", "movie-desc", s.synopsis));
  }

  const link = el("a", "btn-order", "📲 שלח הזמנה ב-WhatsApp");
  link.href = "https://wa.me/" + config.whatsapp + "?text=" +
    encodeURIComponent(buildMessage(s, hall, prefs, general));
  link.target = "_blank";
  link.rel = "noopener";
  c.appendChild(link);
  return c;
}

export function buildMessage(s, hall, prefs, general) {
  const n = Number(prefs.tickets) || 2;
  const opening =
    n === 2 ? "שלום, אשמח להזמין מקום (כרטיס זוגי):" :
    n === 1 ? "שלום, אשמח להזמין מקום (כרטיס אחד):" :
              "שלום, אשמח להזמין " + n + " מקומות:";

  const name = (prefs.bookingName || general.displayName || "").trim();
  const lines = [opening];
  if (name) lines.push("- מזמין: " + name);
  lines.push("- שם הסרט: " + s.title);
  lines.push("- תאריך ושעה: " + s.weekday + ", " + s.date + ", " + s.time);
  lines.push("- אולם: " + (hall ? hall.name : s.hall_raw));
  if (hall && hall.row && hall.seats) {
    lines.push("- מקומות מבוקשים: שורה " + hall.row + ", כיסאות " + hall.seats + " (או בסמוך אליהם)");
  }
  lines.push("", "תודה!");
  return lines.join("\n");
}

function describeFilters(prefs, config) {
  const parts = [];
  const all = ["cinematheque", "rappaport", "other"];
  const halls = prefs.halls || all;
  if (!all.every(h => halls.includes(h))) {
    const names = halls.map(h => h === "other" ? "אולמות אחרים" : config.halls[h].name);
    parts.push("מוצגות הקרנות רק ב: " + names.join(", "));
  }
  if (prefs.earliestTime) parts.push("רק מהשעה " + prefs.earliestTime + " ואילך");
  return parts.length ? parts.join(". ") + "." : "";
}

function dayKey(d) {
  return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
}
