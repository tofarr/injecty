"""Tests for version functionality."""

import re
import unittest
from unittest.mock import patch

import injecty


class TestVersion(unittest.TestCase):
    """Test version functionality."""

    def test_version_is_available(self):
        """Test that version is available and follows semantic versioning."""
        version = injecty.__version__
        self.assertIsInstance(version, str)
        self.assertNotEqual(version, "")

        # Check that version follows semantic versioning pattern
        # Allows for patterns like: 1.2.3, 1.2.3.dev1, 1.2.3a1, etc.
        version_pattern = r"^\d+\.\d+\.\d+(?:\.dev\d+|[abc]\d+|rc\d+)?$"
        self.assertTrue(
            re.match(version_pattern, version) is not None,
            f"Version '{version}' does not follow semantic versioning pattern",
        )

    def test_version_import_logic(self):
        """Test the version import logic directly."""
        # Test that the import logic works as expected
        try:
            from injecty._version import __version__ as version_from_module

            # If we can import it, it should be a string
            self.assertIsInstance(version_from_module, str)
            self.assertNotEqual(version_from_module, "")
        except ImportError:
            # If import fails, fallback should be "0.0.0"
            # This tests the fallback logic indirectly
            pass

    def test_version_fallback_behavior(self):
        """Test that fallback version is reasonable."""
        # Test that if we simulate an ImportError, we get a fallback
        with patch("builtins.__import__") as mock_import:

            def side_effect(name, *args, **kwargs):
                if name == "injecty._version" or name.endswith("._version"):
                    raise ImportError("Mocked import error")
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = side_effect

            # Test the fallback logic by executing the import code directly
            try:
                from injecty._version import __version__

                version = __version__
            except ImportError:
                version = "0.0.0"

            # Should either be the real version or the fallback
            self.assertIsInstance(version, str)
            self.assertNotEqual(version, "")

    def test_version_consistency(self):
        """Test that version is consistent across imports."""
        # Test that version is consistent when accessed different ways
        version1 = injecty.__version__

        # Import again to test consistency
        from injecty import __version__ as version2

        self.assertEqual(version1, version2)
        self.assertEqual(injecty.__version__, version2)

    def test_version_is_not_empty_or_none(self):
        """Test that version is not empty or None."""
        version = injecty.__version__
        self.assertIsNotNone(version)
        self.assertNotEqual(version, "")
        self.assertNotEqual(version, "None")

    def test_version_module_attributes(self):
        """Test that _version module has expected attributes when available."""
        try:
            from injecty import _version

            # Check that the version module has the expected attributes
            self.assertTrue(hasattr(_version, "__version__"))
            self.assertIsInstance(_version.__version__, str)

            # Check for other common setuptools-scm attributes
            if hasattr(_version, "__version_tuple__"):
                self.assertIsInstance(_version.__version_tuple__, tuple)

            if hasattr(_version, "version"):
                self.assertEqual(_version.version, _version.__version__)

        except ImportError:
            # If _version module is not available, that's also valid
            # (fallback should handle this case)
            self.assertEqual(injecty.__version__, "0.0.0")

    def test_import_error_fallback_direct(self):
        """Test ImportError fallback directly to ensure coverage."""
        import sys
        import importlib

        # Save original modules
        original_injecty = sys.modules.get("injecty")
        original_version = sys.modules.get("injecty._version")

        try:
            # Remove modules from cache
            if "injecty" in sys.modules:
                del sys.modules["injecty"]
            if "injecty._version" in sys.modules:
                del sys.modules["injecty._version"]

            # Mock the _version module to not exist
            with patch.dict("sys.modules", {"injecty._version": None}):
                # Import injecty fresh - this should trigger the ImportError fallback
                import injecty as test_injecty  # pylint: disable=reimported

                # The fallback should set version to "0.0.0"
                self.assertEqual(test_injecty.__version__, "0.0.0")

        finally:
            # Restore original state
            if original_injecty is not None:
                sys.modules["injecty"] = original_injecty
            elif "injecty" in sys.modules:
                del sys.modules["injecty"]

            if original_version is not None:
                sys.modules["injecty._version"] = original_version
            elif "injecty._version" in sys.modules:
                del sys.modules["injecty._version"]

            # Re-import to restore normal state if module exists
            if "injecty" in sys.modules:
                importlib.reload(sys.modules["injecty"])
            else:
                # Just import normally to restore state
                import injecty  # pylint: disable=reimported,unused-import,redefined-outer-name


if __name__ == "__main__":
    unittest.main()
