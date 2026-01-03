from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("token_blacklist", "0013_alter_blacklistedtoken_options_and_more"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'token_blacklist_outs_user_id_83bc629a_fk_auth_user') THEN
    ALTER TABLE token_blacklist_outstandingtoken DROP CONSTRAINT token_blacklist_outs_user_id_83bc629a_fk_auth_user;
  END IF;
  ALTER TABLE token_blacklist_outstandingtoken
    ADD CONSTRAINT token_blacklist_outs_user_id_fk_users_user FOREIGN KEY (user_id)
    REFERENCES users_user(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
END
$$;
""",
            reverse_sql="""
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'token_blacklist_outs_user_id_fk_users_user') THEN
    ALTER TABLE token_blacklist_outstandingtoken DROP CONSTRAINT token_blacklist_outs_user_id_fk_users_user;
  END IF;
  ALTER TABLE token_blacklist_outstandingtoken
    ADD CONSTRAINT token_blacklist_outs_user_id_83bc629a_fk_auth_user FOREIGN KEY (user_id)
    REFERENCES auth_user(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
END
$$;
""",
        ),
    ]
