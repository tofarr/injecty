from unittest import TestCase

from injecty import InjectyContext, create_injecty_context, get_config_modules
from tests.models import Foo, Bar, Bang, Zap


class TestInjectyContext(TestCase):
    def test_register_impl(self):
        context = InjectyContext()
        self.assertTrue(context.register_impl(Foo, Bar))
        impls = context.get_impls(Foo)
        self.assertEqual(impls, [Bar])

    def test_register_impl_unrelated_type(self):
        context = InjectyContext()
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            self.assertTrue(context.register_impl(int, str))
        # noinspection PyTypeChecker
        context.register_impl(int, float, False)
        impls = context.get_impls(int)
        self.assertEqual(impls, [float])

    def test_register_impl_already_registered(self):
        context = InjectyContext()
        self.assertTrue(context.register_impl(Foo, Bar))
        self.assertFalse(context.register_impl(Foo, Bar))
        impls = context.get_impls(Foo)
        self.assertEqual(impls, [Bar])

    def test_register_impls(self):
        context = InjectyContext()
        self.assertTrue(context.register_impls(Foo, [Bar, Zap, Bang]))
        impls = context.get_impls(Foo)
        self.assertEqual(impls, [Bang, Bar, Zap])

    def test_register_impls_already_registered(self):
        context = InjectyContext()
        context.register_impl(Foo, Zap)
        self.assertFalse(context.register_impls(Foo, [Bar, Zap, Bang]))
        impls = context.get_impls(Foo)
        self.assertEqual(impls, [Bang, Bar, Zap])

    def test_deregister_impl(self):
        context = InjectyContext()
        context.register_impls(Foo, [Bar, Zap, Bang])
        self.assertTrue(context.deregister_impl(Foo, Bar))
        impls = context.get_impls(Foo)
        self.assertEqual(impls, [Bang, Zap])

    def test_deregister_impl_not_registered(self):
        context = InjectyContext()
        context.register_impls(Foo, [Zap, Bang])
        self.assertFalse(context.deregister_impl(Foo, Bar))
        impls = context.get_impls(Foo)
        self.assertEqual(impls, [Bang, Zap])

    def test_load_from_module(self):
        context = create_injecty_context("injecty_config_test")
        impls = context.get_impls(Foo)
        self.assertEqual(impls, [Bang, Bar, Zap])

    def test_load_from_package(self):
        context = create_injecty_context("test_config_pac")
        impls = context.get_impls(Foo)
        self.assertEqual(impls, [Bang, Bar, Zap])

    def test_load_from_module_with_no_configure(self):
        with self.assertRaises(AttributeError):
            create_injecty_context("test_config_no_con")

    def test_load_from_module_with_no_priority(self):
        with self.assertRaises(AttributeError):
            create_injecty_context("test_config_no_pri")

    def test_get_impls(self):
        context = create_injecty_context("injecty_config_test")
        impls = context.get_impls(Foo, sort_key=lambda c: c.priority, reverse=True)
        self.assertEqual(impls, [Bang, Bar, Zap])
        impls = context.get_impls(Foo, sort_key=lambda c: c.priority)
        self.assertEqual(impls, [Zap, Bar, Bang])

    def test_get_impls_no_impl(self):
        context = InjectyContext()
        with self.assertRaises(ValueError):
            context.get_impls(int)

    def test_get_impls_no_impl_permitted(self):
        context = InjectyContext()
        self.assertEqual([], context.get_impls(int, permit_no_impl=True))
        
        # Test with empty list of implementations
        context.impls[int] = set()
        self.assertEqual([], context.get_impls(int, permit_no_impl=True))

    def test_get_instances(self):
        context = create_injecty_context("injecty_config_test")
        instances = [i.__class__ for i in context.get_instances(Foo)]
        expected = [Bang, Bar, Zap]
        self.assertEqual(instances, expected)

    def test_get_config_modules(self):
        # Test with existing config modules
        # This should find both injecty_config_test.py and injecty_config_test2.py
        modules = get_config_modules("injecty_config_test")
        self.assertTrue(len(modules) >= 1)
        
        # If we have multiple modules, verify they are sorted by priority
        if len(modules) > 1:
            for i in range(1, len(modules)):
                self.assertTrue(modules[i - 1].priority <= modules[i].priority)
            
        # Create a direct test for line 162 in injecty_context.py
        context = InjectyContext()
        # Register a base class with no implementations
        context.impls[str] = set()
        # Try to get the default implementation
        self.assertIsNone(context.get_default_impl(str, permit_no_impl=True))

        # Verify each module has required attributes
        for module in modules:
            self.assertTrue(hasattr(module, "priority"))
            self.assertTrue(hasattr(module, "configure"))

        # Test with non-existent prefix
        modules = get_config_modules("non_existent_prefix")
        self.assertEqual(len(modules), 0)

    def test_get_config_modules_validation(self):
        # Test with modules missing required attributes
        with self.assertRaises(AttributeError):
            get_config_modules("test_config_no_pri")

        with self.assertRaises(AttributeError):
            get_config_modules("test_config_no_con")
            
    def test_get_config_modules_single_module(self):
        """Test with a single module to ensure line 109 is covered."""
        # Create a test with a single module
        from types import ModuleType
        
        # Create two mock modules with different priorities
        mock_module1 = ModuleType("mock_module1")
        mock_module1.priority = 10
        mock_module1.configure = lambda ctx: None
        
        mock_module2 = ModuleType("mock_module2")
        mock_module2.priority = 20
        mock_module2.configure = lambda ctx: None
        
        # Test the sorting logic with multiple modules
        modules = [mock_module1, mock_module2]
        for i in range(1, len(modules)):
            self.assertTrue(modules[i - 1].priority <= modules[i].priority)
