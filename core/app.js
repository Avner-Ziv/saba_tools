// הליבה: טוענת את רשימת המודולים וההעדפות, ומנתבת בין המסכים.
//
// כתובות:
//   #/            מסך הבית. אם מופעל מודול אחד בלבד, הוא מוצג ישירות
//   #/m/<id>      מודול
//   #/settings    הגדרות

import { el, message, setPath } from "./ui.js";
import { LocalPrefsStore, defaultsFromSchema, mergeDeep } from "./prefs.js";
import { renderSettings } from "./settings.js";

const VERSION = new URL(import.meta.url).searchParams.get("v") || "";
const withV = p => VERSION ? p + (p.includes("?") ? "&" : "?") + "v=" + VERSION : p;

const APP_NAME = "הזמנת סרט";
const FONT_SIZES = { normal: "16px", large: "18.5px", xlarge: "21px" };

const state = {
  store: new LocalPrefsStore(),
  generalSchema: null,
  modules: {},        // id -> { manifest, schema, view }
  order: [],          // סדר המודולים מתוך modules/index.json
  defaults: null,     // ברירות מחדל מכל ה-schemas
  saved: {},          // רק מה שהמשתמש שינה
  prefs: null,        // defaults + saved
};

async function getJSON(path) {
  const r = await fetch(withV(path));
  if (!r.ok) throw new Error(path + ": HTTP " + r.status);
  return r.json();
}

async function boot() {
  const root = document.getElementById("app");
  try {
    state.generalSchema = await getJSON("core/general.schema.json");
    const registry = await getJSON("modules/index.json");
    state.order = registry.modules;

    await Promise.all(state.order.map(async id => {
      const base = "modules/" + id + "/";
      const [manifest, schema, view] = await Promise.all([
        getJSON(base + "module.json"),
        getJSON(base + "prefs.schema.json"),
        import("../" + withV(base + "view.js")),
      ]);
      state.modules[id] = { manifest, schema, view };
    }));
  } catch (err) {
    console.error(err);
    message(root, "לא הצלחתי לטעון את האפליקציה. נסה לרענן את הדף.");
    return;
  }

  state.defaults = {
    general: { ...defaultsFromSchema(state.generalSchema), enabledModules: state.order.slice() },
    modules: Object.fromEntries(state.order.map(id => [id, defaultsFromSchema(state.modules[id].schema)])),
  };
  state.saved = await state.store.load();
  recompute();

  window.addEventListener("hashchange", route);
  route();
}

function recompute() {
  state.prefs = mergeDeep(state.defaults, state.saved);
  const size = FONT_SIZES[state.prefs.general.fontSize] || FONT_SIZES.normal;
  document.documentElement.style.fontSize = size;
}

function enabledModules() {
  const list = state.prefs.general.enabledModules || [];
  return state.order.filter(id => list.includes(id) && state.modules[id]);
}

// ---------- מסגרת: פס עליון + תוכן ----------

function frame(title, { back, settings } = {}) {
  const root = document.getElementById("app");
  root.replaceChildren();
  const bar = el("header", "topbar");
  if (back) {
    const b = el("a", "topbar-btn", "→ חזרה");
    b.href = back;
    bar.appendChild(b);
  }
  bar.appendChild(el("h1", "topbar-title", title));
  if (settings) {
    const s = el("a", "topbar-btn settings", "⚙️ הגדרות");
    s.href = "#/settings";
    bar.appendChild(s);
  }
  const content = el("div", "content");
  root.append(bar, content);
  document.title = title;
  return content;
}

// ---------- ניתוב ----------

function route() {
  const hash = location.hash.replace(/^#/, "") || "/";
  window.scrollTo(0, 0);
  if (hash === "/settings") return showSettings();
  const m = hash.match(/^\/m\/([\w-]+)$/);
  if (m && state.modules[m[1]]) return showModule(m[1]);
  return showHome();
}

function showHome() {
  const mods = enabledModules();
  if (mods.length === 1) return showModule(mods[0], true);

  const content = frame(APP_NAME, { settings: true });
  if (mods.length === 0) {
    message(content, "לא הופעל אף שירות. אפשר להפעיל בהגדרות.");
    return;
  }
  const grid = el("div", "tiles");
  for (const id of mods) {
    const { manifest } = state.modules[id];
    const t = el("a", "tile");
    t.href = "#/m/" + id;
    t.append(el("span", "tile-icon", manifest.icon), el("span", "tile-name", manifest.name));
    grid.appendChild(t);
  }
  content.appendChild(grid);
}

async function showModule(id, isHome = false) {
  const mod = state.modules[id];
  const content = frame(mod.manifest.title || mod.manifest.name, {
    back: isHome ? null : "#/",
    settings: true,
  });
  message(content, mod.manifest.loadingText || "טוען…");

  let data;
  try {
    const r = await fetch(mod.manifest.data + "?t=" + Date.now());
    if (!r.ok) throw new Error("HTTP " + r.status);
    data = await r.json();
  } catch (err) {
    console.error(err);
    message(content, "לא הצלחתי לטעון את הנתונים. נסה שוב בעוד כמה דקות.");
    return;
  }

  try {
    mod.view.render(content, {
      data,
      prefs: state.prefs.modules[id],
      general: state.prefs.general,
      config: mod.manifest.config || {},
    });
  } catch (err) {
    console.error(err);
    message(content, "משהו השתבש בהצגת הנתונים.");
  }
}

function showSettings() {
  const content = frame("הגדרות", { back: "#/" });
  const status = el("div", "save-status");
  status.setAttribute("role", "status");
  const form = el("div");

  const sections = [{
    title: state.generalSchema.title,
    schema: state.generalSchema,
    prefix: "general",
    values: state.prefs.general,
  }];
  for (const id of enabledModules()) {
    const mod = state.modules[id];
    sections.push({
      title: mod.schema.title || mod.manifest.name,
      schema: mod.schema,
      prefix: "modules." + id,
      values: state.prefs.modules[id],
    });
  }

  let statusTimer;
  renderSettings(form, sections, async (path, value) => {
    setPath(state.saved, path, value);
    recompute();
    const ok = await state.store.save(state.saved);
    status.textContent = ok ? "✓ נשמר" : "לא הצלחתי לשמור במכשיר הזה";
    status.classList.toggle("error", !ok);
    status.classList.add("show");
    clearTimeout(statusTimer);
    statusTimer = setTimeout(() => status.classList.remove("show"), 2000);
  });

  const done = el("a", "btn-primary", "סיימתי, חזרה לרשימה");
  done.href = "#/";

  const reset = el("button", "btn-link", "החזרת כל ההגדרות לברירת המחדל");
  reset.type = "button";
  let armed = false;
  reset.addEventListener("click", async () => {
    if (!armed) {
      armed = true;
      reset.textContent = "לחץ שוב לאישור";
      setTimeout(() => { armed = false; reset.textContent = "החזרת כל ההגדרות לברירת המחדל"; }, 4000);
      return;
    }
    state.saved = {};
    recompute();
    await state.store.save(state.saved);
    showSettings();
  });

  content.append(form, done, reset, status);
}

boot();
