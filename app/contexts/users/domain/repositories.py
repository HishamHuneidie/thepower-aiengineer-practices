from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class UserRepository(ABC):
    @abstractmethod
    def list(self) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def get(self, user_id: int) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def update(self, user_id: int, data: Dict) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        raise NotImplementedError
