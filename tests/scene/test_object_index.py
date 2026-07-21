from astronavigator.scene.object_index import ObjectIndex
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import Star


def create_star(
    object_id: str,
    name: str,
    ra: float = 0,
    dec: float = 0,
    mag: float = 0,
) -> Star:
    return Star(
        id=object_id,
        name=name,
        object_type=ObjectType.STAR,
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