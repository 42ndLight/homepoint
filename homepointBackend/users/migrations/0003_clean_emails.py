"""Data migration: normalize empty emails and deduplicate existing emails.

This migration will:
- Replace empty string or NULL emails with a unique placeholder per user
  (user{pk}@local.invalid).
- For duplicate non-empty emails, it will keep the first record and
  append "+{pk}" to subsequent ones to make them unique.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model('users', 'User')
    from django.db.models import Count

    # Replace empty strings and NULLs with unique placeholders
    empties = User.objects.filter(email__in=['', None])
    for u in empties:
        u.email = f'user{u.id}@local.invalid'
        u.save(update_fields=['email'])

    # Find duplicates and uniquify all but the first
    dupes = (
        User.objects.values('email')
        .annotate(c=Count('id'))
        .filter(c__gt=1)
    )
    for d in dupes:
        email = d['email']
        users = list(User.objects.filter(email=email).order_by('id'))
        for u in users[1:]:
            local = email.split('@')[0] if '@' in email else f'user{u.id}'
            u.email = f"{local}+{u.id}@local.invalid"
            u.save(update_fields=['email'])


def reverse(apps, schema_editor):
    # Non-destructive forward; no safe reverse
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_email_nullable'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse),
    ]
