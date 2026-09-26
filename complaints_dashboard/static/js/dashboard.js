const state = {
  page: 1,
  perPage: 25,
  totalRows: 0,
};

const charts = {};

function currentFilters() {
  const params = new URLSearchParams();
  const start = document.getElementById("start").value;
  const end = document.getElementById("end").value;
  const category = document.getElementById("category").value;
  const region = document.getElementById("region").value;
  const status = document.getElementById("status").value;
  const priority = document.getElementById("priority").value;
  const channel = document.getElementById("channel").value;

  if (start) params.set("start", start);
  if (end) params.set("end", end);
  if (category) params.set("category", category);
  if (region) params.set("region", region);
  if (status) params.set("status", status);
  if (priority) params.set("priority", priority);
  if (channel) params.set("channel", channel);

  return params;
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${url}`);
  return res.json();
}

function populateSelect(id, values, selected) {
  const select = document.getElementById(id);
  const current = selected ?? select.value;
  select.innerHTML = '<option value="">All</option>';
  for (const value of values) {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = value;
    if (value === current) opt.selected = true;
    select.appendChild(opt);
  }
}

async function loadFilterOptions() {
  const data = await fetchJSON("/api/filters");
  populateSelect("category", data.category);
  populateSelect("region", data.region);
  populateSelect("status", data.status);
  populateSelect("priority", data.priority);
  populateSelect("channel", data.channel);

  if (data.date_range.min) document.getElementById("start").min = data.date_range.min;
  if (data.date_range.max) document.getElementById("start").max = data.date_range.max;
  if (data.date_range.min) document.getElementById("end").min = data.date_range.min;
  if (data.date_range.max) document.getElementById("end").max = data.date_range.max;
}

async function loadKPIs() {
  const params = currentFilters();
  const data = await fetchJSON(`/api/kpis?${params}`);
  document.getElementById("kpi-total").textContent = data.total ?? "–";
  document.getElementById("kpi-open").textContent = data.open_count ?? "–";
  document.getElementById("kpi-avg-days").textContent = data.avg_days_to_close ?? "–";
  document.getElementById("kpi-sla-breach").textContent =
    data.sla_breach_pct != null ? `${data.sla_breach_pct}%` : "–";
  document.getElementById("kpi-reopened").textContent = data.reopened_count ?? "–";
}

function renderChart(canvasId, type, labels, datasets, options = {}) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  if (charts[canvasId]) charts[canvasId].destroy();
  charts[canvasId] = new Chart(ctx, {
    type,
    data: { labels, datasets },
    options: { responsive: true, maintainAspectRatio: false, ...options },
  });
}

async function loadTrend() {
  const params = currentFilters();
  const data = await fetchJSON(`/api/trend?${params}`);
  const labels = data.map((r) => r.month);
  const opened = data.map((r) => r.opened);
  const slaBreach = data.map((r) => r.sla_breach_pct);
  renderChart(
    "chart-trend",
    "line",
    labels,
    [
      { label: "Complaints opened", data: opened, borderColor: "#2b6cb0", backgroundColor: "#2b6cb033", tension: 0.2, yAxisID: "y" },
      { label: "SLA breach %", data: slaBreach, borderColor: "#c05621", backgroundColor: "#c0562133", tension: 0.2, yAxisID: "y1" },
    ],
    {
      scales: {
        y: { position: "left", title: { display: true, text: "Complaints" } },
        y1: { position: "right", title: { display: true, text: "SLA breach %" }, grid: { drawOnChartArea: false } },
      },
    }
  );
}

async function loadGroupChart(endpoint, canvasId, color) {
  const params = currentFilters();
  const data = await fetchJSON(`/${endpoint}?${params}`);
  const labels = data.map((r) => r.label);
  const counts = data.map((r) => r.count);
  renderChart(canvasId, "bar", labels, [{ label: "Complaints", data: counts, backgroundColor: color }]);
}

async function loadTable() {
  const params = currentFilters();
  params.set("page", state.page);
  params.set("per_page", state.perPage);
  const data = await fetchJSON(`/api/complaints?${params}`);
  state.totalRows = data.total;

  const tbody = document.querySelector("#complaints-table tbody");
  tbody.innerHTML = "";
  for (const row of data.rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.complaint_id}</td>
      <td>${row.date_opened}</td>
      <td>${row.date_closed ?? ""}</td>
      <td>${row.status}</td>
      <td>${row.channel}</td>
      <td>${row.category}</td>
      <td>${row.priority}</td>
      <td>${row.region}</td>
      <td>${row.days_to_close ?? ""}</td>
      <td>${row.sla_breach ? "Yes" : "No"}</td>
    `;
    tbody.appendChild(tr);
  }

  const totalPages = Math.max(Math.ceil(state.totalRows / state.perPage), 1);
  document.getElementById("page-info").textContent = `Page ${state.page} of ${totalPages}`;
  document.getElementById("prev-page").disabled = state.page <= 1;
  document.getElementById("next-page").disabled = state.page >= totalPages;
}

async function refreshAll() {
  await Promise.all([
    loadKPIs(),
    loadTrend(),
    loadGroupChart("api/by-category", "chart-category", "#2b6cb0"),
    loadGroupChart("api/by-region", "chart-region", "#38a169"),
    loadGroupChart("api/by-priority", "chart-priority", "#c05621"),
    loadGroupChart("api/by-channel", "chart-channel", "#805ad5"),
    loadTable(),
  ]);
}

document.getElementById("apply-filters").addEventListener("click", () => {
  state.page = 1;
  refreshAll();
});

document.getElementById("reset-filters").addEventListener("click", () => {
  for (const id of ["start", "end", "category", "region", "status", "priority", "channel"]) {
    document.getElementById(id).value = "";
  }
  state.page = 1;
  refreshAll();
});

document.getElementById("prev-page").addEventListener("click", () => {
  if (state.page > 1) {
    state.page -= 1;
    loadTable();
  }
});

document.getElementById("next-page").addEventListener("click", () => {
  state.page += 1;
  loadTable();
});

(async function init() {
  await loadFilterOptions();
  await refreshAll();
})();
