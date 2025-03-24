from unittest import TestCase
from unittest.mock import patch, MagicMock

from injecty import get_impls, get_instances, get_default_impl, get_new_default_instance, get_default_injecty_context
from tests.models import Foo, Bang, Bar, Zap


class TestInjecty(TestCase):
    def test_get_impls(self):
        impls = get_impls(Foo)
        self.assertEqual(impls, [Bang, Bar, Zap])

    def test_get_instances(self):
        instances = [i.__class__ for i in get_instances(Foo)]
        expected = [Bang, Bar, Zap]
        self.assertEqual(instances, expected)

    def test_get_default_impl(self):
        impl = get_default_impl(Foo)
        self.assertEqual(impl, Bang)
        
    def test_get_default_impl_no_impl(self):
        # Test with a class that has no implementations
        impl = get_default_impl(str, permit_no_impl=True)
        self.assertIsNone(impl)

    def test_get_new_default_instance(self):
        instance = get_new_default_instance(Foo)
        self.assertIsInstance(instance, Bang)
        
    def test_get_new_default_instance_no_impl(self):
        # Test with a class that has no implementations
        instance = get_new_default_instance(str, permit_no_impl=True)
        self.assertIsNone(instance)
        
    def test_get_new_default_instance_error(self):
        # Test error handling in get_new_default_instance
        mock_context = MagicMock()
        mock_context.get_new_default_instance.side_effect = RuntimeError("Test error")
        
        with patch('injecty.get_default_injecty_context', return_value=mock_context):
            with self.assertRaises(RuntimeError):
                get_new_default_instance(Foo)
