"""Application settings shared by the Hub and its modules."""

from qgis.PyQt.QtCore import QSettings


class SettingsService:
    def __init__(self, settings=None):
        self._settings = settings if settings is not None else QSettings()

    def value(self, key, default=None, type=None):
        if type is None:
            return self._settings.value(key, default)
        return self._settings.value(key, default, type=type)

    def set_value(self, key, value):
        self._settings.setValue(key, value)

    def setValue(self, key, value):
        self.set_value(key, value)

    def remove(self, key):
        self._settings.remove(key)

    def sync(self):
        self._settings.sync()