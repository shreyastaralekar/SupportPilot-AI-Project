const req = m => v => v.trim() ? "" : m;
const email = v => !v.trim() ? "Enter your work email." : /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v.trim()) ? "" : "Enter a valid email address.";
const strong = v => v.length >= 8 && /[a-z]/.test(v) && /[A-Z]/.test(v) && /\d/.test(v) && /[^\w\s]/.test(v) ? "" : "Use 8+ characters with upper and lower case, a number and a symbol.";
function msg(t, kind) { const m = $("#msg"); m.textContent = t || ""; m.className = kind || ""; }
function show(p) {
  document.querySelectorAll(".pane").forEach(x => x.hidden = x.id !== p);
  document.querySelectorAll("#tabs button").forEach(b => b.classList.toggle("on", b.dataset.p === (p === "up" ? "emp" : p)));
  msg("");
}
document.querySelectorAll("[data-p]").forEach(b => b.addEventListener("click", () => show(b.dataset.p)));
const go = () => { location.href = "/dashboard"; };
bind($("#emp"), {login_id: email, password: req("Enter your password.")}, d => api("/api/login", {role: "employee", ...d}), go);
bind($("#adm"), {login_id: req("Enter your Admin ID."), password: req("Enter your password.")}, d => api("/api/login", {role: "admin", ...d}), go);
bind($("#up"), {
  name: v => /^[^\W\d_](?:[^\W\d_]|[ .'-])+$/.test(v.trim()) && v.trim().length <= 60 ? "" : "Enter your full name (letters only).",
  email, department: req("Choose your department."), password: strong,
  confirm: (v, f) => v === f.elements.password.value ? "" : "Passwords do not match.",
}, d => api("/api/signup", d), (r, d) => { show("emp"); $("#emp").elements.login_id.value = d.email; msg("Account created. Sign in to continue.", "ok"); });
