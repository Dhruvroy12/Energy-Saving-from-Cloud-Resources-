let chart = null;

async function api(url, method = "GET", body = null) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  return res.json();
}

function barColor(u) {
  if (u >= 80) return "#c62828";
  if (u >= 50) return "#f9a825";
  return "#43a047";
}

function render(data) {
  // Server table
  const body = document.getElementById("serverBody");
  body.innerHTML = "";
  data.servers.forEach(s => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>Server ${s.id}</td>
      <td class="${s.status === "ON" ? "on" : "off"}">${s.status}</td>
      <td>${s.task_count}</td>
      <td><div class="bar">
            <div class="bar-fill" style="width:${s.utilization}%;background:${barColor(s.utilization)}"></div>
            <span class="bar-label">${s.utilization}%</span>
          </div></td>
      <td>${s.power_w}</td>`;
    body.appendChild(tr);
  });

  // Totals
  document.getElementById("activeServers").textContent = data.current.active_servers;
  document.getElementById("totalPower").textContent = data.current.power_w;
  document.getElementById("totalEnergy").textContent = data.current.energy_wh;

  // Report
  const r = data.report;
  document.getElementById("noReport").classList.toggle("hidden", !!r);
  document.getElementById("reportBox").classList.toggle("hidden", !r);
  if (!r) return;

  document.getElementById("rBeforeSrv").textContent = r.before.active_servers;
  document.getElementById("rAfterSrv").textContent = r.after.active_servers;
  document.getElementById("rBeforeE").textContent = r.before.energy_wh;
  document.getElementById("rAfterE").textContent = r.after.energy_wh;
  document.getElementById("rBeforeC").textContent = r.before.co2_kg;
  document.getElementById("rAfterC").textContent = r.after.co2_kg;
  document.getElementById("rSaved").textContent = r.energy_saved_wh;
  document.getElementById("rPct").textContent = r.reduction_pct;
  document.getElementById("rCo2").textContent = r.co2_saved_kg;

  const values = [r.before.energy_wh, r.after.energy_wh];
  if (chart) {
    chart.data.datasets[0].data = values;
    chart.update();
  } else {
    chart = new Chart(document.getElementById("energyChart"), {
      type: "bar",
      data: {
        labels: ["Before Optimization", "After Optimization"],
        datasets: [{ label: "Energy (Wh)", data: values,
                     backgroundColor: ["#e57373", "#66bb6a"] }]
      },
      options: { scales: { y: { beginAtZero: true, title: { display: true, text: "Energy (Wh)" } } },
                 plugins: { legend: { display: false } } }
    });
  }
}

function show(msg) { document.getElementById("message").textContent = msg || ""; }

async function refresh() { render(await api("/api/state")); }

document.getElementById("addBtn").onclick = async () => {
  const cpu = document.getElementById("cpuInput").value;
  const d = await api("/api/tasks", "POST", { cpu });
  show(d.message);
  if (d.servers) render(d);
};
document.getElementById("randomBtn").onclick = async () => {
  const d = await api("/api/tasks", "POST", { random: true });
  show(d.message);
  if (d.servers) render(d);
};
document.getElementById("optimizeBtn").onclick = async () => {
  const d = await api("/api/optimize", "POST");
  show(d.message);
  if (d.servers) render(d);
};
document.getElementById("resetBtn").onclick = async () => {
  const d = await api("/api/reset", "POST");
  show(d.message);
  render(d);
};

refresh();
