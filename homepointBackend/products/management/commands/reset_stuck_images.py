from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from products.models import ProductImage, VariantImage


class Command(BaseCommand):
    help = "Resets image records stuck in 'processing' status back to 'pending' or 'failed'."

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=15,
            help="Stuck threshold in minutes (default: 15)",
        )
        parser.add_argument(
            "--mark-failed",
            action="store_true",
            help="Mark stuck images as 'failed' instead of resetting them to 'pending'",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate the reset process without making database modifications",
        )

    def handle(self, *args, **options):
        minutes = options["minutes"]
        mark_failed = options["mark_failed"]
        dry_run = options["dry_run"]

        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        target_status = "failed" if mark_failed else "pending"

        models = [("ProductImage", ProductImage), ("VariantImage", VariantImage)]
        total_updated = 0

        self.stdout.write(
            self.style.NOTICE(
                f"Scanning for images stuck in 'processing' before {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} UTC..."
            )
        )

        for model_name, model_class in models:
            # Filter objects stuck in processing past the cutoff time
            stuck_qs = model_class.objects.filter(
                optimization_status="processing",
                updated_at__lt=cutoff_time,  # Assuming 'updated_at' or 'last_optimized_at' tracks changes
            )

            count = stuck_qs.count()

            if count == 0:
                self.stdout.write(f"No stuck {model_name} records found.")
                continue

            self.stdout.write(
                self.style.WARNING(f"Found {count} stuck {model_name} records.")
            )

            if dry_run:
                self.stdout.write(
                    self.style.NOTICE(
                        f"[DRY RUN] Would set {count} {model_name} records to '{target_status}'."
                    )
                )
            else:
                update_fields = {"optimization_status": target_status}
                if mark_failed:
                    update_fields["error_log"] = (
                        f"Stuck in processing for over {minutes} minutes. Marked failed by cleanup command."
                    )

                updated_count = stuck_qs.update(**update_fields)
                total_updated += updated_count

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully updated {updated_count} {model_name} records to '{target_status}'."
                    )
                )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS("Dry run complete. No database changes were made.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Cleanup complete. Total records updated: {total_updated}"
                )
            )