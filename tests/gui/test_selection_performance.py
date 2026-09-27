import os
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from astronavigator.event.event_bus import EventBus
from astronavigator.event.event_type import EventType
from astronavigator.gui.panel.selection_panel import SelectionPanel
from astronavigator.scene.scene import Scene
from astronavigator.scene.scene_controller import SceneController
from astronavigator.sky.comet_render_cache import CometRenderSnapshot, CometRenderState
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import Comet
from astronavigator.sky.object_type import ObjectType


def test_snapshot_updates_selection_and_focus_without_catalog_rebuild_or_orbit_calculation():
    qt = QApplication.instance() or QApplication([])
    scene = Scene()
    bus = EventBus()
    controller = SceneController(scene, bus, Mock())
    comet = Mock(spec=Comet)
    comet.id = "comet"
    comet.name = "Test comet"
    comet.object_type = ObjectType.COMET
    comet.get_add_info.return_value = None
    scene.selection.selected = comet
    scene.focus.target = comet
    application = SimpleNamespace(scene=scene, event_bus=bus, main_actions=Mock())
    panel = SelectionPanel(application)
    panel.show()
    qt.processEvents()
    catalog_changed = Mock()
    bus.subscribe(EventType.SCENE_UPDATED, catalog_changed)
    state = CometRenderState(Position(12, 34), Magnitude(5))
    controller.set_comet_render_snapshot(
        CometRenderSnapshot(scene.time.utc, (0, 0, 0), {"comet": state}, 0)
    )
    from astronavigator.sky.dynamic_render_cache import DynamicRenderState

    controller.set_dynamic_render_states(
        {"comet": DynamicRenderState(state.position, state.magnitude)}
    )
    panel._refresh_context()
    assert scene.sky_camera.center == state.position
    assert panel._magnitude_value.text() == "5.00"
    for _ in range(60):
        controller.advance_time(1 / 60)
    comet.get_position.assert_not_called()
    comet.get_magnitude.assert_not_called()
    catalog_changed.assert_not_called()
    panel.close()
