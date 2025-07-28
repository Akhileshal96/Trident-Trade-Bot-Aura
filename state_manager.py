# state_manager.py

# 🧠 In-memory bot status flag
state = {
    "running": False
}

def set_running():
    state["running"] = True

def set_stopped():
    state["running"] = False

def get_status():
    return state["running"]
