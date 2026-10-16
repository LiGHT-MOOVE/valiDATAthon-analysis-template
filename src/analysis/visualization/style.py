"""Configuration for consistent plot styling."""

import random
from dataclasses import dataclass, field


def generate_random_colors(
    names: list[str] | None = None,
) -> dict[str, str]:
    """Generate a random hex color for each name."""
    names = names or []
    rng = random.SystemRandom()
    colors = set()
    while len(colors) < len(names):
        color = f"#{rng.randint(0, 0xFFFFFF):06X}"
        colors.add(color)
    return dict(zip(names, colors))


@dataclass(frozen=True)
class PlotStyle:
    """Store visual style settings used across figures."""

    font_title: int = 12
    font_subtitle: int = 11
    font_label: int = 10
    font_tick: int = 9
    font_legend: int = 9
    font_value: int = 9

    primary_color: str = "#105091"
    secondary_color: str = "#7C7F82"
    grid_color: str = "#D9D9D9"
    text_color: str = "#000000"
    muted_text_color: str = "#666666"
    country_colors: dict[str, str] = field(default_factory=dict)
    model_categories: dict[str, str] = field(default_factory=dict)
