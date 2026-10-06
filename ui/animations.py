# -*- coding: utf-8 -*-
"""Small, lifecycle-safe Qt animations shared by Estelar UI dialogs."""

from qgis.PyQt.QtCore import QEasingCurve, QObject, QPropertyAnimation
from qgis.PyQt.QtWidgets import QGraphicsOpacityEffect, QWidget


REDUCED_MOTION_KEY = "EstelarHub/reducedMotion"
FADE_DURATION_MS = 160


def movimento_habilitado(settings) -> bool:
    """Read the shared reduced-motion preference from QSettings-like objects."""
    try:
        return not bool(settings.value(REDUCED_MOTION_KEY, False, type=bool))
    except TypeError:
        return not bool(settings.value(REDUCED_MOTION_KEY, False))


class AnimacoesUI(QObject):
    """Runs short opacity transitions without replacing non-opacity effects."""

    def __init__(self, parent=None, enabled=True):
        super().__init__(parent)
        self.enabled = bool(enabled)
        self._animations = {}
        self._effects = {}
        self._final_states = {}

    def _opacity_effect(self, widget):
        effect = widget.graphicsEffect()
        if isinstance(effect, QGraphicsOpacityEffect):
            return effect, self._effects.get(widget) is effect
        if effect is not None:
            # A drop shadow or other effect must remain untouched.
            return None, False

        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        self._effects[widget] = effect
        return effect, True

    def fade(
        self,
        widget: QWidget,
        target_opacity: float = 1.0,
        duration_ms: int = FADE_DURATION_MS,
        start_opacity=None,
        hide_when_finished: bool = False,
    ) -> None:
        """Fade one widget; an owned opacity effect is removed at full opacity."""
        if widget is None:
            return
        target_opacity = max(0.0, min(1.0, float(target_opacity)))
        previous = self._animations.pop(widget, None)
        if previous is not None:
            previous.stop()
            previous.deleteLater()

        self._final_states[widget] = (target_opacity, bool(hide_when_finished))
        if not self.enabled or duration_ms <= 0:
            effect = widget.graphicsEffect()
            if isinstance(effect, QGraphicsOpacityEffect):
                effect.setOpacity(target_opacity)
                if self._effects.get(widget) is effect and target_opacity >= 1.0:
                    widget.setGraphicsEffect(None)
                    self._effects.pop(widget, None)
            if hide_when_finished:
                widget.hide()
            self._final_states.pop(widget, None)
            return

        effect, owned = self._opacity_effect(widget)
        if effect is None:
            if hide_when_finished:
                widget.hide()
            self._final_states.pop(widget, None)
            return

        start = effect.opacity() if start_opacity is None else float(start_opacity)
        start = max(0.0, min(1.0, start))
        effect.setOpacity(start)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(duration_ms)
        animation.setStartValue(start)
        animation.setEndValue(target_opacity)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animations[widget] = animation

        def finish(current=animation, target=target_opacity, hide=hide_when_finished):
            if self._animations.get(widget) is not current:
                return
            self._animations.pop(widget, None)
            effect.setOpacity(target)
            if hide:
                widget.hide()
            self._final_states.pop(widget, None)
            if owned and (target >= 1.0 or hide):
                if widget.graphicsEffect() is effect:
                    widget.setGraphicsEffect(None)
                self._effects.pop(widget, None)
            current.deleteLater()

        animation.finished.connect(finish)
        animation.start()

    def will_be_visible(self, widget: QWidget) -> bool:
        """Return the effective visibility, including an in-flight fade target."""
        pending = self._final_states.get(widget)
        if pending is not None:
            return not pending[1]
        return not widget.isHidden()

    def set_visible(
        self,
        widget: QWidget,
        visible: bool,
        duration_ms: int = FADE_DURATION_MS,
    ) -> None:
        """Animate a simple show/hide when the containing window is visible."""
        if widget is None:
            return
        visible = bool(visible)
        if not self.enabled or not widget.window().isVisible():
            self.fade(widget, 1.0, duration_ms=0)
            widget.setVisible(visible)
            return

        if visible:
            was_hidden = widget.isHidden()
            if was_hidden:
                widget.show()
            self.fade(
                widget,
                1.0,
                duration_ms,
                start_opacity=0.0 if was_hidden else None,
            )
        elif self.will_be_visible(widget):
            self.fade(widget, 0.0, duration_ms, hide_when_finished=True)

    def fade_window(self, window: QWidget, duration_ms: int = 180) -> None:
        """Fade a top-level window in using Qt's native window-opacity property."""
        if not self.enabled or duration_ms <= 0 or not window.isVisible():
            window.setWindowOpacity(1.0)
            return

        key = (window, "windowOpacity")
        previous = self._animations.pop(key, None)
        if previous is not None:
            previous.stop()
            previous.deleteLater()

        window.setWindowOpacity(0.0)
        animation = QPropertyAnimation(window, b"windowOpacity", self)
        animation.setDuration(duration_ms)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animations[key] = animation

        def finish(current=animation):
            if self._animations.get(key) is current:
                self._animations.pop(key, None)
                window.setWindowOpacity(1.0)
            current.deleteLater()

        animation.finished.connect(finish)
        animation.start()

    def stop_all(self) -> None:
        """Stop animations and synchronously apply each pending final state."""
        for key, animation in tuple(self._animations.items()):
            animation.stop()
            animation.deleteLater()
            if isinstance(key, tuple) and len(key) == 2 and key[1] == "windowOpacity":
                key[0].setWindowOpacity(1.0)
        self._animations.clear()

        for widget, (opacity, hide) in tuple(self._final_states.items()):
            effect = widget.graphicsEffect()
            if isinstance(effect, QGraphicsOpacityEffect):
                effect.setOpacity(opacity)
            if hide:
                widget.hide()
        self._final_states.clear()

        for widget, effect in tuple(self._effects.items()):
            if widget.graphicsEffect() is effect:
                widget.setGraphicsEffect(None)
        self._effects.clear()
