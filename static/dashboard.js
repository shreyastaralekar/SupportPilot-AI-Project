const ROLE = document.body.dataset.role;
let ALL = [], TAB = "Open";
const chip = p => `<span class="chip ${esc(p.slice(0, 2))}">${esc(p)}</span>`;
const sla = h => h == 168 ? "1 week" : h == 672 ? "4 weeks" : h + " hrs";
const C = {
  id: ["Ticket ID", t => `<b>${esc(t.ticket_id)}</b>`],
  title: ["Title", t => `<span title="${esc(t.description || t.title)}">${esc(t.title)}</span>`],
  req: ["Requester", t => `${esc(t.requester)}<small>${esc(t.department)}</small>`],
  cls: ["Category", t => `${esc(t.category)}<small>${esc(t.sub_category)}</small>${t.ai_status == "Needs review" ? '<small class="warn">Needs review</small>' : ""}`],
  sev: ["Severity", t => `${esc(t.severity)}<small>${t.confidence}% confidence</small>`],
  pri: ["Priority", t => chip(t.priority)],
  raised: ["Raised", t => fmt(t.created_at)],
  due: ["Expected by", t => `${fmt(t.due_at)}<small>within ${sla(t.sla_hours)}</small>`],
  closed: ["Closed on", t => fmt(t.closed_at)],
  act: ["Action", t => `<button class="mini" data-id="${esc(t.ticket_id)}" data-to="${t.status == "Open" ? "Closed" : "Open"}">${t.status == "Open" ? "Close" : "Reopen"}</button>`],
};
function render() {
  const rows = ALL.filter(t => t.status === TAB), end = TAB === "Open" ? "due" : "closed";
  const ks = ROLE === "admin" ? ["id", "title", "req", "cls", "sev", "pri", end, "act"] : ["id", "title", "pri", "raised", end];
  $("#tbl").innerHTML = `<thead><tr>${ks.map(k => `<th>${C[k][0]}</th>`).join("")}</tr></thead><tbody>` +
    (rows.length ? rows.map(t => `<tr>${ks.map(k => `<td>${C[k][1](t)}</td>`).join("")}</tr>`).join("")
      : `<tr><td class="none" colspan="${ks.length}">No ${TAB.toLowerCase()} tickets.</td></tr>`) + "</tbody>";
  document.querySelectorAll("[data-tab]").forEach(b => {
    b.classList.toggle("on", b.dataset.tab === TAB);
    b.querySelector("span").textContent = ALL.filter(t => t.status === b.dataset.tab).length;
  });
}
async function load() {
  const r = await api("/api/tickets", null, "GET");
  if (r.status === 401) { location.href = "/login"; return; }
  if (!r.ok) return;
  ALL = r.d.tickets;
  const open = ALL.filter(t => t.status === "Open").length;
  $("#s-open").textContent = open; $("#s-closed").textContent = ALL.length - open; $("#s-total").textContent = ALL.length;
  if ($("#s-acc")) $("#s-acc").textContent = Math.round(r.d.accuracy) + "%";
  render();
}
document.querySelectorAll("[data-tab]").forEach(b => b.addEventListener("click", () => { TAB = b.dataset.tab; render(); }));
$("#tbl").addEventListener("click", async e => {
  const b = e.target.closest("[data-id]"); if (!b) return;
  b.disabled = true;
  await api(`/api/tickets/${encodeURIComponent(b.dataset.id)}/status`, {status: b.dataset.to});
  load();
});
const tf = $("#tf");
if (tf) bind(tf, {
  title: v => v.trim().length < 5 ? "Enter a title of at least 5 characters." : v.trim().length > 120 ? "Keep the title under 120 characters." : "",
  description: v => v.trim().length < 20 ? "Describe the issue in at least 20 characters: what happened and any error message." : v.length > 2000 ? "Keep the description under 2000 characters." : "",
}, d => api("/api/tickets", {title: d.title, description: d.description}), t => {
  $("#raised").innerHTML = `<div class="done"><h3>Your ticket has been raised</h3><span>Ticket ID</span><big>${esc(t.ticket_id)}</big>${chip(t.priority)}
    <span>Expected resolution: within <b>${sla(t.sla_hours)}</b>, by <b>${fmt(t.due_at)}</b></span></div>`;
  tf.reset(); TAB = "Open"; load();
});
load();
