"""Background execution service for QGIS Processing algorithms."""

from qgis.core import (
    QgsApplication,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProject,
)


class ProcessingService:
    def __init__(self):
        self._task_resources = {}

    def run_async(self, algorithm_id, parameters, on_finished=None, context=None, feedback=None):
        """Run one registered Processing algorithm as a cancellable QgsTask."""
        registry = QgsApplication.processingRegistry()
        algorithm = registry.algorithmById(algorithm_id)
        if algorithm is None:
            raise KeyError(f"Algoritmo de processamento não registrado: {algorithm_id}")

        processing_context = context or QgsProcessingContext()
        if context is None:
            processing_context.setProject(QgsProject.instance())
        processing_feedback = feedback or QgsProcessingFeedback()

        task = QgsProcessingAlgRunnerTask(
            algorithm,
            parameters,
            processing_context,
            processing_feedback,
        )
        task_key = id(task)
        self._task_resources[task_key] = (processing_context, processing_feedback)

        def notify_finished(successful, results):
            try:
                if on_finished is not None:
                    on_finished(successful, results)
            finally:
                self._task_resources.pop(task_key, None)

        task.executed.connect(notify_finished)

        QgsApplication.taskManager().addTask(task)
        return task