"""Arc-length flight: one continuous course, steady cruise speed, moving attacks."""

from __future__ import annotations

import bisect
import hashlib
import math
import random
import secrets
from dataclasses import dataclass

from .art import DEFAULT_CARRIER, carrier_launch_points, project
from .calendar import Calendar, Cell
from .limits import FrameLimitError

WIDTH, HEIGHT = 480, 320
GRID_X, GRID_Y, GRID_STEP = 28, 237, 8
HEADING_STEPS = 64
CRUISE_SPEED = 100.0  # Logical pixels per second, independent of export FPS.


def unit(vector):
    length = math.hypot(*vector)
    return (vector[0] / length, vector[1] / length) if length else (0.0, -1.0)


def heading(vector):
    return math.degrees(math.atan2(vector[0], -vector[1])) % 360


def sprite_heading(angle):
    return round(angle / (360 / HEADING_STEPS)) * (360 / HEADING_STEPS) % 360


def centre(cell: Cell):
    return GRID_X + cell.column * GRID_STEP + 3, GRID_Y + cell.row * GRID_STEP + 3


def route_seed(seed):
    if seed is not None and (not isinstance(seed, str) or not 1 <= len(seed) <= 128):
        raise ValueError("seed must be a string of 1..128 characters")
    return seed if seed is not None else secrets.token_hex(8)


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    heading: float
    thrust: int = 1
    bank: int = 0


class ArcPath:
    """Invert a dense arc-length table so curve parameters cannot cause braking."""

    def __init__(self, points, *, closed=False):
        self.closed = closed
        self.parameters = list(range(len(points)))
        self.lengths = [0.0]
        for a, b in zip(points, points[1:], strict=False):
            self.lengths.append(self.lengths[-1] + math.dist(a, b))
        self.length = self.lengths[-1]

        def evaluate(parameter):
            index = min(len(points) - 2, max(0, math.floor(parameter)))
            fraction = parameter - index
            return tuple(
                a + (b - a) * fraction
                for a, b in zip(points[index], points[index + 1], strict=True)
            )

        self.evaluate = evaluate

    def point(self, distance):
        distance = distance % self.length if self.closed else max(0.0, min(self.length, distance))
        upper = min(len(self.lengths) - 1, max(1, bisect.bisect_left(self.lengths, distance)))
        low_length, high_length = self.lengths[upper - 1], self.lengths[upper]
        fraction = (distance - low_length) / max(1e-12, high_length - low_length)
        parameter = self.parameters[upper - 1] + fraction * (
            self.parameters[upper] - self.parameters[upper - 1]
        )
        return self.evaluate(parameter)

    def pose(self, distance):
        point = self.point(distance)
        before, after = self.point(distance - 0.25), self.point(distance + 0.25)
        vector = (after[0] - before[0], after[1] - before[1])
        if not self.closed and distance < 0.25:
            vector = (after[0] - point[0], after[1] - point[1])
        elif not self.closed and distance > self.length - 0.25:
            vector = (point[0] - before[0], point[1] - before[1])
        far_before, far_after = self.point(distance - 5), self.point(distance + 5)
        first = heading((point[0] - far_before[0], point[1] - far_before[1]))
        last = heading((far_after[0] - point[0], far_after[1] - point[1]))
        turn = (last - first + 180) % 360 - 180
        bank = (1 if turn > 0 else -1) if abs(turn) > 4 else 0
        if not self.closed and min(distance, self.length - distance) < 5:
            bank = 0
        return Pose(*point, heading(vector), 1, bank)


def turn_points(entering, leaving):
    steps = 600
    first_angle = math.atan2(entering[1], entering[0])
    last_angle = math.atan2(leaving[1], leaving[0])
    angle_delta = (last_angle - first_angle + math.pi) % math.tau - math.pi
    points = [(0.0, 0.0)]
    for index in range(steps):
        a, b = index / steps, (index + 1) / steps
        first = first_angle + angle_delta * (3 * a * a - 2 * a**3)
        last = first_angle + angle_delta * (3 * b * b - 2 * b**3)
        x, y = points[-1]
        points.append(
            (
                x + (math.cos(first) + math.cos(last)) / (2 * steps),
                y + (math.sin(first) + math.sin(last)) / (2 * steps),
            )
        )
    return points


def course(entry_x, rng, top, height):
    # Integrate a smoothly ramped turn rate: zero curvature at each straight,
    # broad 180-degree turns, and no tight corners hidden inside spline knots.
    steps = 600
    turn = [(0.0, 0.0)]
    for index in range(steps):
        a, b = index / steps, (index + 1) / steps
        first, last = math.pi * (3 * a * a - 2 * a**3), math.pi * (3 * b * b - 2 * b**3)
        x, y = turn[-1]
        turn.append(
            (
                x + (math.cos(first) + math.cos(last)) / (2 * steps),
                y + (math.sin(first) + math.sin(last)) / (2 * steps),
            )
        )
    factor = height / turn[-1][1]
    turn = [(x * factor, y * factor) for x, y in turn]
    extent = max(x for x, _ in turn)
    right = rng.uniform(451, 461) - extent
    left = rng.uniform(19, 29) + extent
    bottom = top + height
    points = [(entry_x, top)]
    maneuvers = []
    spin_side = rng.choice(("upper", "lower")) if rng.random() < 0.6 else None
    spin_x = rng.uniform(200, 325)
    radius = rng.uniform(34, 38)
    upper_amp = rng.uniform(-5, 5)
    lower_amp = rng.uniform(-5, 5)
    phases = (rng.uniform(0, math.tau), rng.uniform(0, math.tau))

    def sweep(a, b, y, amplitude, phase):
        limit = min(5, ((b - a) / 160) ** 2 * 3)
        amplitude = max(-limit, min(limit, amplitude))
        for index in range(1, 121):
            t = index / 120
            bend = (
                amplitude
                * math.sin(math.pi * t) ** 4
                * (0.6 + 0.4 * math.sin(math.tau * t + phase))
            )
            points.append((a + (b - a) * t, y + bend))
        points[-1] = (b, y)

    def spin(x, y, direction):
        start = len(points) - 1
        # A closed, rounded loop. Curvature is zero at entry/exit, so neither
        # heading nor cruise speed jumps when joining the straight pass.
        for index in range(1, 601):
            angle = math.tau * index / 600
            px = radius * (math.sin(angle) - 0.25 * math.sin(2 * angle))
            py = radius * ((1 - math.cos(angle)) - 0.25 * (1 - math.cos(2 * angle)))
            points.append((x + direction * px, y + direction * py))
        points[-1] = (x, y)
        maneuvers.append(
            {
                "kind": "loop",
                "direction": direction,
                "start_index": start,
                "end_index": len(points) - 1,
            }
        )

    if spin_side == "upper":
        sweep(entry_x, spin_x, top, upper_amp, phases[0])
        spin(spin_x, top, 1)
        sweep(spin_x, right, top, upper_amp, phases[0])
    else:
        sweep(entry_x, right, top, upper_amp, phases[0])
    points.extend((right + x, top + y) for x, y in turn[1:])
    if spin_side == "lower":
        sweep(right, spin_x, bottom, lower_amp, phases[1])
        spin(spin_x, bottom, -1)
        sweep(spin_x, left, bottom, lower_amp, phases[1])
    else:
        sweep(right, left, bottom, lower_amp, phases[1])
    points.extend((left - x, bottom - y) for x, y in turn[1:])
    sweep(left, entry_x, top, upper_amp, phases[0])
    path = ArcPath(points, closed=True)
    path.maneuvers = [
        {
            "kind": m["kind"],
            "direction": m["direction"],
            "start_distance": path.lengths[m["start_index"]],
            "end_distance": path.lengths[m["end_index"]],
        }
        for m in maneuvers
    ]
    return path


@dataclass(frozen=True)
class Strike:
    cell: Cell
    fire: int
    hit: int
    origin: tuple[float, float]
    target: tuple[int, int]
    direction: tuple[float, float]
    jet_id: int = 0

    def projectile(self, t):
        """Leave the moving jet's nose, then bend toward the selected day cell."""
        distance = math.dist(self.origin, self.target)
        aim = unit((self.target[0] - self.origin[0], self.target[1] - self.origin[1]))
        first = tuple(
            p + v * max(12, distance * 0.4)
            for p, v in zip(self.origin, self.direction, strict=True)
        )
        last = tuple(p - v * min(12, distance * 0.2) for p, v in zip(self.target, aim, strict=True))
        return tuple(
            (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t**3 * d
            for a, b, c, d in zip(self.origin, first, last, self.target, strict=True)
        )


class Flight:
    def __init__(
        self,
        calendar: Calendar,
        fps=20,
        seed=None,
        *,
        targets=None,
        delay=0,
        jet_id=0,
        carrier=DEFAULT_CARRIER,
    ):
        self.fps = fps
        deck_point, bow_point = carrier_launch_points(carrier)
        self.carrier = carrier
        self.seed = route_seed(seed)
        self.jet_id = jet_id
        rng = random.Random(self.seed)
        top = rng.uniform(201, 207)
        height = rng.uniform(68, 76)
        sx, sy = project(*deck_point)
        bx, by = project(*bow_point)
        self.deck, self.bow = (65 + sx, 12 + sy), (65 + bx, 12 + by)
        self.runway = unit((bx - sx, by - sy))
        self.takeoff_heading = heading(self.runway)
        departure_turn = turn_points(self.runway, (1, 0))
        factor = (top - self.bow[1]) / departure_turn[-1][1]
        departure_points = [
            (self.bow[0] + x * factor, self.bow[1] + y * factor) for x, y in departure_turn
        ]
        entry = departure_points[-1]
        self.departure = ArcPath(departure_points)
        self.course = course(entry[0], rng, top, height)
        self.lap_frames = math.ceil(self.course.length / CRUISE_SPEED * fps)
        self.step = self.course.length / self.lap_frames
        self.launch_start = round(0.4 * fps) + delay
        self.launch_frames = math.ceil(2 * math.dist(self.deck, self.bow) / (self.step * fps) * fps)
        self.launch_end = self.launch_start + self.launch_frames
        self.departure_frames = math.ceil(self.departure.length / self.step)
        self.cruise_start = self.launch_end + self.departure_frames
        self.strikes = self._strikes(calendar, targets)
        last_fire = max((s.fire for s in self.strikes), default=self.cruise_start)
        laps = max(1, (last_fire - self.cruise_start) // self.lap_frames + 1)
        self.cruise_end = self.cruise_start + laps * self.lap_frames
        self.maneuvers = [
            {
                "kind": m["kind"],
                "direction": m["direction"],
                "start_frame": self.cruise_start
                + lap * self.lap_frames
                + math.ceil(m["start_distance"] / self.step),
                "end_frame": self.cruise_start
                + lap * self.lap_frames
                + math.floor(m["end_distance"] / self.step),
            }
            for lap in range(laps)
            for m in self.course.maneuvers
        ]
        approach = tuple(p - v * 55 for p, v in zip(self.deck, self.runway, strict=True))
        corner = turn_points((1, 0), (0, -1))
        factor = -(top - 137) / corner[-1][1]
        corner_x = 442 - (top - 137)
        corner = [(corner_x + x * factor, top + y * factor) for x, y in corner]
        first_return = ArcPath([entry, (corner_x, top), *corner[1:]])
        landing_turn = turn_points((0, -1), self.runway)
        factor = (approach[0] - 442) / landing_turn[-1][0]
        turn_start = (442, approach[1] - landing_turn[-1][1] * factor)
        landing_turn = [
            (turn_start[0] + x * factor, turn_start[1] + y * factor) for x, y in landing_turn
        ]
        second_return = ArcPath([corner[-1], turn_start, *landing_turn[1:]])
        self.returns = (first_return, second_return)
        self.return_frames = tuple(math.ceil(path.length / self.step) for path in self.returns)
        self.touchdown = self.cruise_end + sum(self.return_frames)
        self.approach = approach
        self.landing_frames = math.ceil(2 * math.dist(approach, self.deck) / self.step)
        self.landed = self.touchdown + self.landing_frames
        self.reset_start, self.reset_frames = self.landed + round(0.3 * fps), round(0.8 * fps)
        cycle = fps * 4
        self.frame_count = (
            math.ceil((self.reset_start + self.reset_frames + round(0.3 * fps)) / cycle) * cycle
        )
        if self.frame_count > 3000:
            raise FrameLimitError("flight exceeds the 3000-frame export limit; select fewer days")

    def _strikes(self, calendar, targets=None):
        if targets is None:
            targets = [c for c in calendar.cells() if c.day and c.day.commits]
        poses = [self.course.pose(frame * self.step) for frame in range(self.lap_frames)]
        loop_frames = {
            frame
            for frame in range(self.lap_frames)
            if any(
                m["start_distance"] <= frame * self.step <= m["end_distance"]
                for m in self.course.maneuvers
            )
        }
        candidates = []
        for cell in targets:
            target = centre(cell)
            ranked = []
            for frame, pose in enumerate(poses):
                angle = math.radians(sprite_heading(pose.heading))
                direction = math.sin(angle), -math.cos(angle)
                delta = target[0] - pose.x, target[1] - pose.y
                distance = math.hypot(*delta)
                facing = sum(a * b for a, b in zip(direction, unit(delta), strict=True))
                if distance >= 27 and facing > 0.15:
                    ranked.append((distance + 32 * (1 - facing) ** 2, frame))
            # All grid cells have a forward-facing approach on this closed course.
            if not ranked:
                raise ValueError("no forward firing approach for a commit cell")
            ranked.sort()
            choices = [frame for _, frame in ranked[: max(12, self.fps)]]
            during_loop = [(score, frame) for score, frame in ranked if frame in loop_frames]
            candidates.append((choices[0], cell, choices, during_loop))
        loop_target = None
        possible = [item for item in candidates if item[3]]
        if possible:
            loop_target = min(possible, key=lambda item: item[3][0][0])[1]
        occupied, strikes = set(), []
        interval = max(1, round(0.14 * self.fps))
        for _, cell, choices, loop_choices in sorted(
            candidates,
            key=lambda item: (item[1] != loop_target, item[0], item[1].column, item[1].row),
        ):
            if cell == loop_target:
                choices = [frame for _, frame in loop_choices[: max(12, self.fps)]]
            for lap in range(40):
                fire = next(
                    (
                        self.cruise_start + lap * self.lap_frames + frame
                        for frame in choices
                        if all(
                            self.cruise_start + lap * self.lap_frames + frame + delta
                            not in occupied
                            for delta in range(-interval + 1, interval)
                        )
                    ),
                    None,
                )
                if fire is not None:
                    break
            else:
                raise ValueError("unable to schedule every day cell; select fewer days")
            occupied.add(fire)
            pose = poses[(fire - self.cruise_start) % self.lap_frames]
            angle = math.radians(sprite_heading(pose.heading))
            direction = math.sin(angle), -math.cos(angle)
            origin = pose.x + direction[0] * 15, pose.y + direction[1] * 15
            target = centre(cell)
            duration = max(3, round((0.22 + math.dist(origin, target) / 240) * self.fps))
            strikes.append(
                Strike(cell, fire, fire + duration, origin, target, direction, self.jet_id)
            )
        return sorted(strikes, key=lambda strike: strike.hit)

    def pose(self, frame):
        if frame < self.launch_start or frame >= self.landed:
            return Pose(*self.deck, self.takeoff_heading, 0, 0)
        if frame < self.launch_end:
            u = (frame - self.launch_start) / self.launch_frames
            t = 2 * u**3 - u**4
            return Pose(
                self.deck[0] + (self.bow[0] - self.deck[0]) * t,
                self.deck[1] + (self.bow[1] - self.deck[1]) * t,
                self.takeoff_heading,
                2,
            )
        if frame < self.cruise_start:
            return self.departure.pose(
                (frame - self.launch_end) / self.departure_frames * self.departure.length
            )
        if frame < self.cruise_end:
            return self.course.pose((frame - self.cruise_start) * self.step)
        cursor = self.cruise_end
        for path, frames in zip(self.returns, self.return_frames, strict=True):
            if frame < cursor + frames:
                return path.pose((frame - cursor) / frames * path.length)
            cursor += frames
        u = (frame - self.touchdown) / self.landing_frames
        t = 2 * u - 2 * u**3 + u**4
        return Pose(
            self.approach[0] + (self.deck[0] - self.approach[0]) * t,
            self.approach[1] + (self.deck[1] - self.approach[1]) * t,
            self.takeoff_heading,
            0,
        )

    def restored(self, cell, frame):
        return frame >= self.reset_start + (cell.column / 53) * self.reset_frames

    def visible_poses(self, frame):
        return (self.pose(frame),)


class Squadron:
    """Share day-cell targets across independently seeded, staggered sorties."""

    def __init__(
        self, calendar: Calendar, jets: int, fps=20, seed=None, *, carrier=DEFAULT_CARRIER
    ):
        if type(jets) is not int or not 1 <= jets <= 3:
            raise ValueError("jets must be an integer in 1..3")
        self.fps = fps
        carrier_launch_points(carrier)
        self.carrier = carrier
        self.seed = route_seed(seed)
        targets = [c for c in calendar.cells() if c.day and c.day.commits]
        self.flights = []
        delay = 0
        for index in range(jets):
            child_seed = (
                self.seed
                if index == 0
                else hashlib.sha256(f"{self.seed}:jet:{index}".encode()).hexdigest()
            )
            flight = Flight(
                calendar,
                fps,
                child_seed,
                targets=targets[index::jets],
                delay=delay,
                jet_id=index,
                carrier=carrier,
            )
            self.flights.append(flight)
            # The next jet enters the catapult after the previous aircraft clears it.
            delay = flight.launch_end + round(0.35 * fps) - round(0.4 * fps)
        self.strikes = sorted(
            (s for flight in self.flights for s in flight.strikes), key=lambda s: s.hit
        )
        self.maneuvers = [
            {**maneuver, "jet": flight.jet_id + 1}
            for flight in self.flights
            for maneuver in flight.maneuvers
        ]
        self.landed = max(f.landed for f in self.flights)
        self.reset_start = self.landed + round(0.3 * fps)
        self.reset_frames = round(0.8 * fps)
        self.frame_count = (
            math.ceil((self.reset_start + self.reset_frames + round(0.3 * fps)) / (fps * 4))
            * fps
            * 4
        )
        if self.frame_count > 3000:
            raise FrameLimitError("flight exceeds the 3000-frame export limit; select fewer days")

    def restored(self, cell, frame):
        return frame >= self.reset_start + (cell.column / 53) * self.reset_frames

    def visible_poses(self, frame):
        if frame >= self.landed:
            return (self.flights[0].pose(0),)
        return tuple(
            flight.pose(frame)
            for index, flight in enumerate(self.flights)
            if (index == 0 or frame >= self.flights[index - 1].launch_end) and frame < flight.landed
        )
