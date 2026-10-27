// מסך הגדרות שנבנה אוטומטית מקבצי ה-schema.
//
// סוגי שדות נתמכים:
//   section     - כותרת ביניים
//   text        - שדה טקסט
//   number      - מונה עם כפתורי + ו-−  (min, max)
//   choice      - בחירה אחת מתוך כפתורים (options)
//   multichoice - בחירה מרובה מתוך כפתורים (options, minSelected)
//   boolean     - כן / לא

import { el, getPath } from "./ui.js";

export function renderSettings(container, sections, onChange) {
  container.replaceChildren();
  for (const sec of sections) {
    const box = el("section", "settings-section");
    box.appendChild(el("h2", "settings-title", sec.title));
    for (const field of sec.schema.fields) {
      box.appendChild(renderField(field, sec, onChange));
    }
    container.appendChild(box);
  }
}

function renderField(field, sec, onChange) {
  if (field.type === "section") {
    return el("h3", "settings-subtitle", field.label);
  }

  const wrap = el("div", "field");
  const labelId = "lbl-" + sec.prefix.replace(/\W/g, "_") + "-" + field.key.replace(/\W/g, "_");
  const label = el("div", "field-label", field.label);
  label.id = labelId;
  wrap.appendChild(label);
  if (field.help) wrap.appendChild(el("div", "field-help", field.help));

  const path = sec.prefix + "." + field.key;
  const current = getPath(sec.values, field.key);
  const save = value => onChange(path, value);

  let control;
  switch (field.type) {
    case "text":     control = textControl(current, save, labelId); break;
    case "number":   control = numberControl(current, field, save, labelId); break;
    case "choice":   control = choiceControl(current, field.options, save, labelId); break;
    case "boolean":  control = choiceControl(current,
                       [{ value: true, label: "כן" }, { value: false, label: "לא" }], save, labelId); break;
    case "multichoice": control = multiControl(current, field, save, labelId); break;
    default:         control = el("div", "field-help", "סוג שדה לא מוכר: " + field.type);
  }
  wrap.appendChild(control);
  return wrap;
}

function textControl(value, save, labelId) {
  const input = el("input", "text-input");
  input.type = "text";
  input.value = value ?? "";
  input.setAttribute("aria-labelledby", labelId);
  let timer;
  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => save(input.value.trim()), 600);
  });
  input.addEventListener("change", () => { clearTimeout(timer); save(input.value.trim()); });
  return input;
}

function numberControl(value, field, save, labelId) {
  const min = field.min ?? 0, max = field.max ?? 99;
  let v = Number(value ?? field.default ?? min);
  const row = el("div", "stepper");
  row.setAttribute("role", "group");
  row.setAttribute("aria-labelledby", labelId);
  const minus = el("button", "stepper-btn", "−");
  const shown = el("span", "stepper-value", String(v));
  const plus = el("button", "stepper-btn", "+");
  minus.type = plus.type = "button";
  minus.setAttribute("aria-label", "פחות");
  plus.setAttribute("aria-label", "יותר");
  shown.setAttribute("aria-live", "polite");
  const update = d => {
    const nv = Math.min(max, Math.max(min, v + d));
    if (nv === v) return;
    v = nv;
    shown.textContent = String(v);
    save(v);
  };
  minus.addEventListener("click", () => update(-1));
  plus.addEventListener("click", () => update(1));
  // ב-RTL הכפתור הראשון מופיע מימין: + מימין, − משמאל
  row.append(plus, shown, minus);
  return row;
}

function choiceControl(value, options, save, labelId) {
  const row = el("div", "choice-row");
  row.setAttribute("role", "group");
  row.setAttribute("aria-labelledby", labelId);
  const buttons = options.map(opt => {
    const b = el("button", "choice-btn", opt.label);
    b.type = "button";
    b.setAttribute("aria-pressed", String(opt.value === value));
    b.addEventListener("click", () => {
      buttons.forEach(x => x.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
      save(opt.value);
    });
    row.appendChild(b);
    return b;
  });
  return row;
}

function multiControl(value, field, save, labelId) {
  const selected = new Set(Array.isArray(value) ? value : []);
  const minSel = field.minSelected ?? 0;
  const row = el("div", "choice-row");
  row.setAttribute("role", "group");
  row.setAttribute("aria-labelledby", labelId);
  for (const opt of field.options) {
    const b = el("button", "choice-btn", opt.label);
    b.type = "button";
    b.setAttribute("aria-pressed", String(selected.has(opt.value)));
    b.addEventListener("click", () => {
      if (selected.has(opt.value)) {
        if (selected.size <= minSel) return; // לא מאפשרים לבטל את האחרון
        selected.delete(opt.value);
      } else {
        selected.add(opt.value);
      }
      b.setAttribute("aria-pressed", String(selected.has(opt.value)));
      // שומרים לפי סדר האפשרויות, לא לפי סדר הלחיצות
      save(field.options.map(o => o.value).filter(x => selected.has(x)));
    });
    row.appendChild(b);
  }
  return row;
}
