from django.core.management.base import BaseCommand

from marketplace.services import generate_weekly_settlements


class Command(BaseCommand):
    help = "Generate auditable settlement records for delivered supplier orders in the current seven-day period."

    def handle(self, *args, **options):
        settlements = generate_weekly_settlements()
        self.stdout.write(self.style.SUCCESS(f"Generated or updated {len(settlements)} settlement record(s)."))
