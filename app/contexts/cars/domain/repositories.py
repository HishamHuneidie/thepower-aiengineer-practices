from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class CarRepository(ABC):
    @abstractmethod
    def list(self) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def get(self, car_id: int) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def update(self, car_id: int, data: Dict) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, car_id: int) -> bool:
        raise NotImplementedError
