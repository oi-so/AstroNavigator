from dataclasses import dataclass
from astronavigator.sky.position import Position



@dataclass(slots=True)
class ConstellationLine:
    start_id: str
    end_id: str



@dataclass(slots=True)
class Constellation:
    name: str
    lines: list[ConstellationLine]
    label_position: Position