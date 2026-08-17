"""Badge legibility, measured rather than judged.

White on the old yellow measured 1.98:1 against a WCAG floor of 4.5:1, so a
badge reading 55% was unreadable and nothing said so. Contrast is arithmetic, so
it is checked rather than left to whoever picks the next colour.
"""
from __future__ import annotations

import re

import pytest

pytest.importorskip("pyshacl")

from specl.validate_spec import (  # noqa: E402
    BADGE_COLOURS,
    BADGE_LABEL_FILL,
    BADGE_LABEL_TEXT,
    badge_background,
    badge_svg,
    contrast_ratio,
    readable_text,
)

# WCAG 2.1 AA for normal text. Badge text is small, so this is a floor rather
# than a target.
MINIMUM = 4.5


def test_the_known_bad_pairing_is_measurably_bad():
    """The regression this exists for. Without it the threshold is a number
    nobody can justify."""
    assert contrast_ratio("#dfb317", "#ffffff") < MINIMUM


@pytest.mark.parametrize("name", sorted(BADGE_COLOURS))
def test_every_badge_colour_is_legible(name):
    background = BADGE_COLOURS[name]
    assert contrast_ratio(background, readable_text(background)) >= MINIMUM


def test_the_label_half_is_legible():
    assert contrast_ratio(BADGE_LABEL_FILL, BADGE_LABEL_TEXT) >= MINIMUM


@pytest.mark.parametrize("score", [0, 25, 49, 50, 55, 84, 85, 99, 100, None])
def test_every_score_renders_legibly(score):
    """Including the boundaries, where the colour changes."""
    background = badge_background(score)
    label = "failing" if score is None else f"{score}%"
    svg = badge_svg(label, background)
    fill = re.findall(r'<text[^>]*fill="([^"]+)"', svg)[1]
    assert contrast_ratio(background, fill) >= MINIMUM
    assert f">{label}</text>" in svg


def test_readable_text_picks_the_better_of_the_two():
    assert readable_text("#ffffff") == "#1a1a1a"
    assert readable_text("#000000") == "#ffffff"


def test_the_badge_is_wide_enough_for_its_text():
    """`failing` is longer than a percentage and used to render at the same
    fixed width, so it overflowed its own rectangle."""
    narrow = int(re.search(r'width="(\d+)"', badge_svg("5%", "#8fb996")).group(1))
    wide = int(re.search(r'width="(\d+)"', badge_svg("failing", "#b08585")).group(1))
    assert wide > narrow


def test_the_badge_carries_an_accessible_label():
    svg = badge_svg("55%", BADGE_COLOURS["mid"])
    assert 'role="img"' in svg
    assert 'aria-label="spec maturity: 55%"' in svg
