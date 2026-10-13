import random
from flask import Flask, render_template, jsonify, request
from energy_optimizer import CloudSimulator, SERVER_CAPACITY

app = Flask(__name__)
sim = CloudSimulator()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state")
def get_state():
    return jsonify(sim.state())


@app.route("/api/tasks", methods=["POST"])
def add_tasks():
    data = request.get_json(silent=True) or {}
    if data.get("random"):
        cpus = [random.randint(5, 25) for _ in range(10)]
    else:
        try:
            cpu = int(data.get("cpu", 0))
        except (TypeError, ValueError):
            return jsonify(message="CPU must be a number."), 400
        if not 1 <= cpu <= SERVER_CAPACITY:
            return jsonify(message=f"CPU must be between 1 and {SERVER_CAPACITY}."), 400
        cpus = [cpu]

    added = sum(1 for c in cpus if sim.add_task(c))
    msg = f"{added} task(s) allocated."
    if added < len(cpus):
        msg += f" {len(cpus) - added} rejected (no server capacity)."
    return jsonify(message=msg, **sim.state())


@app.route("/api/optimize", methods=["POST"])
def optimize():
    ok, msg = sim.optimize()
    return jsonify(message=msg, **sim.state()), (200 if ok else 400)


@app.route("/api/reset", methods=["POST"])
def reset():
    sim.reset()
    return jsonify(message="Simulation reset.", **sim.state())


if __name__ == "__main__":
    app.run(debug=True)
