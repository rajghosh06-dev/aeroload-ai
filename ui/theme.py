"""Design tokens and color palette for AeroLoad-AI light engineering theme."""

from __future__ import annotations

from typing import Union
from engine.models import CargoCategory, HazardClass

# Base surfaces
BG_PRIMARY = "#F4F6F3"       # Clean neutral canvas
BG_PANEL = "#FFFFFF"         # Pure white surface
BG_SECONDARY = "#EEF1ED"     # Cool-tinted secondary surface
BG_SUBTLE = "#E7EBE7"        # Subtle hover / divider surface
BORDER_SUBTLE = "#D6DBD6"    # Standard boundary border
BORDER_STRONG = "#BBC4BC"    # Strong structural border

# Typography
TEXT_PRIMARY = "#202522"     # Deep graphite primary text
TEXT_SECONDARY = "#5E6761"   # Secondary readable text
TEXT_MUTED = "#808982"       # Muted annotations & captions

# Brand & engineering accents
ACCENT_PRIMARY = "#315C4B"   # Deep forest (Primary functional accent)
ACCENT_PRIMARY_HOVER = "#274B3E"
ACCENT_SECONDARY = "#AD633E" # Signal copper (Restrained character accent)

# Semantic status colors
STATUS_SUCCESS = "#3E7957"   # Confident engineering green (Valid, Solved, Legal)
STATUS_WARNING = "#B9782E"   # Warm amber / ochre (Caution, Unassigned, Controlled)
STATUS_DANGER = "#B34E48"    # Clear danger red (Violation, Blocked, Hazard)
STATUS_INFO = "#65706A"      # Slate neutral information

# Backward-compatibility map
COLORS = {
    "bg": BG_PRIMARY,
    "panel": BG_PANEL,
    "panel_alt": BG_SECONDARY,
    "border": BORDER_SUBTLE,
    "border_strong": BORDER_STRONG,
    "text": TEXT_PRIMARY,
    "muted": TEXT_MUTED,
    "accent": ACCENT_PRIMARY,
    "accent_hover": ACCENT_PRIMARY_HOVER,
    "accent_copper": ACCENT_SECONDARY,
    "accent_secondary": ACCENT_SECONDARY,
    "safe": STATUS_SUCCESS,
    "warning": STATUS_WARNING,
    "danger": STATUS_DANGER,
    "info": STATUS_INFO,
}


def status_color(is_valid: bool) -> str:
    """Return semantic hex color for validation or safety state."""
    return STATUS_SUCCESS if is_valid else STATUS_DANGER


def hazard_badge_color(hazard_class: Union[str, HazardClass]) -> str:
    """Return badge color consistent with light engineering palette."""
    val = hazard_class.value if isinstance(hazard_class, HazardClass) else str(hazard_class)
    if val in {"Flammable", "Toxic", "Biohazard"}:
        return STATUS_DANGER
    if val in {"Lithium Battery", "Oxidizer"}:
        return STATUS_WARNING
    if val == "Food":
        return STATUS_INFO
    return TEXT_MUTED


def category_badge_color(category: Union[str, CargoCategory]) -> str:
    """Return category badge color consistent with light engineering palette."""
    val = category.value if isinstance(category, CargoCategory) else str(category)
    if val == "Hazardous":
        return STATUS_DANGER
    if val == "Fragile":
        return STATUS_WARNING
    if val == "Food":
        return STATUS_INFO
    return TEXT_MUTED