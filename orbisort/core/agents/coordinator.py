import queue
import threading
from utils.logger import get_logger

logger = get_logger()

class AgentMessage:
    def __init__(self, sender, msg_type, data):
        self.sender = sender
        self.msg_type = msg_type
        self.data = data

class Coordinator:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Coordinator, cls).__new__(cls)
            cls._instance.agents = {}
            cls._instance.subscriptions = {} # msg_type -> list of agent names
            cls._instance.msg_queue = queue.Queue()
            cls._instance.running = True
            cls._instance.lock = threading.Lock()
            cls._instance.thread = threading.Thread(target=cls._instance._dispatch_loop, daemon=True)
            cls._instance.thread.start()
        return cls._instance

    def register_agent(self, name, agent, subscriptions=None):
        with self.lock:
            self.agents[name] = agent
            if subscriptions:
                for msg_type in subscriptions:
                    if msg_type not in self.subscriptions:
                        self.subscriptions[msg_type] = []
                    self.subscriptions[msg_type].append(name)
        logger.info(f"Agent {name} registered with subscriptions: {subscriptions}")

    def subscribe(self, agent_name, msg_type):
        with self.lock:
            if msg_type not in self.subscriptions:
                self.subscriptions[msg_type] = []
            if agent_name not in self.subscriptions[msg_type]:
                self.subscriptions[msg_type].append(agent_name)

    def publish(self, sender, msg_type, data):
        self.msg_queue.put(AgentMessage(sender, msg_type, data))

    def _dispatch_loop(self):
        while self.running:
            try:
                msg = self.msg_queue.get(timeout=1)
                
                # Use a snapshot of subscriptions to avoid "dictionary changed size" error
                with self.lock:
                    target_agents = list(self.subscriptions.get(msg.msg_type, []))
                
                # Fallback: if no subscriptions, broadcast (for legacy/missing subs)
                if not target_agents and msg.msg_type != "LOG":
                    target_agents = list(self.agents.keys())

                for name in target_agents:
                    if name != msg.sender:
                        agent = self.agents.get(name)
                        if agent:
                            # Run receive in a separate thread to avoid blocking the coordinator
                            threading.Thread(target=agent.receive, args=(msg,), daemon=True).start()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Coordinator Error: {e}")

coordinator = Coordinator()
