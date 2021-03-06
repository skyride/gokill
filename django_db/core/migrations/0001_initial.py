# Generated by Django 2.1.1 on 2018-09-30 03:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sde', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alliance',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, default=None, max_length=128, null=True)),
                ('ticker', models.CharField(db_index=True, default=None, max_length=5, null=True)),
                ('disbanded', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, default=None, max_length=128, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Corporation',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, default=None, max_length=128, null=True)),
                ('ticker', models.CharField(db_index=True, default=None, max_length=5, null=True)),
                ('members', models.IntegerField(default=None, null=True)),
                ('disbanded', models.BooleanField(default=False)),
                ('alliance', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Alliance')),
            ],
        ),
        migrations.CreateModel(
            name='Involved',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('damage_done', models.IntegerField(default=0)),
                ('is_attacker', models.BooleanField(default=True)),
                ('final_blow', models.BooleanField(default=False)),
                ('alliance', models.ForeignKey(db_constraint=False, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Alliance')),
                ('character', models.ForeignKey(db_constraint=False, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Character')),
                ('corporation', models.ForeignKey(db_constraint=False, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Corporation')),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flag', models.IntegerField()),
                ('dropped', models.IntegerField(default=0)),
                ('destroyed', models.IntegerField(default=0)),
                ('singleton', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Killmail',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('hash', models.CharField(max_length=40)),
                ('killmail_date', models.DateTimeField(db_index=True)),
                ('posted_date', models.DateTimeField(db_index=True)),
                ('damage_taken', models.IntegerField(default=0)),
                ('position_x', models.FloatField()),
                ('position_y', models.FloatField()),
                ('position_z', models.FloatField()),
                ('system', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='sde.System')),
                ('type', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='sde.Type')),
            ],
        ),
        migrations.AddField(
            model_name='item',
            name='killmail',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Killmail'),
        ),
        migrations.AddField(
            model_name='item',
            name='type',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='sde.Type'),
        ),
        migrations.AddField(
            model_name='involved',
            name='killmail',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Killmail'),
        ),
        migrations.AddField(
            model_name='involved',
            name='ship_type',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, related_name='involved_ships', to='sde.Type'),
        ),
        migrations.AddField(
            model_name='involved',
            name='weapon_type',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, related_name='involved_weapons', to='sde.Type'),
        ),
        migrations.AddField(
            model_name='character',
            name='corporation',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Corporation'),
        ),
    ]
