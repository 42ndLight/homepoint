from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Sync user groups from user.role. Use --dry-run to preview changes."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show changes without applying.')
        parser.add_argument('--batch', type=int, default=0, help='Process only N users (for testing).')

    def handle(self, *args, **options):
        User = get_user_model()
        role_to_group = {
            'staff': 'Warehouse Staff',
            'admin': 'Warehouse Staff',
            'fundi': 'Fundi',
            'customer': 'Customer',
        }

        dry_run = options.get('dry_run', False)
        batch = options.get('batch', 0)

        qs = User.objects.all().order_by('pk')
        if batch > 0:
            qs = qs[:batch]

        added = 0
        removed = 0

        for user in qs:
            target_group_name = role_to_group.get(getattr(user, 'role', None))
            if not target_group_name:
                continue

            group, _ = Group.objects.get_or_create(name=target_group_name)

            if not user.groups.filter(pk=group.pk).exists():
                if dry_run:
                    self.stdout.write(f"[DRY] Would add {user.username} -> {group.name}")
                else:
                    user.groups.add(group)
                    added += 1
                    self.stdout.write(f"Added {user.username} -> {group.name}")

            # Remove other role-related groups to keep membership consistent
            other_group_names = [n for n in set(role_to_group.values()) if n != target_group_name]
            other_groups = Group.objects.filter(name__in=other_group_names)
            for og in other_groups:
                if user.groups.filter(pk=og.pk).exists():
                    if dry_run:
                        self.stdout.write(f"[DRY] Would remove {og.name} from {user.username}")
                    else:
                        user.groups.remove(og)
                        removed += 1
                        self.stdout.write(f"Removed {og.name} from {user.username}")

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run complete. No changes applied.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Sync complete. Added: {added}, Removed: {removed}'))
