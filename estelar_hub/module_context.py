"""Dependencies provided to first-party and installed Hub modules."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleContext:
    application: object
    parent: object
    settings: object
    project_manager: object
    processing_service: object
    logger: object
    error_service: object = None
    update_service: object = None
