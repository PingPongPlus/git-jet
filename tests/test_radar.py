import pytest

from git_jet import art
from git_jet.demo import demo_calendar
from git_jet.render import Renderer


def test_radar_makes_a_complete_loop_with_distinct_front_back_and_edge_views():
    frames = [art.radar_sprite(i / 80) for i in range(80)]
    assert frames[0].tobytes() == art.radar_sprite(1).tobytes()
    assert len({frame.tobytes() for frame in frames}) >= 16
    assert frames[0].tobytes() != frames[40].tobytes()
    assert (
        frames[20].getbbox()[2] - frames[20].getbbox()[0]
        < frames[0].getbbox()[2] - frames[0].getbbox()[0]
    )
    assert all(set(frame.getchannel("A").tobytes()) == {0, 255} for frame in frames)


@pytest.mark.parametrize("fps", (5, 10, 20, 25))
@pytest.mark.parametrize("carrier", ("lincoln", "classic"))
def test_radar_timing_is_continuous_during_flight_and_after_landing(fps, carrier):
    renderer = Renderer(demo_calendar(), fps=fps, seed="radar-preview", carrier=carrier)
    x, y = art.project(*art.carrier_radar_origin(carrier))
    region = (65 + x - 7, 12 + y - 23, 65 + x + 9, 12 + y - 12)
    for frame in (0, fps, renderer.flight.landed, renderer.frame_count - 1):
        expected = art.carrier_sprite(frame / (fps * 4), carrier=carrier).crop(
            (x - 7, y - 23, x + 9, y - 12)
        )
        assert renderer.frame(frame).crop(region).tobytes() == expected.tobytes()
    assert renderer.frame(0).crop(region).tobytes() != renderer.frame(fps).crop(region).tobytes()
    assert (
        renderer.frame(0).crop(region).tobytes() == renderer.frame(fps * 4).crop(region).tobytes()
    )
