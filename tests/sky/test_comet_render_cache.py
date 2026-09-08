from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

from astronavigator.scene.scene import Scene
from astronavigator.scene.time import Time
from astronavigator.sky.comet_render_cache import CometRenderCache, CometRenderState
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.position import Position


def test_paused_catalog_eventually_finishes_and_does_not_recalculate():
    cache = CometRenderCache()
    time = Time(utc=datetime(2026, 9, 8, tzinfo=timezone.utc), is_paused=True)
    comets = tuple(SimpleNamespace(id=str(i)) for i in range(100))
    for _ in range(100):
        batch = cache._select_update_batch(comets, 11, time)
        assert len(batch) <= 4
        for comet in batch:
            cache._updated_at[comet.id] = time.utc
    assert len(cache._updated_at) == 100
    assert cache._select_update_batch(comets, 11, time) == ()


def test_background_is_not_starved_and_selected_is_prioritized():
    cache = CometRenderCache()
    time = Time(utc=datetime(2026, 9, 8, tzinfo=timezone.utc))
    comets = tuple(SimpleNamespace(id=str(i)) for i in range(100))
    cache._state_cache = {
        str(i): CometRenderState(Position(0, 0), Magnitude(5)) for i in range(50)
    }
    batch = cache._select_update_batch(comets, 11, time, selected_id="99")
    assert batch[0].id == "99"
    assert any(50 <= int(comet.id) < 99 for comet in batch)
    assert len(batch) == 4


def test_small_time_changes_reuse_states_but_reverse_time_refreshes():
    cache = CometRenderCache()
    time = Time(utc=datetime(2026, 9, 8, tzinfo=timezone.utc))
    comet = SimpleNamespace(id="one")
    cache._updated_at[comet.id] = time.utc
    cache._state_cache[comet.id] = CometRenderState(Position(0, 0), Magnitude(5))
    time.utc += timedelta(seconds=2)
    assert cache._select_update_batch((comet,), 11, time) == ()
    assert cache._select_update_batch((comet,), 11, time, "one") == (comet,)
    time.utc -= timedelta(seconds=60)
    assert cache._select_update_batch((comet,), 11, time) == (comet,)


def test_observer_change_discards_inflight_result():
    cache = CometRenderCache()
    cache._thread_pool = Mock()
    scene = Scene()
    comet = SimpleNamespace(
        id="one",
        get_position=Mock(return_value=Position(0, 0)),
        get_magnitude=Mock(return_value=Magnitude(5)),
    )
    cache.request_update(scene.time, scene.observer, (comet,), 11)
    task = cache._active_task
    scene.observer.latitude += 1
    cache.request_update(scene.time, scene.observer, (comet,), 11)
    task.run()
    assert cache.snapshot is None
    assert not cache._busy
    assert not cache._state_cache


def test_real_time_throttle_applies_even_when_simulation_jumps():
    cache = CometRenderCache()
    cache._thread_pool = Mock()
    scene = Scene()
    comet = SimpleNamespace(id="one")
    cache.request_update(scene.time, scene.observer, (comet,), 11)
    cache._busy = False
    scene.time.utc += timedelta(seconds=600)
    cache.request_update(scene.time, scene.observer, (comet,), 11)
    assert cache._thread_pool.start.call_count == 1


def test_dark_comets_are_rejected_before_projection():
    from astronavigator.layer.object_layer import ObjectLayer
    from astronavigator.sky.comet_render_cache import CometRenderSnapshot
    from astronavigator.sky.sky_object import Comet

    comet = Mock(spec=Comet)
    comet.id = "dark"
    scene = Scene()
    scene.comet_render_snapshot = CometRenderSnapshot(
        scene.time.utc,
        (0, 0, 0),
        {"dark": CometRenderState(Position(0, 0), Magnitude(25))},
        0,
    )
    context = SimpleNamespace(scene=scene, projection=Mock())
    ObjectLayer()._render_object(comet, 11, None, context)
    context.projection.project.assert_not_called()


def test_catalog_keeps_faint_comets(tmp_path, monkeypatch):
    import pandas as pd
    from astronavigator.catalog.parser.mpc_comet_parser import MpcCometParser
    from astronavigator.catalog.parser import mpc_comet_parser

    rows = pd.DataFrame(
        [
            dict(
                designation="Faint comet",
                reference="1",
                magnitude_g=20.0,
                magnitude_k=10.0,
                perihelion_year=2000,
                perihelion_month=1,
                perihelion_day=1.0,
            )
        ]
    )
    monkeypatch.setattr(mpc_comet_parser.mpc, "load_comets_dataframe", lambda _: rows)
    monkeypatch.setattr(mpc_comet_parser.mpc, "comet_orbit", lambda *_: 1)
    context = SimpleNamespace(ephemeris={"sun": 1}, timescale=None)
    path = tmp_path / "comets.txt"
    path.touch()
    catalog = MpcCometParser(context, "test").parse(path)
    assert len(catalog.objects) == 1
    assert catalog.objects[0].magnitude_g == 20
    assert not catalog.objects[0].is_active(
        Time(utc=datetime(2026, 9, 8, tzinfo=timezone.utc))
    )


def test_high_speed_keeps_completed_and_inflight_selection():
    from astronavigator.event.event_bus import EventBus
    from astronavigator.scene.scene_controller import SceneController

    scene = Scene()
    controller = SceneController(scene, EventBus(), Mock())
    scene.time.speed = 1_000_000
    cache = CometRenderCache()
    cache._thread_pool = Mock()
    comet = SimpleNamespace(
        id="one",
        get_position=Mock(return_value=Position(12, 34)),
        get_magnitude=Mock(return_value=Magnitude(5)),
    )
    cache.request_update(scene.time, scene.observer, (comet,), 11, "one")
    task = cache._active_task
    controller.advance_time(0.016)
    cache.request_update(scene.time, scene.observer, (comet,), 11, "one")
    task.run()
    assert cache.snapshot.states["one"].position == Position(12, 34)
    previous = cache.snapshot
    controller.advance_time(0.016)
    cache.request_update(scene.time, scene.observer, (comet,), 11, "one")
    assert cache.snapshot is previous
    # 手動の日時変更では、古い座標を使い続けない。
    controller.set_time(scene.time.utc + timedelta(days=3))
    cache.request_update(scene.time, scene.observer, (comet,), 11, "one")
    assert cache.snapshot is None


def test_manual_time_change_rejects_inflight_result():
    cache = CometRenderCache()
    cache._thread_pool = Mock()
    scene = Scene()
    comet = SimpleNamespace(
        id="one",
        get_position=Mock(return_value=Position(0, 0)),
        get_magnitude=Mock(return_value=Magnitude(5)),
    )
    cache.request_update(scene.time, scene.observer, (comet,), 11)
    task = cache._active_task
    scene.time.revision += 1
    cache.request_update(scene.time, scene.observer, (comet,), 11)
    task.run()
    assert cache.snapshot is None
