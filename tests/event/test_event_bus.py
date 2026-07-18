from astronavigator.event.event import Event
from astronavigator.event.event_bus import EventBus
from astronavigator.event.event_type import EventType



def test_subscribe():
    bus = EventBus()

    called = False

    def callback(event: Event):
        nonlocal called
        called = True

    bus.subscribe(EventType.TIME_CHANGED, callback)
    bus.publish(EventType.TIME_CHANGED)

    assert called


def test_unsubscribe():
    bus = EventBus()

    called = False

    def callback(event: Event):
        nonlocal called
        called = True

    bus.subscribe(EventType.TIME_CHANGED, callback)
    bus.unsubscribe(EventType.TIME_CHANGED, callback)
    bus.publish(EventType.TIME_CHANGED)

    assert not called



def test_multiple_subscribers():
    bus = EventBus()

    count = 0


    def callback1(event: Event):
        nonlocal count
        count += 1

    def callback2(event: Event):
        nonlocal count
        count += 1


    bus.subscribe(EventType.TIME_CHANGED, callback1)
    bus.subscribe(EventType.TIME_CHANGED, callback2)

    bus.publish(EventType.TIME_CHANGED)

    assert count == 2


def test_payload():
    bus = EventBus()

    received = None

    def callback(event: Event):
        nonlocal received
        received = event.payload

    bus.subscribe(EventType.TIME_CHANGED, callback)
    bus.publish(EventType.TIME_CHANGED, 123)

    assert received == 123