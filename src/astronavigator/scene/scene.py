from __future__ import annotations
from dataclasses import dataclass

from astronavigator.scene.focus import Focus
from astronavigator.layer.layer_manager import LayerManager
from astronavigator.scene.observer import Observer
from astronavigator.scene.selection import Selection
from astronavigator.sky.sky_object import SkyObject
from astronavigator.scene.time import Time
from astronavigator.scene.sky_camera import SkyCamera


@dataclass(slots=True)
class Scene:
    observer: Observer
    time: Time

    objects: list[SkyObject]

    selection: Selection
    focus: Focus

    layer_manager: LayerManager
    sky_camera: SkyCamera