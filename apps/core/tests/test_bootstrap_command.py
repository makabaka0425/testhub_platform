from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase


class BootstrapCommandTests(SimpleTestCase):
    @mock.patch("apps.core.management.commands.bootstrap.call_command")
    def test_runs_all_initializers_by_default(self, initializer):
        call_command("bootstrap", stdout=StringIO())

        self.assertEqual(initializer.call_count, 2)
        self.assertEqual(initializer.call_args_list[0].args[0], "init_locator_strategies")
        self.assertEqual(initializer.call_args_list[1].args[0], "load_component_pack")
        self.assertFalse(initializer.call_args_list[1].kwargs["overwrite"])

    @mock.patch("apps.core.management.commands.bootstrap.call_command")
    def test_supports_skipping_initializers(self, initializer):
        call_command(
            "bootstrap",
            skip_locator_strategies=True,
            skip_components=True,
            stdout=StringIO(),
        )

        initializer.assert_not_called()

    @mock.patch("apps.core.management.commands.bootstrap.call_command")
    def test_can_overwrite_components(self, initializer):
        call_command(
            "bootstrap",
            skip_locator_strategies=True,
            overwrite_components=True,
            stdout=StringIO(),
        )

        self.assertEqual(initializer.call_count, 1)
        self.assertEqual(initializer.call_args.args[0], "load_component_pack")
        self.assertTrue(initializer.call_args.kwargs["overwrite"])
