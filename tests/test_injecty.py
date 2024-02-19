from unittest import TestCase

from injecty import get_impls, get_instances, get_default_impl, get_new_default_instance
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

    def test_get_new_default_instance(self):
        instance = get_new_default_instance(Foo)
        self.assertIsInstance(instance, Bang)
