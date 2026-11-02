"""Directional ocean swells and an advecting carrier wake, with binary alpha."""

import math
from functools import lru_cache

from PIL import Image, ImageColor, ImageDraw, ImageFilter

from .art import DEEP as ORIGINAL_DEEP
from .art import DEFAULT_CARRIER, project, validate_carrier
from .art import FOAM as ORIGINAL_FOAM
from .art import WAVE as ORIGINAL_WAVE

DEFAULT_WATER = "ocean"
WATER_STYLES = ("ocean", "original")
SIZE = (450, 210)
POSITION = (25, 12)
SHADOW = "#123747"
DEEP = "#19475b"
MID = "#20576d"
SHALLOW = "#2b687e"
SWELL = "#397e92"
GLINT = "#5b9eaf"
SPRAY = "#a5cdd2"
FOAM = "#e8eee6"
COLORS = (
    SHADOW,
    DEEP,
    MID,
    SHALLOW,
    SWELL,
    GLINT,
    SPRAY,
    FOAM,
    ORIGINAL_DEEP,
    ORIGINAL_WAVE,
    ORIGINAL_FOAM,
)
RGB = tuple(ImageColor.getcolor(color, "RGBA") for color in COLORS)


def point(u, v, z=0):
    x, y = project(u, v, z)
    return x + 40, y


def validate_water(water):
    if not isinstance(water, str) or water not in WATER_STYLES:
        raise ValueError("water must be ocean or original")
    return water


def water_sprite(t=0, *, water=DEFAULT_WATER, carrier=DEFAULT_CARRIER):
    """Sample a four-second ocean cycle independently of export frame rate."""
    validate_water(water)
    validate_carrier(carrier)
    if water == "original":
        return original_water_sprite(t, carrier=carrier)
    # All supported rates divide 400, so motion advances in equal time steps
    # at 5, 10, 20 and 25 FPS while a complete cycle fits in the frame cache.
    return _water_frame(round((t % 1) * 400) % 400, carrier)


@lru_cache(maxsize=100)
def _water_frame(index, carrier):
    time = index / 400
    phase = math.tau * time
    bow_u, bow_v, bow_z = (-12, 11, 6) if carrier == "lincoln" else (-19, 27, 5)
    mask = Image.new("L", SIZE)
    outline = (
        (-75, 10),
        (-63, -16),
        (-33, -34),
        (24, -41),
        (102, -42),
        (183, -39),
        (266, -31),
        (325, -15),
        (355, 14),
        (337, 55),
        (305, 95),
        (244, 104),
        (169, 109),
        (83, 116),
        (7, 114),
        (-51, 99),
        (-79, 69),
        (-86, 38),
    )
    ImageDraw.Draw(mask).polygon(
        [point(u, v + 2 * math.sin(phase + n * 1.3)) for n, (u, v) in enumerate(outline)], fill=255
    )
    edge = mask.filter(ImageFilter.GaussianBlur(2.5)).load()

    # Three travelling wave trains cross at different wavelengths and speeds.
    # Integer temporal frequencies close the loop without reversing the flow.
    image = Image.new("RGBA", SIZE)
    pixels = image.load()
    for y in range(29, 204):
        for x in range(5, 445):
            coverage = edge[x, y]
            grain = ((x // 3 * 73) ^ (y * 151) ^ (x // 9 * y * 7)) % 256
            if coverage == 0 or (coverage < 255 and coverage <= grain):
                continue
            dx, dy = x - 75, y - 140
            u = (0.30 * dx - 0.76 * dy) / 0.5024
            v = (0.29 * dx + 0.94 * dy) / 0.5024
            long = 0.12 * u + 0.26 * v - phase
            cross = 0.21 * u - 0.39 * v - phase * 2
            chop = 0.47 * u + 0.61 * v - phase * 3
            face = (
                0.62 * math.sin(long + 0.5 * math.sin(cross))
                + 0.27 * math.sin(cross)
                + 0.11 * math.sin(chop)
            )
            # The bow compresses the approaching swells into travelling rings.
            # Their energy falls away with distance from the submerged stem.
            if bow_u - 45 < u < bow_u + 65 and abs(v - bow_v) < 50:
                distance = math.hypot((u - bow_u) / 1.25, v - bow_v)
                pressure = max(0, 1 - distance / 55)
                face += 0.35 * pressure * math.sin(distance * 0.48 - phase * 4)
            shade = (
                0
                if face < -0.69
                else 1
                if face < -0.29
                else 2
                if face < 0.20
                else 3
                if face < 0.60
                else 4
                if face < 0.91
                else 5
            )
            pixels[x, y] = RGB[shade]

    draw = ImageDraw.Draw(image)

    # Successive pressure crests grow outward from the stem, then flatten into
    # the sea. Their ends flare aft, carrying the displaced water around the bow.
    for crest in range(3):
        age = (time * 2 + crest / 3) % 1
        radius = 3 + age * 14
        spread = 5 + age * 28
        ridge = []
        for step in range(25):
            angle = -math.pi / 2 + math.pi * step / 24
            u = bow_u + 4 + age * 12 - radius * math.cos(angle)
            v = bow_v + spread * math.sin(angle)
            z = bow_z * (1 - age) + 2 * math.sin(math.pi * age)
            ridge.append(point(u, v, z))
        draw.line(ridge, fill=SHALLOW, width=4, joint="curve")
        draw.line(ridge, fill=SWELL, width=2, joint="curve")
        if age < 0.75:
            for start in (0, 4, 9, 14, 19, 22):
                draw.line(ridge[start : start + 2], fill=SPRAY if age < 0.35 else GLINT)

    # Bright foam follows curved paths away from the contact point. A second,
    # smaller set of particles rises above the crest and falls back into it.
    for side in (-1, 1):

        def foam_point(q, side=side):
            u = bow_u - 5 * math.sin(math.pi * q) + 62 * q * q
            v = bow_v + side * (3 + 35 * q + 9 * math.sin(math.pi * q))
            return point(u, v, bow_z * (1 - q))

        for fleck in range(24):
            age = (time * 2 + fleck / 24) % 1
            color = FOAM if age < 0.45 else SPRAY if age < 0.75 else GLINT
            draw.line(
                (foam_point(max(0, age - 0.035)), foam_point(age)),
                fill=color,
                width=1 + (age < 0.25),
            )
        for droplet in range(12):
            age = (time * 3 + droplet / 12 + side * 0.07) % 1
            u = bow_u - 5 * age + 18 * age * age
            v = bow_v + side * (4 + 20 * age)
            z = bow_z + 8 * math.sin(math.pi * age) - 3 * age
            x, y = point(u, v, z)
            if age < 0.82:
                draw.line((x, y, x, y + 1), fill=FOAM if age < 0.45 else SPRAY)

    # Narrow shoulder waves carry the pressure crest into the longer hull wake.

    def shoulder(q, side):
        spread = (42 if carrier == "lincoln" else 34) if side == 1 else 22
        u = bow_u + 168 * q
        v = bow_v + side * (10 * math.sqrt(q) + spread * q)
        v += 0.8 * math.sin(phase - q * 9) * math.sin(math.pi * q)
        return point(u, v, bow_z * (1 - q))

    draw.polygon(
        [
            point(bow_u - 4, bow_v, bow_z - 1),
            point(bow_u + 3, bow_v - 7, bow_z - 1),
            point(bow_u + 18, bow_v - 8, bow_z - 1),
            point(bow_u + 22, bow_v + 12, bow_z - 1),
            point(bow_u + 4, bow_v + 8, bow_z - 1),
        ],
        fill=SHALLOW,
    )
    for side in (-1, 1):
        path = [shoulder(step / 32, side) for step in range(33)]
        draw.line(path, fill=SHALLOW, width=3, joint="curve")
        for start in range(0, 30, 4):
            draw.line(path[start : start + 3], fill=SWELL, width=2)
        for fleck in range(19):
            q = (time * 3 / 19 + fleck / 19) % 1
            x, y = shoulder(q, side)
            reach = max(1, round(3 * (1 - q)))
            color = FOAM if q < 0.20 else SPRAY if q < 0.5 else GLINT
            draw.line((x, y, x + reach, y - 1), fill=color)

    # Adjacent lanes churn at different phases along the visible waterline.
    for lane in range(3):
        for fleck in range(24):
            q = (time / 6 + fleck / 24 + lane * 0.17) % 1
            u = -3 + q * 301
            v = 35 + 20 * min(1, max(0, u / 110)) + lane * 6
            v += 2.8 * math.sin(q * 27 - phase + lane)
            x, y = point(u, v)
            length = 6 + round(3 * math.sin(q * math.tau * 5 + lane))
            draw.line((x - 1, y + 1, x + length, y - 2), fill=SWELL, width=2)
            color = SPRAY if lane == 0 and round(q * 24) % 3 else GLINT
            draw.line((x, y, x + length - 2, y - 2), fill=color)
            if lane == 0 and round(q * 24) % 4 == 0:
                draw.point((x + 1, y - 1), fill=FOAM)

    # Widening stern eddies lose their bright foam as they drift aft.
    for side in (-1, 1):
        for eddy in range(12):
            q = (time / 4 + eddy / 12 + side * 0.09) % 1
            u = 257 + q * 105
            v = 23 + side * (6 + q * 38)
            v += 3 * math.sin(q * 13 - phase + side)
            x, y = point(u, v)
            radius = 3 + round(q * 7)
            draw.arc(
                (x - radius, y - 2, x + radius, y + 3), 185, 345, fill=GLINT if q > 0.5 else SPRAY
            )
            if q < 0.35:
                draw.line((x - 2, y - 1, x + 2, y - 2), fill=FOAM)

    # Wake marks share the dissolving, transparent outer edge of the sea.
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            if edge[x, y] < 100:
                pixels[x, y] = (0, 0, 0, 0)
    return image


def original_water_sprite(t=0, *, carrier=DEFAULT_CARRIER):
    """Preserve the exact water pixels used by each original carrier drawing."""
    image = Image.new("RGBA", SIZE)
    draw = ImageDraw.Draw(image)
    phase = math.tau * (t % 1)
    if carrier == "classic":
        for index, u in enumerate((-7, 30, 70, 112, 158, 202, 241)):
            x, y = point(u, 58, -2)
            x += round(2 * math.sin(phase + index))
            y += round(math.sin(phase + index * 0.7))
            width = (22, 31, 24, 35, 23, 30, 21)[index]
            draw.polygon(
                [
                    (x - 7, y),
                    (x + width - 5, y - 10),
                    (x + width, y - 9),
                    (x + 1, y + 3),
                    (x - 10, y + 3),
                ],
                fill=ORIGINAL_DEEP,
            )
            draw.line((x - 4, y, x + width - 7, y - 9), fill=ORIGINAL_WAVE, width=2)
            draw.line((x, y - 1, x + width - 11, y - 8), fill=ORIGINAL_FOAM)
    else:
        for index, (u, v) in enumerate(
            (
                (-3, 27),
                (35, 34),
                (75, 40),
                (116, 57),
                (158, 57),
                (200, 57),
                (242, 56),
                (268, 47),
            )
        ):
            x, y = point(u, v)
            x += round(2 * math.sin(phase + index))
            y += round(math.sin(phase + index * 0.8))
            reach = (15, 21, 20, 25, 22, 24, 18, 14)[index]
            draw.polygon(
                [
                    (x - 8, y + 2),
                    (x + reach - 4, y - 7),
                    (x + reach + 4, y - 6),
                    (x + 2, y + 5),
                    (x - 10, y + 5),
                ],
                fill=ORIGINAL_DEEP,
            )
            draw.line((x - 5, y + 1, x + reach - 4, y - 6), fill=ORIGINAL_WAVE, width=2)
            draw.line((x - 1, y, x + reach - 9, y - 4), fill=ORIGINAL_FOAM)
        x, y = point(-12, 10, 2)
        draw.polygon(
            [
                (x - 10, y + 1),
                (x - 4, y - 4),
                (x + 2, y - 2),
                (x + 9, y),
                (x + 15, y + 3),
                (x + 3, y + 6),
                (x - 7, y + 5),
            ],
            fill=ORIGINAL_WAVE,
        )
        draw.line(
            (x - 7, y, x - 2, y - 2, x + 4, y + 1, x + 10, y + 2), fill=ORIGINAL_FOAM, width=2
        )
    return image
