from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Initialize the non-sensitive default data required by L-Test."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite-components",
            action="store_true",
            help="Update component definitions and remove stale components.",
        )
        parser.add_argument(
            "--skip-locator-strategies",
            action="store_true",
            help="Do not initialize UI automation locator strategies.",
        )
        parser.add_argument(
            "--skip-components",
            action="store_true",
            help="Do not load the APP automation component pack.",
        )

    def handle(self, *args, **options):
        self.stdout.write("Initializing L-Test default data...")

        if not options["skip_locator_strategies"]:
            call_command(
                "init_locator_strategies",
                stdout=self.stdout,
                stderr=self.stderr,
            )

        if not options["skip_components"]:
            call_command(
                "load_component_pack",
                overwrite=options["overwrite_components"],
                stdout=self.stdout,
                stderr=self.stderr,
            )

        self.stdout.write(self.style.SUCCESS("L-Test default data is ready."))
