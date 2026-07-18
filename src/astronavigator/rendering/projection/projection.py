from abc import ABC, abstractmethod

from astronavigator.sky.position import Position


class Projection(ABC):
    @abstractmethod
    def project(self, position: Position) -> None:
        ...

    