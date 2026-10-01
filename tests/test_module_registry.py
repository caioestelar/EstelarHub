import json
import tempfile
import unittest
from pathlib import Path

from core.module_registry import ModuleDefinition, ModuleRegistry


class ModuleRegistryTests(unittest.TestCase):
    def test_discovers_manifest_and_loads_entry_point_only_on_launch(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            module_root = Path(temporary_directory) / "coordinate-tool"
            module_root.mkdir()
            (module_root / "module_entry.py").write_text(
                "def launch(context):\n    return {'module': 'coordinate-tool', 'context': context}\n",
                encoding="utf-8",
            )
            manifest = {
                "schema_version": 1,
                "id": "coordinate-tool-test",
                "name": "Coordinate Tool Test",
                "version": "1.2.0",
                "description": "Test extension module",
                "entry_point": "module_entry:launch",
            }
            (module_root / "estelar-module.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )

            registry = ModuleRegistry((
                ModuleDefinition(
                    "coordinate-tool-test",
                    "Coordinate Tool Test",
                    "Upcoming catalog item",
                    "convert",
                    "Coordenadas",
                    "upcoming",
                ),
            ))

            self.assertFalse(registry.discover_manifests((Path(temporary_directory),)))
            self.assertTrue(registry.can_launch("coordinate-tool-test"))
            context = object()
            result = registry.launch("coordinate-tool-test", context)

            self.assertEqual(result["module"], "coordinate-tool")
            self.assertIs(result["context"], context)
            self.assertEqual(registry.get("coordinate-tool-test").version, "1.2.0")

    def test_rejects_entry_point_path_traversal(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            module_root = Path(temporary_directory) / "invalid-tool"
            module_root.mkdir()
            (module_root / "estelar-module.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "id": "invalid-tool",
                    "name": "Invalid Tool",
                    "version": "1.0.0",
                    "entry_point": "..\\outside:launch",
                }),
                encoding="utf-8",
            )
            registry = ModuleRegistry()

            errors = registry.discover_manifests((Path(temporary_directory),))

            self.assertEqual(len(errors), 1)
            self.assertFalse(registry.can_launch("invalid-tool"))


if __name__ == "__main__":
    unittest.main()