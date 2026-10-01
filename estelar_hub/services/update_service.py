"""Asynchronous GitHub release checks; downloads are never executed silently."""

import json
import re
import os
from pathlib import Path

from qgis.PyQt.QtCore import QObject, QStandardPaths, QUrl, pyqtSignal
from qgis.PyQt.QtNetwork import QNetworkAccessManager, QNetworkRequest


class UpdateService(QObject):
    update_available = pyqtSignal(dict)
    up_to_date = pyqtSignal(dict)
    check_failed = pyqtSignal(str)
    installer_downloaded = pyqtSignal(str)

    def __init__(self, repository="caioestelar/EstelarMapTools", parent=None):
        super().__init__(parent)
        self.repository = repository
        self.network = QNetworkAccessManager(self)
        self._pending_replies = set()
        self._download_replies = {}

    def check_for_updates(self, current_version):
        request = QNetworkRequest(QUrl(f"https://api.github.com/repos/{self.repository}/releases/latest"))
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        request.setRawHeader(b"User-Agent", b"Estelar-Hub")
        reply = self.network.get(request)
        self._pending_replies.add(reply)
        reply.finished.connect(lambda active_reply=reply, current=current_version: self._handle_reply(active_reply, current))
        return reply

    def _handle_reply(self, reply, current_version):
        self._pending_replies.discard(reply)
        try:
            if reply.error():
                self.check_failed.emit(reply.errorString())
                return

            release = json.loads(bytes(reply.readAll()).decode("utf-8"))
            latest_version = release.get("tag_name", "").lstrip("vV")
            information = {
                "version": latest_version,
                "name": release.get("name") or latest_version,
                "url": release.get("html_url", ""),
                "notes": release.get("body", ""),
                "assets": release.get("assets", []),
            }
            if self._version_tuple(latest_version) > self._version_tuple(current_version):
                self.update_available.emit(information)
            else:
                self.up_to_date.emit(information)
        except Exception as error:
            self.check_failed.emit(str(error))
        finally:
            reply.deleteLater()

    def download_installer(self, release):
        assets = release.get("assets", [])
        installer = next((asset for asset in assets if asset.get("name", "").lower() == "estelarhubsetup.exe"), None)
        if installer is None:
            self.check_failed.emit("A release mais recente ainda não publicou o instalador EstelarHubSetup.exe.")
            return None

        request = QNetworkRequest(QUrl(installer["browser_download_url"]))
        request.setRawHeader(b"User-Agent", b"Estelar-Hub")
        reply = self.network.get(request)
        self._pending_replies.add(reply)
        self._download_replies[reply] = installer["name"]
        reply.finished.connect(lambda active_reply=reply: self._save_installer(active_reply))
        return reply

    def _save_installer(self, reply):
        filename = self._download_replies.pop(reply, "EstelarHubSetup.exe")
        self._pending_replies.discard(reply)
        try:
            if reply.error():
                self.check_failed.emit(reply.errorString())
                return

            temp_directory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.TempLocation)
            download_directory = Path(temp_directory) / "EstelarHub" / "updates"
            download_directory.mkdir(parents=True, exist_ok=True)
            installer_path = download_directory / filename
            installer_path.write_bytes(bytes(reply.readAll()))
            self.installer_downloaded.emit(str(installer_path))
        except Exception as error:
            self.check_failed.emit(str(error))
        finally:
            reply.deleteLater()

    @staticmethod
    def _version_tuple(value):
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?", str(value or "").strip())
        if not match:
            return (0, 0, 0, 0, ())
        major, minor, patch = (int(match.group(index)) for index in (1, 2, 3))
        prerelease = match.group(4)
        if prerelease is None:
            return major, minor, patch, 1, ()
        tokens = tuple(
            (0, int(token)) if token.isdigit() else (1, token.casefold())
            for token in prerelease.split(".")
        )
        return major, minor, patch, 0, tokens