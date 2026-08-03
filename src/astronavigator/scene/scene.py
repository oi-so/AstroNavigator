from __future__ import annotations
from dataclasses import dataclass, field

from astronavigator.gui.gui_settings import GuiSettings
from astronavigator.mount.mount import Mount
from astronavigator.rendering.rendering_settings import RenderingSettings
from astronavigator.scene.focus import Focus
from astronavigator.scene.object_index import ObjectIndex
from astronavigator.scene.observer import Observer
from astronavigator.scene.selection import Selection
from astronavigator.sky.constellation_line import Constellation
from astronavigator.sky.sky_object import SkyObject
from astronavigator.scene.time import Time
from astronavigator.camera.sky_camera import SkyCamera


@dataclass(slots=True)
class Scene:
    observer: Observer = field(default_factory=Observer.default)
    time: Time = field(default_factory=Time.now)

    objects: list[SkyObject] = field(default_factory=list)
    object_index: ObjectIndex = field(default_factory=ObjectIndex)
    constellations: list[Constellation] = field(default_factory=list)

    selection: Selection = field(default_factory=Selection)
    focus: Focus = field(default_factory=Focus)

    sky_camera: SkyCamera = field(default_factory=SkyCamera.default)

    rendering_settings: RenderingSettings = field(default_factory=RenderingSettings)
    gui_settings: GuiSettings = field(default_factory=GuiSettings)

    mount: Mount = field(default_factory=Mount)