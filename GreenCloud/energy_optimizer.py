"""
energy_optimizer.py
Simulation logic for the Green Cloud Computing project.
All values are SIMULATED - they are not measurements from real servers.
"""

# ---------------- Simulation settings (change these to experiment) ----------------
NUM_SERVERS = 5          # number of simulated servers
SERVER_CAPACITY = 100    # CPU capacity of each server (units = %)
IDLE_POWER = 100         # Watts drawn by a server that is ON but idle
MAX_POWER = 250          # Watts drawn by a server at 100% CPU
CONSOLIDATION_LIMIT = 80 # Max CPU % per server when consolidating
HOURS = 1                # Time period for energy calculation (hours)
CARBON_FACTOR = 0.82     # kg CO2 per kWh (assumed grid emission factor)


class CloudSimulator:
    def __init__(self):
        self.reset()

    def reset(self):
        self.servers = [{"id": i + 1, "tasks": [], "on": True}
                        for i in range(NUM_SERVERS)]
        self.next_task_id = 1
        self.before = None      # snapshot taken just before optimization
        self.optimized = False

    # ---------------- Helpers ----------------
    @staticmethod
    def load(server):
        return sum(t["cpu"] for t in server["tasks"])

    @staticmethod
    def power(server):
        """Linear power model: P = idle + (max - idle) * utilization.
        A server that is switched OFF consumes 0 W."""
        if not server["on"]:
            return 0.0
        util = CloudSimulator.load(server) / SERVER_CAPACITY
        return IDLE_POWER + (MAX_POWER - IDLE_POWER) * util

    def summary(self):
        active = sum(1 for s in self.servers if s["on"])
        power = sum(self.power(s) for s in self.servers)
        energy = power * HOURS                      # Wh
        co2 = energy / 1000 * CARBON_FACTOR         # kg
        return {"active_servers": active,
                "power_w": round(power, 1),
                "energy_wh": round(energy, 1),
                "co2_kg": round(co2, 3)}

    # ---------------- Task allocation (load balancing) ----------------
    def add_task(self, cpu):
        """Place the task on the least-loaded server that can fit it.
        This spreads work across all servers (the 'before' scenario)."""
        candidates = [s for s in self.servers
                      if self.load(s) + cpu <= SERVER_CAPACITY]
        if not candidates:
            return False
        target = min(candidates, key=self.load)
        target["tasks"].append({"id": self.next_task_id, "cpu": cpu})
        target["on"] = True
        self.next_task_id += 1
        self.optimized = False
        return True

    # ---------------- Energy optimization (consolidation) ----------------
    def _pack(self, tasks, limit):
        """First-Fit Decreasing bin packing. Returns list of bins or None."""
        bins = [[] for _ in range(NUM_SERVERS)]
        loads = [0] * NUM_SERVERS
        for t in sorted(tasks, key=lambda x: x["cpu"], reverse=True):
            for i in range(NUM_SERVERS):
                if loads[i] + t["cpu"] <= limit:
                    bins[i].append(t)
                    loads[i] += t["cpu"]
                    break
            else:
                return None
        return bins

    def optimize(self):
        tasks = [t for s in self.servers for t in s["tasks"]]
        if not tasks:
            return False, "No tasks to optimize. Add some tasks first."

        bins = self._pack(tasks, CONSOLIDATION_LIMIT) or self._pack(tasks, SERVER_CAPACITY)
        if bins is None:
            return False, "Workload cannot be consolidated."

        self.before = self.summary()
        for server, b in zip(self.servers, bins):
            server["tasks"] = b
            server["on"] = len(b) > 0   # idle servers are switched OFF
        self.optimized = True
        return True, "Workload consolidated. Idle servers switched off."

    # ---------------- Report ----------------
    def report(self):
        if not self.optimized or self.before is None:
            return None
        after = self.summary()
        saved = self.before["energy_wh"] - after["energy_wh"]
        pct = (saved / self.before["energy_wh"] * 100) if self.before["energy_wh"] else 0
        return {"before": self.before,
                "after": after,
                "energy_saved_wh": round(saved, 1),
                "reduction_pct": round(pct, 1),
                "co2_saved_kg": round(self.before["co2_kg"] - after["co2_kg"], 3)}

    def state(self):
        servers = []
        for s in self.servers:
            servers.append({
                "id": s["id"],
                "status": "ON" if s["on"] else "OFF",
                "task_count": len(s["tasks"]),
                "utilization": round(self.load(s) / SERVER_CAPACITY * 100, 1),
                "power_w": round(self.power(s), 1),
            })
        return {"servers": servers,
                "current": self.summary(),
                "report": self.report()}
