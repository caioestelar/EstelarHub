# -*- coding: utf-8 -*-
"""Custom pointer cursor shared by EstelarMapTools windows."""

from collections import deque
import os

from qgis.PyQt.QtCore import QPoint, QSize, Qt
from qgis.PyQt.QtGui import QColor, QCursor, QImage, QPainter, QPainterPath, QPen, QPixmap


_CURSOR_SIZE = QSize(20, 20)
_CURSOR_HOTSPOT = QPoint(1, 1)
_MAP_CURSOR_SIZE = QSize(36, 36)
_MAP_POINTER_SIZE = QSize(27, 27)
_MAP_BADGE_POSITION = (23, 23, 12, 12)
_PAN_CURSOR_SIZE = QSize(32, 32)
_PAN_CURSOR_HOTSPOT = QPoint(16, 16)
_PAN_TRANSITION_SIZE = QSize(40, 40)
_PAN_TRANSITION_HOTSPOT = QPoint(20, 20)
_PAN_TRANSITION_FRAME_COUNT = 8
_PAN_CURSOR_DARK = QColor("#111112")
_PAN_CURSOR_FILL = QColor("#58ACC3")
_PAN_CURSOR_ACCENT = QColor("#F36A26")
_BACKGROUND_CHANNEL_MIN = 232
_BACKGROUND_CHANNEL_SPREAD_MAX = 30
_CACHED_CURSOR = None
_CACHED_CURSOR_IMAGE = None
_CACHED_MAP_CURSORS = {}
_CACHED_PAN_CURSOR = None
_CACHED_PAN_TRANSITION = None


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


def cursor_estelar_mover_mapa() -> QCursor:
    """Return a clean four-arrow Estelar cursor for panning the map."""
    global _CACHED_PAN_CURSOR
    if _CACHED_PAN_CURSOR is not None:
        return QCursor(_CACHED_PAN_CURSOR)

    pixmap = QPixmap(_PAN_CURSOR_SIZE)
    pixmap.fill(Qt.GlobalColor.transparent)

    arrow = QPainterPath()
    arrow.moveTo(16, 4)
    arrow.lineTo(21, 9)
    arrow.lineTo(18, 9)
    arrow.lineTo(18, 14)
    arrow.lineTo(14, 14)
    arrow.lineTo(14, 9)
    arrow.lineTo(11, 9)
    arrow.closeSubpath()

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(
        QPen(
            _PAN_CURSOR_DARK,
            1.25,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    painter.setBrush(_PAN_CURSOR_FILL)
    for rotation in (0, 90, 180, 270):
        painter.save()
        painter.translate(16, 16)
        painter.rotate(rotation)
        painter.translate(-16, -16)
        painter.drawPath(arrow)
        painter.restore()

    centro = QPainterPath()
    centro.moveTo(16, 13.5)
    centro.lineTo(18.5, 16)
    centro.lineTo(16, 18.5)
    centro.lineTo(13.5, 16)
    centro.closeSubpath()
    painter.setPen(QPen(_PAN_CURSOR_DARK, 0.9))
    painter.setBrush(_PAN_CURSOR_ACCENT)
    painter.drawPath(centro)
    painter.end()

    _CACHED_PAN_CURSOR = QCursor(
        pixmap,
        _PAN_CURSOR_HOTSPOT.x(),
        _PAN_CURSOR_HOTSPOT.y(),
    )
    return QCursor(_CACHED_PAN_CURSOR)


def cursor_estelar_transicao_pan() -> tuple[QCursor, ...]:
    """Build cached frames that morph the pointer into the pan glyph."""
    global _CACHED_PAN_TRANSITION
    if _CACHED_PAN_TRANSITION is not None:
        return tuple(QCursor(frame) for frame in _CACHED_PAN_TRANSITION)

    pointer = QPixmap.fromImage(_imagem_estelar()).scaled(
        _CURSOR_SIZE,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    glyph = cursor_estelar_mover_mapa().pixmap()
    frames = []

    for frame_index in range(_PAN_TRANSITION_FRAME_COUNT):
        raw_progress = frame_index / (_PAN_TRANSITION_FRAME_COUNT - 1)
        progress = raw_progress * raw_progress * (3.0 - 2.0 * raw_progress)
        frame_pixmap = QPixmap(_PAN_TRANSITION_SIZE)
        frame_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(frame_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pointer_size = max(8, round(_CURSOR_SIZE.width() * (1.0 - 0.4 * progress)))
        pointer_frame = pointer.scaled(
            QSize(pointer_size, pointer_size),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        hotspot = QPoint(
            round(_CURSOR_HOTSPOT.x() * pointer_frame.width() / max(pointer.width(), 1)),
            round(_CURSOR_HOTSPOT.y() * pointer_frame.height() / max(pointer.height(), 1)),
        )
        painter.setOpacity(1.0 - progress)
        painter.drawPixmap(
            _PAN_TRANSITION_HOTSPOT.x() - hotspot.x(),
            _PAN_TRANSITION_HOTSPOT.y() - hotspot.y(),
            pointer_frame,
        )

        glyph_size = max(1, round(_PAN_CURSOR_SIZE.width() * progress))
        glyph_frame = glyph.scaled(
            QSize(glyph_size, glyph_size),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.setOpacity(progress)
        painter.drawPixmap(
            _PAN_TRANSITION_HOTSPOT.x() - glyph_frame.width() // 2,
            _PAN_TRANSITION_HOTSPOT.y() - glyph_frame.height() // 2,
            glyph_frame,
        )
        painter.end()

        frames.append(
            QCursor(
                frame_pixmap,
                _PAN_TRANSITION_HOTSPOT.x(),
                _PAN_TRANSITION_HOTSPOT.y(),
            )
        )

    _CACHED_PAN_TRANSITION = tuple(frames)
    return tuple(QCursor(frame) for frame in _CACHED_PAN_TRANSITION)
