"""Lifecycle manager for the embedded PyQGIS engine."""


class QgisRuntime:
    def __init__(self, prefix_path):
        self.prefix_path = str(prefix_path)
        self.application = None
        self.initialized = False
        self.processing_available = False
        self.processing_error = None

    def start(self):
        if self.application is not None:
            return self.application

        from qgis.core import QgsApplication

        QgsApplication.setPrefixPath(self.prefix_path, True)
        self.application = QgsApplication([], True)
        self.application.setOrganizationName("Estelar Engenharia")
        self.application.setOrganizationDomain("estelarengenharia.com.br")
        self.application.setApplicationName("Estelar Hub")
        self.application.initQgis()
        self.initialized = True
        self._initialize_processing()
        return self.application

    def _initialize_processing(self):
        try:
            from processing.core.Processing import Processing

            Processing.initialize()
            self.processing_available = True
        except Exception as error:
            self.processing_error = error
            self.processing_available = False

    def stop(self):
        if self.application is None:
            return
        if self.initialized:
            self.application.exitQgis()
            self.initialized = False
        self.application = None