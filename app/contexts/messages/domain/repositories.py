from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class MessageRepositoryInterface(ABC):
    @abstractmethod
    def list(self) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def get(self, message_id: int) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict) -> Dict:
        raise NotImplementedError
