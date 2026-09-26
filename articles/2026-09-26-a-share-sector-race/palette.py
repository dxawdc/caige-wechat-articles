"""Shared board colors for the video and standalone HTML."""

COLOR_FAMILIES = (
    ("#315f85", "#42729a", "#3a698f", "#527fa3", "#486f91", "#6488a5"),
    ("#227775", "#348781", "#2a777b", "#4a928b", "#387f82", "#629b96"),
    ("#a8753d", "#b58145", "#986e3c", "#bd8c53", "#a67d49", "#c29967"),
    ("#a65b62", "#b7696b", "#9b555f", "#be7876", "#ac6870", "#c4867f"),
    ("#706389", "#817198", "#665d82", "#9080a4", "#786c90", "#9a8aa9"),
)

BOARD_COLORS = tuple(
    COLOR_FAMILIES[index % len(COLOR_FAMILIES)][index // len(COLOR_FAMILIES)]
    for index in range(30)
)
