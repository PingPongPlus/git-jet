import pytest
from PIL import ImageColor


@pytest.fixture
def assert_carrier_body_preserved():
    """Only the detached blue water may disappear from the approved studies."""
    sea = {ImageColor.getcolor(color, "RGBA") for color in ("#39799c", "#70b3ce", "#f1f4e8")}

    def compare(current, reference):
        assert current.size == reference.size
        pixels, original = current.load(), reference.load()
        for y in range(current.height):
            for x in range(current.width):
                assert pixels[x, y] == original[x, y] or (
                    pixels[x, y] == (0, 0, 0, 0) and original[x, y] in sea
                ), (x, y)

    return compare
