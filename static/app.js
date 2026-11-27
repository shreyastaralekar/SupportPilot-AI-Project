const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const fmt = iso => iso ? new Date(iso).toLocaleString([], {weekday: "short", day: "numeric", month: "short", hour: "numeric", minute: "2-digit"}) : "–";
async function api(url, body, method = "POST") {
  try {
    const r = await fetch(url, {method, headers: {"Content-Type": "application/json"}, body: body ? JSON.stringify(body) : undefined});
    return {ok: r.ok, status: r.status, d: await r.json().catch(() => ({}))};
  } catch (x) { return {ok: false, status: 0, d: {error: "Could not reach the server. Is app.py running?"}}; }
}
function setErr(f, n, m) {
  const s = f.querySelector(`[data-for="${n}"]`); if (s) s.textContent = m || "";
  const el = f.elements[n]; if (el && el.classList) el.classList.toggle("bad", !!m);
}
// Validates every field on blur/input and again on submit; only calls send() when all fields pass.
function bind(f, rules, send, done) {
  const run = n => setErr(f, n, rules[n](f.elements[n].value, f));
  for (const n in rules) {
    const el = f.elements[n];
    el.addEventListener("blur", () => run(n));
    el.addEventListener("input", () => { if (el.classList.contains("bad")) run(n); });
  }
  f.addEventListener("submit", async e => {
    e.preventDefault(); setErr(f, "_", "");
    let first = null;
    for (const n in rules) { run(n); if (!first && f.elements[n].classList.contains("bad")) first = n; }
    if (first) { f.elements[first].focus(); return; }
    const b = f.querySelector("button[type=submit]"); b.disabled = true;
    const data = Object.fromEntries(new FormData(f));
    const r = await send(data); b.disabled = false;
    if (r.ok) return done(r.d, data);
    for (const n in r.d.fields || {}) setErr(f, n, r.d.fields[n]);
    setErr(f, "_", r.d.error || "Something went wrong. Try again.");
  });
}
