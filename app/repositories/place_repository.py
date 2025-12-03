from abc import ABC, abstractmethod
from typing import Iterable

from app.models.location import Place
from app.data.sample_places import SAMPLE_PLACES


class AbstractPlaceRepository(ABC):
    @abstractmethod
    def list_places(self) -> Iterable[Place]:
        raise NotImplementedError


class InMemoryPlaceRepository(AbstractPlaceRepository):
    """
    Simple in-memory repository backed by static Addis Ababa data.
    Replace with a DB-backed implementation when needed.
    """

    def __init__(self) -> None:
        self._places: list[Place] = SAMPLE_PLACES

    def list_places(self) -> Iterable[Place]:
        return list(self._places)


