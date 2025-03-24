"""
Tests for error handling in the injecty module.
"""

import importlib
from types import ModuleType
from unittest.mock import patch, MagicMock, create_autospec

import pytest

from injecty.injecty_context import InjectyContext, create_injecty_context


class TestInstanceCreationErrors:
    """Tests for error handling during instance creation."""
    
    def test_get_instances_error(self):
        """Test error handling in InjectyContext.get_instances."""
        # Create a context with a mock implementation that raises an exception
        context = InjectyContext()
        
        # Create a mock class that raises an exception when instantiated
        class ErrorClass:
            def __init__(self):
                raise RuntimeError("Test error")
        
        # Register the mock class
        context.register_impl(object, ErrorClass)
        
        # Attempt to create instances should raise the exception
        with pytest.raises(RuntimeError, match="Test error"):
            context.get_instances(object)
    
    def test_get_new_default_instance_error(self):
        """Test error handling in InjectyContext.get_new_default_instance."""
        # Create a context with a mock implementation that raises an exception
        context = InjectyContext()
        
        # Create a mock class that raises an exception when instantiated
        class ErrorClass:
            def __init__(self):
                raise ValueError("Test error")
        
        # Register the mock class
        context.register_impl(object, ErrorClass)
        
        # Attempt to create an instance should raise the exception
        with pytest.raises(ValueError, match="Test error"):
            context.get_new_default_instance(object)


class TestConfigModuleErrors:
    """Tests for error handling during configuration module loading and processing."""
    
    def test_import_module_error(self):
        """Test error handling when a module cannot be imported."""
        # Create a custom module finder that will be returned by pkgutil.iter_modules
        class MockModuleFinder:
            def __init__(self, name):
                self.name = name
        
        mock_finder = MockModuleFinder("injecty_config_nonexistent")
        
        # Patch pkgutil.iter_modules to return our mock finder
        with patch('pkgutil.iter_modules', return_value=[mock_finder]):
            # Patch importlib.import_module to raise ImportError
            with patch('importlib.import_module', side_effect=ImportError("Test import error")):
                # This should raise the ImportError
                from injecty.injecty_context import get_config_modules
                with pytest.raises(ImportError, match="Test import error"):
                    get_config_modules()
    
    def test_configure_module_error(self):
        """Test error handling when a module's configure method raises an exception."""
        # Create a module with a configure method that raises an exception
        class TestModule:
            priority = 0
            
            @staticmethod
            def configure(context):
                raise RuntimeError("Test configure error")
        
        # Mock get_config_modules to return our test module
        with patch('injecty.injecty_context.get_config_modules', return_value=[TestModule]):
            with pytest.raises(RuntimeError, match="Test configure error"):
                create_injecty_context()
    
    def test_configure_returns_value(self):
        """Test warning when a module's configure method returns a value."""
        # Create a module with a configure method that returns a value
        class TestModule:
            priority = 0
            
            @staticmethod
            def configure(context):
                return "unexpected return value"
        
        # Mock get_config_modules to return our test module
        with patch('injecty.injecty_context.get_config_modules', return_value=[TestModule]):
            # This should not raise an exception, but should log a warning
            with patch('injecty.injecty_context.logger') as mock_logger:
                context = create_injecty_context()
                assert isinstance(context, InjectyContext)
                
                # Verify that a warning was logged
                mock_logger.warning.assert_called_once()