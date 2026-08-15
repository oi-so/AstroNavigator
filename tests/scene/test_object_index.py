from astronavigator.event.event_bus import EventBus
from astronavigator.rendering.projection.stereographic_projection import StereographicProjection
from astronavigator.rendering.projection.projection_manager import ProjectionManager
from astronavigator.scene.object_index import ObjectIndex
from astronavigator.scene.scene_controller import SceneController
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import Planet, Star
from astronavigator.scene.scene import Scene


def create_controller(scene: Scene) -> SceneController:
    return SceneController(scene, EventBus(), ProjectionManager(StereographicProjection()))

def create_star(
    object_id: str,
    name: str,
    ra: float = 0,
    dec: float = 0,
    mag: float = 0,
    hip: int | None = None,
    aliases: tuple[str, ...] = (),
) -> Star:
    return Star(
        id=object_id,
        name=name,
        object_type=ObjectType.STAR,
        hip=hip,
        aliases=aliases,
        _position=Position(ra, dec),
        _magnitude=Magnitude(mag),
    )

def test_update():
    star = create_star("star1", "Sirius")

    index = ObjectIndex()
    index.update([star])

    assert index.find_by_id("star1") is star


def test_find_by_id():
    star1 = create_star("star1", "Sirius")
    star2 = create_star("star2", "Betelgeuse")

    index = ObjectIndex()
    index.update([star1, star2])

    assert index.find_by_id("star2") is star2


def test_find_by_id_returns_none():
    star = create_star("star1", "Sirius")

    index = ObjectIndex()
    index.update([star])

    assert index.find_by_id("unknown") is None

def test_find_by_name():
    star1 = create_star("star1", "Sirius")
    star2 = create_star("star2", "Betelgeuse")

    index = ObjectIndex()
    index.update([star1, star2])

    assert index.find_by_name("Betelgeuse") is star2

def test_find_by_type():
    star1 = create_star("star1", "Sirius")
    star2 = create_star("star2", "Betelgeuse")

    index = ObjectIndex()
    index.update([star1, star2])

    stars = index.find_by_type(ObjectType.STAR)
    assert len(stars) == 2
    assert star1 in stars
    assert star2 in stars


def test_find_by_name_returns_none():
    star = create_star("star1", "Sirius")

    index = ObjectIndex()
    index.update([star])

    assert index.find_by_name("Betelgeuse") is None


def test_find_by_type_returns_empty_list():
    star = create_star("star1", "Sirius")

    index = ObjectIndex()
    index.update([star])

    moons = index.find_by_type(ObjectType.MOON)

    assert moons == []


def test_update_replaces_objects():
    star1 = create_star("star1", "Sirius")
    star2 = create_star("star2", "Betelgeuse")

    index = ObjectIndex()

    index.update([star1])
    index.update([star2])

    assert index.find_by_id("star1") is None
    assert index.find_by_id("star2") is star2


def test_add_object_updates_object_index():
    star1 = create_star("star1", "Sirius")
    star2 = create_star("star2", "Betelgeuse")

    scene = Scene()
    scene_controller = create_controller(scene)

    scene_controller.add_object(star1)
    scene_controller.add_object(star2)

    assert scene.object_index.find_by_id("star1") is star1
    assert scene.object_index.find_by_id("star2") is star2

def test_remove_object_updates_object_index():
    star1 = create_star("star1", "Sirius")
    star2 = create_star("star2", "Betelgeuse")

    scene = Scene()
    scene_controller = create_controller(scene)

    scene_controller.add_object(star1)
    scene_controller.add_object(star2)

    scene_controller.remove_object(star1)

    assert scene.object_index.find_by_id("star1") is None
    assert scene.object_index.find_by_id("star2") is star2



def test_find_by_query_prioritizes_exact_prefix_and_partial_matches():
    exact = create_star("exact", "Mars")
    prefix = create_star("prefix", "Marsden")
    partial = create_star("partial", "Alpha Mars")

    index = ObjectIndex()
    index.update([partial, prefix, exact])

    assert index.find_by_query("Mars") == [
        exact,
        prefix,
        partial,
    ]


def test_find_by_query_normalizes_spaces_case_and_symbols():
    star = create_star(
        "sirius",
        "Sirius",
        aliases=("Alpha Canis Majoris",),
    )

    index = ObjectIndex()
    index.update([star])

    assert index.find_by_query("ALPHA-CANIS MAJORIS") == [star]


def test_find_by_query_finds_hip_number():
    star = create_star(
        "sirius",
        "Sirius",
        hip=32349,
    )

    index = ObjectIndex()
    index.update([star])

    assert index.find_by_query("HIP 32349") == [star]
    assert index.find_by_query("hip32349") == [star]


def test_find_by_query_finds_object_id():
    star = create_star(
        "hyg:123",
        "Test Star",
    )

    index = ObjectIndex()
    index.update([star])

    assert index.find_by_query("hyg:123") == [star]


def test_find_by_query_does_not_return_duplicate_objects():
    star = create_star(
        "sirius",
        "Sirius",
        aliases=("Sirius", "Sirius A"),
    )

    index = ObjectIndex()
    index.update([star])

    assert index.find_by_query("Sirius") == [star]


def test_find_by_query_respects_limit():
    stars = [
        create_star(f"star{index}", f"Search Star {index}")
        for index in range(10)
    ]

    object_index = ObjectIndex()
    object_index.update(stars)

    results = object_index.find_by_query(
        "Search",
        limit=3,
    )

    assert len(results) == 3


def test_find_by_query_returns_empty_list_for_empty_query():
    index = ObjectIndex()
    index.update([create_star("sirius", "Sirius")])

    assert index.find_by_query("") == []
    assert index.find_by_query("   ") == []