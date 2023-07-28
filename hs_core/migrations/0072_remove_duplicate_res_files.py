from django.db import migrations
from django.core.management import call_command

def migrate_resourcefiles(apps, schema_editor):
    call_command('fix_resourcefile_duplicates')

class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0071_alter_date_type'),
    ]

    operations = [
        migrations.RunPython(migrate_resourcefiles),
    ]
