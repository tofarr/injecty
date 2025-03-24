"""
Tests for configuration module validation.
"""

import importlib.util
import sys
from types import ModuleType
from typing import Any

import pytest

from injecty import InjectyContext, validate_config_module


def create_mock_module(
    name: str,
    priority: Any = 0,
    configure_func: Any = None,
) -> ModuleType:
    """Create a mock module for testing."""
    spec = importlib.util.find_spec("types")
    module = importlib.util.module_from_spec(spec)
    module.__name__ = name
    
    if priority is not None:
        module.priority = priority
        
    if configure_func is not None:
        module.configure = configure_func
    
    return module


def test_validate_valid_module():
    """Test validation of a valid configuration module."""
    def configure(context: InjectyContext):
        pass
    
    module = create_mock_module("valid_module", priority=0, configure_func=configure)
    
    # Should not raise any exceptions
    validate_config_module(module)


def test_validate_missing_priority():
    """Test validation of a module missing the priority attribute."""
    def configure(context: InjectyContext):
        pass
    
    module = create_mock_module("missing_priority", priority=None, configure_func=configure)
    
    with pytest.raises(AttributeError) as excinfo:
        validate_config_module(module)
    
    assert "missing required 'priority' attribute" in str(excinfo.value)


def test_validate_invalid_priority_type():
    """Test validation of a module with an invalid priority type."""
    def configure(context: InjectyContext):
        pass
    
    module = create_mock_module("invalid_priority", priority="not_an_int", configure_func=configure)
    
    with pytest.raises(TypeError) as excinfo:
        validate_config_module(module)
    
    assert "invalid 'priority' attribute: expected int" in str(excinfo.value)


def test_validate_missing_configure():
    """Test validation of a module missing the configure method."""
    module = create_mock_module("missing_configure", priority=0, configure_func=None)
    
    with pytest.raises(AttributeError) as excinfo:
        validate_config_module(module)
    
    assert "missing required 'configure' method" in str(excinfo.value)


def test_validate_non_callable_configure():
    """Test validation of a module with a non-callable configure attribute."""
    module = create_mock_module("non_callable_configure", priority=0, configure_func="not_callable")
    
    with pytest.raises(TypeError) as excinfo:
        validate_config_module(module)
    
    assert "invalid 'configure' attribute: expected callable" in str(excinfo.value)


def test_validate_configure_no_parameters():
    """Test validation of a module with a configure method that takes no parameters."""
    def configure():
        pass
    
    module = create_mock_module("no_params_configure", priority=0, configure_func=configure)
    
    with pytest.raises(ValueError) as excinfo:
        validate_config_module(module)
    
    assert "invalid 'configure' method: expected at least 1 parameter" in str(excinfo.value)


def test_validate_configure_unusual_parameter_name():
    """Test validation of a module with a configure method that has an unusual parameter name."""
    def configure(unusual_name):
        pass
    
    module = create_mock_module("unusual_param_name", priority=0, configure_func=configure)
    
    # This should not raise an exception, but should log a warning
    validate_config_module(module)