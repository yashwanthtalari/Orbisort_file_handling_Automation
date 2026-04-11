from abc import ABC, abstractmethod
from core.agents.coordinator import coordinator

class BaseAgent(ABC):
    def __init__(self, name, subscriptions=None):
        self.name = name
        coordinator.register_agent(name, self, subscriptions)

    def send(self, msg_type, data):
        coordinator.publish(self.name, msg_type, data)

    def subscribe(self, msg_type):
        coordinator.subscribe(self.name, msg_type)

    @abstractmethod
    def receive(self, message):
        pass
