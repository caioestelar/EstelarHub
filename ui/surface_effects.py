# -*- coding: utf-8 -*-
"""Shared Qt surface effects for the Estelar UI."""

from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QGraphicsDropShadowEffect, QWidget


SHADOW_OPACITY = 0.15
SHADOW_BLUR_RADIUS = 18
SHADOW_VERTICAL_OFFSET = 4


def aplicar_sombra_superficie(widget: QWidget) -> QGraphicsDropShadowEffect | None:
    """Aplica sombra suave de 15% sem substituir efeitos existentes."""
    if widget.graphicsEffect() is not None:
        return None

    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(SHADOW_BLUR_RADIUS)
    effect.setOffset(0, SHADOW_VERTICAL_OFFSET)
    effect.setColor(QColor(0, 0, 0, round(255 * SHADOW_OPACITY)))
    widget.setGraphicsEffect(effect)
    return effect
