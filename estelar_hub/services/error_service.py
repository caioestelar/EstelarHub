"""Central exception hooks and user-facing error reporting."""

import sys
import threading
import traceback

from qgis.PyQt.QtWidgets import QMessageBox


class ErrorService:
    def __init__(self, logger):
        self.logger = logger
        self._previous_exception_hook = None
        self._previous_thread_hook = None

    def install(self):
        if self._previous_exception_hook is not None:
            return
        self._previous_exception_hook = sys.excepthook
        self._previous_thread_hook = threading.excepthook

        def handle_exception(exception_type, exception, trace):
            self.logger.critical(
                "Unhandled application exception",
                exc_info=(exception_type, exception, trace),
            )
            self._previous_exception_hook(exception_type, exception, trace)

        def handle_thread_exception(args):
            self.logger.critical(
                "Unhandled exception in worker thread %s",
                args.thread.name if args.thread else "unknown",
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )

        sys.excepthook = handle_exception
        threading.excepthook = handle_thread_exception

    def restore(self):
        if self._previous_exception_hook is None:
            return
        sys.excepthook = self._previous_exception_hook
        threading.excepthook = self._previous_thread_hook
        self._previous_exception_hook = None
        self._previous_thread_hook = None

    def report(self, parent, title, message, exception=None):
        if exception is not None:
            self.logger.error(
                "%s: %s",
                title,
                message,
                exc_info=(type(exception), exception, exception.__traceback__),
            )
        else:
            self.logger.error("%s: %s", title, message)
        QMessageBox.critical(parent, title, message)

    def log_traceback(self, title, exception):
        self.logger.error("%s", title)
        self.logger.error("%s", "".join(traceback.format_exception(exception)))