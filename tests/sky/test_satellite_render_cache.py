from types import SimpleNamespace
from unittest.mock import Mock

from astronavigator.scene.scene import Scene
from astronavigator.sky.satellite_render_cache import SatelliteRenderCache


def test_fast_forward_does_not_increase_satellite_request_rate(monkeypatch):
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(
        "astronavigator.sky.satellite_render_cache.perf_counter", lambda: clock.now
    )
    cache = SatelliteRenderCache()
    cache._thread_pool = Mock()
    scene = Scene()
    scene.time.speed = 1_000_000
    cache.request_update(scene.time, scene.observer, ())
    first = cache._active_task
    for _ in range(3):
        clock.now += 0.016
        scene.time.advance(0.016)
        cache.request_update(scene.time, scene.observer, ())
    assert cache._pending_request is None
    assert cache._active_task is first
    clock.now += 0.016
    scene.time.advance(0.016)
    cache.request_update(scene.time, scene.observer, ())
    assert cache._pending_request.time.utc == scene.time.utc
