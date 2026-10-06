# -*- coding: utf-8 -*-
"""Custom pointer cursor shared by EstelarMapTools windows."""

from collections import deque
import os

from qgis.PyQt.QtCore import QPoint, QSize, Qt
from qgis.PyQt.QtGui import QColor, QCursor, QImage, QPainter, QPen, QPixmap


_CURSOR_SIZE = QSize(20, 20)
_CURSOR_HOTSPOT = QPoint(1, 1)
_MAP_CURSOR_SIZE = QSize(36, 36)
_MAP_POINTER_SIZE = QSize(27, 27)
_MAP_BADGE_POSITION = (23, 23, 12, 12)
_BACKGROUND_CHANNEL_MIN = 232
_BACKGROUND_CHANNEL_SPREAD_MAX = 30
_CACHED_CURSOR = None
_CACHED_CURSOR_IMAGE = None
_CACHED_MAP_CURSORS = {}


def _is_connected_white_background(color: QColor) -> bool:
    channels = (color.red(), color.green(), color.blue())
    return (
        min(channels) >= _BACKGROUND_CHANNEL_MIN
        and max(channels) - min(channels) <= _BACKGROUND_CHANNEL_SPREAD_MAX
    )


def _remove_edge_background(image: QImage) -> QImage:
    """Make near-white pixels connected to the image edge transparent."""
    width = image.width()
    height = image.height()
    if width < 1 or height < 1:
        return image

    visited = bytearray(width * height)
    queue = deque()

    def add_edge_pixel(x: int, y: int) -> None:
        index = y * width + x
        if visited[index]:
            return
        visited[index] = 1
        color = image.pixelColor(x, y)
        if _is_connected_white_background(color):
            image.setPixelColor(x, y, QColor(color.red(), color.green(), color.blue(), 0))
            queue.append((x, y))

    for x in range(width):
        add_edge_pixel(x, 0)
        if height > 1:
            add_edge_pixel(x, height - 1)
    for y in range(1, height - 1):
        add_edge_pixel(0, y)
        if width > 1:
            add_edge_pixel(width - 1, y)

    while queue:
        x, y = queue.popleft()
        for next_x, next_y in (
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
        ):
            if not (0 <= next_x < width and 0 <= next_y < height):
                continue

            index = next_y * width + next_x
            if visited[index]:
                continue
            visited[index] = 1
            color = image.pixelColor(next_x, next_y)
            if _is_connected_white_background(color):
                image.setPixelColor(
                    next_x,
                    next_y,
                    QColor(color.red(), color.green(), color.blue(), 0),
                )
                queue.append((next_x, next_y))

    return image


def _crop_to_visible_pixels(image: QImage) -> QImage:
    left = image.width()
    top = image.height()
    right = -1
    bottom = -1

    for y in range(image.height()):
        for x in range(image.width()):
            if image.pixelColor(x, y).alpha() == 0:
                continue
            left = min(left, x)
            top = min(top, y)
            right = max(right, x)
            bottom = max(bottom, y)

    if right < left or bottom < top:
        return image
    return image.copy(left, top, right - left + 1, bottom - top + 1)


def _imagem_estelar() -> QImage:
    """Carrega e prepara o asset da marca uma única vez."""
    global _CACHED_CURSOR_IMAGE
    if _CACHED_CURSOR_IMAGE is not None:
        return QImage(_CACHED_CURSOR_IMAGE)

    asset_path = os.path.join(os.path.dirname(__file__), "assets", "estelar-cursor.png")
    image = QImage(asset_path)
    if image.isNull():
        _CACHED_CURSOR_IMAGE = QImage()
        return QImage()

    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    image = _remove_edge_background(image)
    _CACHED_CURSOR_IMAGE = _crop_to_visible_pixels(image)
    return QImage(_CACHED_CURSOR_IMAGE)


def cursor_estelar() -> QCursor:
    """Return the cached 20px branded pointer, or the native arrow on failure."""
    global _CACHED_CURSOR
    if _CACHED_CURSOR is not None:
        return QCursor(_CACHED_CURSOR)

    image = _imagem_estelar()
    if image.isNull():
        _CACHED_CURSOR = QCursor(Qt.CursorShape.ArrowCursor)
        return QCursor(_CACHED_CURSOR)

    pixmap = QPixmap.fromImage(image).scaled(
        _CURSOR_SIZE,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    hotspot = QPoint(
        min(_CURSOR_HOTSPOT.x(), pixmap.width() - 1),
        min(_CURSOR_HOTSPOT.y(), pixmap.height() - 1),
    )
    _CACHED_CURSOR = QCursor(pixmap, hotspot.x(), hotspot.y())
    return QCursor(_CACHED_CURSOR)


def cursor_estelar_mapa(arrastando: bool = False) -> QCursor:
    """Create a branded map-grab cursor, visually distinct while dragging."""
    global _CACHED_MAP_CURSORS
    estado = bool(arrastando)
    if estado in _CACHED_MAP_CURSORS:
        return QCursor(_CACHED_MAP_CURSORS[estado])

    image = _imagem_estelar()
    if image.isNull():
        return cursor_estelar()

    cursor_image = QImage(
        _MAP_CURSOR_SIZE,
        QImage.Format.Format_ARGB32,
    )
    cursor_image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(cursor_image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pointer = QPixmap.fromImage(image).scaled(
        _MAP_POINTER_SIZE,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    painter.drawPixmap(0, 0, pointer)

    x, y, width, height = _MAP_BADGE_POSITION
    painter.setPen(QPen(QColor("#101214"), 2))
    painter.setBrush(QColor("#101214"))
    painter.drawEllipse(x, y, width, height)

    if estado:
        painter.setPen(QPen(QColor("#F36A26"), 1.5))
        painter.setBrush(QColor("#F36A26"))
        painter.drawEllipse(x + 1, y + 1, width - 2, height - 2)
        painter.setPen(QPen(QColor("#FFF4EC"), 1.5))
        painter.drawLine(x + 4, y + 6, x + 8, y + 6)
    else:
        painter.setPen(QPen(QColor("#1783A5"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(x + 1, y + 1, width - 2, height - 2)
        painter.setPen(QPen(QColor("#D9F6FF"), 1.5))
        painter.setBrush(QColor("#D9F6FF"))
        painter.drawEllipse(x + 5, y + 5, 2, 2)

    painter.end()
    pixmap = QPixmap.fromImage(cursor_image)
    _CACHED_MAP_CURSORS[estado] = QCursor(
        pixmap,
        _CURSOR_HOTSPOT.x(),
        _CURSOR_HOTSPOT.y(),
    )
    return QCursor(_CACHED_MAP_CURSORS[estado])
