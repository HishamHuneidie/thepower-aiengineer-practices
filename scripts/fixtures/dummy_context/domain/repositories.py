from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class {EntityName}RepositoryInterface(ABC):
    @abstractmethod
    def list(self) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def get(self, {entity_name}_id: int) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def update(self, {entity_name}_id: int, data: Dict) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, {entity_name}_id: int) -> bool:
        raise NotImplementedError
