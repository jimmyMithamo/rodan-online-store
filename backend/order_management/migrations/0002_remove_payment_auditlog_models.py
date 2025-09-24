# Generated migration to remove models from order_management
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order_management', '0001_initial'),
    ]

    operations = [
        # Remove indexes first to avoid field reference issues
        migrations.RunSQL(
            "DROP INDEX IF EXISTS order_manag_order_i_891fd9_idx;",
            reverse_sql="",
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS order_manag_user_id_34d0e2_idx;",
            reverse_sql="",
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS order_manag_status_c86e49_idx;",
            reverse_sql="",
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS order_manag_payment_4a3f5c_idx;",
            reverse_sql="",
        ),
        # Now safely delete the models
        migrations.DeleteModel(
            name='Payment',
        ),
        migrations.DeleteModel(
            name='AuditLog',
        ),
    ]