# -*- coding: utf-8 -*-
"""Custom pointer cursor shared by EstelarMapTools windows."""

from collections import deque
import os

from qgis.PyQt.QtCore import QPoint, QSize, Qt
from qgis.PyQt.QtGui import QColor, QCursor, QImage, QPixmap


_CURSOR_SIZE = QSize(40, 40)
_CURSOR_HOTSPOT = QPoint(1, 1)
_BACKGROUND_CHANNEL_MIN = 232
_BACKGROUND_CHANNEL_SPREAD_MAX = 30
_CACHED_CURSOR = None


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


def cursor_estelar() -> QCursor:
    """Return the cached 40px branded pointer, or the native arrow on failure."""
    global _CACHED_CURSOR
    if _CACHED_CURSOR is not None:
        return QCursor(_CACHED_CURSOR)

    asset_path = os.path.join(os.path.dirname(__file__), "assets", "estelar-cursor.png")
    image = QImage(asset_path)
    if image.isNull():
        _CACHED_CURSOR = QCursor(Qt.CursorShape.ArrowCursor)
        return QCursor(_CACHED_CURSOR)

    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    image = _remove_edge_background(image)
    image = _crop_to_visible_pixels(image)
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
