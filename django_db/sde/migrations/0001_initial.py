# Generated by Django 2.1.1 on 2018-09-30 00:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeCategory',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, null=True)),
                ('description', models.CharField(max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AttributeType',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=400)),
                ('description', models.CharField(max_length=1000, null=True)),
                ('icon_id', models.IntegerField(null=True)),
                ('default_value', models.IntegerField(null=True)),
                ('published', models.BooleanField(db_index=True)),
                ('display_name', models.CharField(max_length=150, null=True)),
                ('unit_id', models.IntegerField(null=True)),
                ('stackable', models.BooleanField()),
                ('high_is_good', models.BooleanField()),
                ('category', models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='types', to='sde.AttributeCategory')),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('icon_id', models.IntegerField(null=True)),
                ('published', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Constellation',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('x', models.FloatField()),
                ('y', models.FloatField()),
                ('z', models.FloatField()),
                ('radius', models.FloatField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('icon_id', models.IntegerField(null=True)),
                ('anchored', models.BooleanField()),
                ('anchorable', models.BooleanField()),
                ('fittable_non_singleton', models.BooleanField()),
                ('published', models.BooleanField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sde.Category')),
            ],
        ),
        migrations.CreateModel(
            name='MarketGroup',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(null=True)),
                ('icon_id', models.IntegerField(null=True)),
                ('has_types', models.BooleanField()),
                ('parent', models.ForeignKey(db_constraint=False, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='sde.MarketGroup')),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('x', models.FloatField()),
                ('y', models.FloatField()),
                ('z', models.FloatField()),
                ('radius', models.FloatField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('x', models.FloatField(default=0)),
                ('y', models.FloatField(default=0)),
                ('z', models.FloatField(default=0)),
                ('structure', models.BooleanField(default=False)),
                ('last_updated', models.DateTimeField(auto_now=True, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='System',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('x', models.FloatField()),
                ('y', models.FloatField()),
                ('z', models.FloatField()),
                ('luminosity', models.FloatField()),
                ('border', models.BooleanField()),
                ('fringe', models.BooleanField()),
                ('corridor', models.BooleanField()),
                ('hub', models.BooleanField()),
                ('international', models.BooleanField()),
                ('security', models.FloatField()),
                ('radius', models.FloatField(null=True)),
                ('security_class', models.CharField(max_length=2, null=True)),
                ('constellation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='systems', to='sde.Constellation')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='systems', to='sde.Region')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('description', models.TextField()),
                ('mass', models.FloatField(null=True)),
                ('volume', models.FloatField(null=True)),
                ('capacity', models.FloatField(null=True)),
                ('published', models.BooleanField()),
                ('icon_id', models.IntegerField(null=True)),
                ('buy', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('sell', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('group', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='sde.Group')),
                ('market_group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='sde.MarketGroup')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='TypeAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value_int', models.IntegerField(null=True)),
                ('value_float', models.FloatField(null=True)),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='types', to='sde.AttributeType')),
                ('type', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='sde.Type')),
            ],
        ),
        migrations.AddField(
            model_name='system',
            name='sun',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='sde.Type'),
        ),
        migrations.AddField(
            model_name='station',
            name='system',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='sde.System'),
        ),
        migrations.AddField(
            model_name='station',
            name='type',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='sde.Type'),
        ),
        migrations.AddField(
            model_name='constellation',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='constellations', to='sde.Region'),
        ),
    ]
