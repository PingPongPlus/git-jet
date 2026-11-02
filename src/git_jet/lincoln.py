"""Lincoln carrier artwork approved by the owner on 2026-11-02."""

import math

from PIL import Image, ImageDraw

from git_jet.art import DEEP, FOAM, GOLD, INK, LIGHT, WAVE, project, radar_sprite

HULL = "#546570"
LIT = "#71838d"
DARK = "#344754"
DECK = "#596871"
RUNWAY = "#465761"
EDGE = "#b3c2c7"
MARK = "#dbe1da"
GREY = "#9caeb5"
SHADOW = "#657a86"
GLASS = "#203e50"

# Coordinates follow the supplied 2070x1138 annotated reference.
# Recover its deck axes, then use Git Jet's original pixel projection.
REFERENCE_OUTLINE = (
    (15, 829),
    (577, 687),
    (665, 624),
    (1119, 525),
    (1215, 547),
    (1618, 447),
    (1664, 454),
    (1695, 435),
    (1877, 458),
    (1808, 489),
    (1900, 511),
    (1021, 736),
    (787, 746),
    (750, 746),
    (151, 874),
)
REFERENCE_RUNWAY = ((760, 734), (1655, 458), (1808, 457), (1018, 728))
RADAR_ORIGIN = (178, 3, 60)


def reference_point(x, y, z=29):
    dx, dy = x - 15, y - 829
    fore = ((45 / 136) * dx - dy) / (142 / 562 + 45 / 136)
    across = dx - fore
    return -27 + fore * 0.18, -4 + across * 0.22, z


def flight_anchors():
    """Use the painted angled runway, with room for the whole ground sprite."""
    lane = [reference_point(*p, 30) for p in REFERENCE_RUNWAY]
    front = tuple((a + b) / 2 for a, b in zip(lane[0], lane[3], strict=True))
    rear = tuple((a + b) / 2 for a, b in zip(lane[1], lane[2], strict=True))
    length = math.dist(project(*front), project(*rear))

    def along(distance):
        return tuple(a + (b - a) * distance / length for a, b in zip(rear, front, strict=True))

    # Touch down 18 native pixels inside the rear threshold, then decelerate
    # through the 55-pixel landing roll to the same point used for the next launch.
    return along(18 + 55), along(length - 18)


def carrier_sprite(t=0):
    image = Image.new("RGBA", (350, 190))
    draw = ImageDraw.Draw(image)

    def poly(points, color):
        draw.polygon([project(*p) for p in points], fill=color)

    def line(points, color, width=1):
        draw.line([project(*p) for p in points], fill=color, width=width)

    def box(u, v, width, depth, z, height, top=GREY):
        poly([(u, v, z), (u + width, v, z), (u + width, v, z + height), (u, v, z + height)], DARK)
        poly([(u, v, z), (u, v + depth, z), (u, v + depth, z + height), (u, v, z + height)], LIT)
        poly(
            [
                (u, v + depth, z),
                (u + width, v + depth, z),
                (u + width, v + depth, z + height),
                (u, v + depth, z + height),
            ],
            HULL,
        )
        poly(
            [
                (u, v, z + height),
                (u + width, v, z + height),
                (u + width, v + depth, z + height),
                (u, v + depth, z + height),
            ],
            top,
        )

    phase = math.tau * (t % 1)
    for index, (u, v) in enumerate(
        ((-3, 27), (35, 34), (75, 40), (116, 57), (158, 57), (200, 57), (242, 56), (268, 47))
    ):
        x, y = project(u, v, 0)
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
            fill=DEEP,
        )
        draw.line((x - 5, y + 1, x + reach - 4, y - 6), fill=WAVE, width=2)
        draw.line((x - 1, y, x + reach - 9, y - 4), fill=FOAM)
    x, y = project(-12, 10, 2)
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
        fill=WAVE,
    )
    draw.line((x - 7, y, x - 2, y - 2, x + 4, y + 1, x + 10, y + 2), fill=FOAM, width=2)

    # A fine raked stem underneath the thin, straight bow deck edge.
    stem, keel = (-23, 11, 24), (-10, 11, 8)
    poly([stem, (-3, -2, 24), (23, 6, 24), (27, 28, 24), (18, 24, 4), keel], INK)
    poly([(-22, 11, 23), (-2, 0, 23), (22, 7, 23), (25, 26, 23), (17, 23, 5), keel], LIT)
    top = [stem, (9, 26, 24), (75, 32, 24), (113, 50, 24), (257, 49, 24), (270, 33, 24)]
    bottom = [(268, 30, 3), (253, 44, 3), (119, 45, 3), (78, 29, 3), (18, 23, 4), keel]
    poly([*top, *bottom], INK)
    poly(
        [
            (-22, 12, 23),
            (10, 25, 23),
            (76, 31, 23),
            (114, 49, 23),
            (256, 48, 23),
            (268, 33, 23),
            (267, 30, 5),
            (251, 43, 5),
            (120, 44, 5),
            (79, 28, 5),
            (19, 22, 6),
            (-10, 11, 9),
        ],
        HULL,
    )
    line([stem, keel], EDGE)
    line([(20, 23, 5), (79, 29, 4), (120, 45, 4), (252, 44, 4)], DARK)
    line([(24, 24, 4), (79, 29, 3), (120, 45, 3), (250, 44, 3)], "#775650")
    for u, v in ((42, 28), (68, 30), (129, 49), (165, 49), (204, 49), (239, 49)):
        line([(u, v, 17), (u + 13, v, 17)], SHADOW)
        line([(u + 2, v, 9), (u + 10, v, 9)], DARK)
    for u, v in ((127, 49), (179, 49), (228, 49)):
        poly([(u, v, 21), (u + 23, v, 21), (u + 23, v, 10), (u, v, 10)], INK)
        line([(u + 2, v, 20), (u + 20, v, 20)], SHADOW)
        line([(u + 3, v, 11), (u + 20, v, 11)], LIT)
        for offset in (7, 14):
            line([(u + offset, v, 12), (u + offset, v, 18)], DARK)
    for u, v in ((103, 47), (158, 51), (213, 51)):
        poly([(u, v, 24), (u + 5, v + 7, 26), (u + 8, v, 12)], DARK)
        line([(u, v, 24), (u + 5, v + 7, 26)], LIT)
    for u, v in ((60, 30), (172, 49)):
        line([(u, v, 14), (u + 11, v, 14)], "#c28664", 2)
        line([(u + 2, v, 15), (u + 9, v, 15)], EDGE)

    # Exact red-guide footprint, with a two-pixel-thick flight-deck lip.
    outline = [reference_point(*p) for p in REFERENCE_OUTLINE]
    poly([(u, v, 27) for u, v, _ in outline], INK)
    poly(outline, DECK)
    line([*outline, outline[0]], EDGE)
    near_edge = [reference_point(*p, 27) for p in REFERENCE_OUTLINE[10:]]
    line(near_edge, DARK)
    for a, b in zip(outline, (*outline[1:], outline[0]), strict=True):
        distance = math.dist(a[:2], b[:2])
        for index in range(1, max(1, int(distance / 10))):
            part = index / max(1, int(distance / 10))
            u, v = a[0] + (b[0] - a[0]) * part, a[1] + (b[1] - a[1]) * part
            line([(u, v, 29), (u, v, 31)], SHADOW)

    # The green-guide landing strip begins at the port-side midship extension.
    lane = [reference_point(*p, 30) for p in REFERENCE_RUNWAY]
    poly(lane, RUNWAY)
    line(lane[:2], MARK)
    line(lane[2:], MARK)
    front = tuple((lane[0][i] + lane[3][i]) / 2 for i in range(3))
    back = tuple((lane[1][i] + lane[2][i]) / 2 for i in range(3))
    for index in range(10):
        a, b = 0.06 + index * 0.09, 0.10 + index * 0.09
        line(
            [
                tuple(front[i] + (back[i] - front[i]) * fraction for i in range(3))
                for fraction in (a, b)
            ],
            MARK,
        )
    for fraction in (0.60, 0.66, 0.72, 0.78):
        outer = tuple(lane[0][i] + (lane[1][i] - lane[0][i]) * fraction for i in range(3))
        inner = tuple(lane[3][i] + (lane[2][i] - lane[3][i]) * fraction for i in range(3))
        line([outer, inner], INK)
        draw.point(project(*inner), fill=MARK)
    # Forward catapult rails use the narrow bow, separate from the angled landing strip.
    for v in (18, 26):
        line([(-17, v, 30), (94, v + 4, 30)], SHADOW, 2)
        line([(-17, v, 30), (94, v + 4, 30)], EDGE)
    for u in (-10, -5, 0):
        for v in (18, 22, 27):
            line([(u, v, 30), (u + 3, v, 30)], MARK)
    line([(1, 14, 30), (83, 19, 30), (112, 19, 30)], GOLD)
    line([(113, 14, 30), (153, 14, 30)], GOLD)
    for u in range(16, 158, 18):
        for v in (1, 9):
            draw.point(project(u, v, 30), fill=SHADOW)
    for u, v in ((114, 49), (220, 47)):
        poly([(u, v, 30), (u + 25, v, 30), (u + 25, v + 10, 30), (u, v + 10, 30)], INK)
        poly(
            [(u + 2, v + 1, 30), (u + 23, v + 1, 30), (u + 23, v + 8, 30), (u + 2, v + 8, 30)], LIT
        )
        line([(u + 2, v + 1, 31), (u + 8, v + 1, 31)], GOLD)

    def parked(u, v):
        points = [
            (-9, 0),
            (-4, -1),
            (-1, -1),
            (3, -5),
            (5, -5),
            (3, -1),
            (8, -1),
            (10, -4),
            (11, -4),
            (9, 0),
            (11, 4),
            (10, 4),
            (8, 1),
            (3, 1),
            (5, 5),
            (3, 5),
            (-1, 1),
            (-4, 1),
        ]
        poly([(u + a, v + b, 31) for a, b in points], INK)
        line([(u - 7, v, 32), (u + 8, v, 32)], GREY, 2)
        line([(u, v, 32), (u + 4, v - 4, 32)], EDGE)
        line([(u, v, 32), (u + 4, v + 4, 32)], LIT)
        line([(u - 3, v, 33), (u, v, 33)], GLASS)
        line([(u + 8, v, 33), (u + 10, v - 3, 33)], EDGE)

    # Parked jets fill the other half of the deck, following its widening outline.
    for u, v in (
        (-9, 2),
        (15, 3),
        (39, 4),
        (63, 5),
        (4, 13),
        (30, 14),
        (56, 15),
        (80, 16),
        (107, -10),
        (132, -9),
        (155, -8),
        (101, 4),
        (126, 5),
        (151, 6),
        (211, 9),
        (233, 9),
        (254, 13),
    ):
        parked(u, v)
    box(151, 15, 7, 4, 30, 2, GOLD)
    for u, v in ((145, 18), (160, 18), (202, 10)):
        x, y = project(u, v, 31)
        draw.point((x, y - 1), fill=MARK)
        draw.point((x, y), fill=GOLD)

    # The island sits in the far-side step of the traced silhouette.
    box(160, -3, 34, 20, 29, 8, LIT)
    box(169, 0, 25, 18, 37, 14, LIT)
    box(171, -1, 25, 21, 51, 8, GREY)
    line([(173, 20, 56), (194, 20, 56)], INK, 3)
    line([(173, 20, 57), (193, 20, 57)], GLASS)
    for u in (175, 181, 187, 192):
        draw.point(project(u, 20, 56), fill=LIGHT)
    line([(171, -1, 59), (196, -1, 59), (196, 20, 59), (171, 20, 59)], EDGE)
    box(175, 2, 17, 13, 59, 3, EDGE)
    box(188, 4, 8, 9, 59, 5, DARK)
    line([(189, 5, 64), (194, 5, 64)], INK, 2)
    # Wrap the bridge glazing around its forward face, left of the hull number.
    line([(171, 1, 56), (171, 18, 56)], INK, 3)
    line([(171, 1, 57), (171, 18, 57)], GLASS)
    for v in (2, 8, 15):
        draw.point(project(171, v, 56), fill=LIGHT)
    # Recessed ventilation grille and an exposed access ladder on the forward wall.
    poly([(169, 1, 49), (169, 8, 49), (169, 8, 43), (169, 1, 43)], SHADOW)
    line([(169, 1, 49), (169, 8, 49)], EDGE)
    for z in (44, 46, 48):
        line([(169, 2, z), (169, 7, z)], DARK)
    for v in (12, 16):
        line([(169, v, 38), (169, v, 49)], DARK)
    for z in range(39, 50, 2):
        line([(169, 12, z), (169, 16, z)], EDGE)
    # A small service landing with railings breaks up the tall blank surface.
    poly([(166, 0, 40), (169, 0, 40), (169, 18, 40), (166, 18, 40)], GREY)
    line([(166, 0, 39), (166, 18, 39)], DARK)
    for v in (1, 9, 17):
        line([(166, v, 40), (166, v, 42)], EDGE)
    line([(166, 1, 42), (166, 17, 42)], EDGE)
    # Watertight service door and a short pipe on the lower forward face.
    poly([(160, 4, 35), (160, 11, 35), (160, 11, 30), (160, 4, 30)], DARK)
    line([(160, 4, 35), (160, 11, 35)], GREY)
    draw.point(project(160, 9, 32), fill=MARK)
    line([(160, 15, 30), (160, 15, 36)], SHADOW)
    for u in (171, 177, 183, 189):
        line([(u, 18, 43), (u + 2, 18, 43)], GLASS)
        line([(u, 18, 39), (u + 2, 18, 39)], SHADOW)
    line([(169, 18, 38), (194, 18, 38)], EDGE)
    x, y = project(174, 19, 49)
    for digit, rows in enumerate(((7, 1, 2, 2, 2), (7, 1, 7, 4, 7))):
        for row, bits in enumerate(rows):
            for col in range(3):
                if bits & (1 << (2 - col)):
                    draw.point((x + digit * 4 + col, y + row), fill=MARK)
    for u, v, z in ((168, 10, 58), (192, 17, 60)):
        x, y = project(u, v, z)
        draw.ellipse((x - 3, y - 4, x + 3, y + 1), fill=SHADOW)
        draw.ellipse((x - 3, y - 4, x + 2, y), fill=MARK)
        draw.point((x - 1, y - 3), fill=FOAM)

    x, y = project(*RADAR_ORIGIN)
    draw.line((x, y, x, y - 22), fill=INK, width=2)
    draw.line((x + 1, y - 1, x + 1, y - 21), fill=EDGE)
    draw.line((x - 9, y - 12, x + 8, y - 12), fill=SHADOW)
    image.alpha_composite(radar_sprite(t), (x - 7, y - 23))
    draw.line((x - 6, y - 4, x + 7, y - 4), fill=LIT)
    draw.line((x - 5, y - 4, x - 2, y - 10), fill=EDGE)
    draw.line((x + 5, y - 4, x + 2, y - 10), fill=EDGE)
    x, y = project(201, 8, 59)
    draw.line((x, y + 4, x, y - 14), fill=DARK, width=2)
    draw.line((x + 1, y + 3, x + 1, y - 13), fill=GREY)
    draw.line((x - 5, y - 8, x + 5, y - 8), fill=EDGE)
    draw.point((x, y - 15), fill=GOLD)
    return image
