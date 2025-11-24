from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wallets', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallet',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='wallets',
                to=settings.AUTH_USER_MODEL,
                db_index=True,
            ),
        ),
    ]

