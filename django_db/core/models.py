from django.db import models

from sde.models import (
    Type,
    System
)


class Alliance(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=128, null=True, default=None, db_index=True)
    ticker = models.CharField(max_length=5, null=True, default=None, db_index=True)
    disbanded = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "alliance"


class Corporation(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=128, null=True, default=None, db_index=True)
    ticker = models.CharField(max_length=5, null=True, default=None, db_index=True)
    alliance = models.ForeignKey(Alliance, on_delete=models.SET_NULL, db_constraint=False, null=True, default=None)
    members = models.IntegerField(null=True, default=None)
    disbanded = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "corporation"


class Character(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=128, null=True, default=None, db_index=True)
    security_status = models.FloatField(default=0)
    corporation = models.ForeignKey(Corporation, on_delete=models.SET_NULL, db_constraint=False, null=True, default=None)

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "character"


class Killmail(models.Model):
    id = models.BigIntegerField(primary_key=True)
    hash = models.CharField(max_length=40)

    type = models.ForeignKey(Type, on_delete=models.CASCADE, db_constraint=False, db_index=True)
    system = models.ForeignKey(System, on_delete=models.CASCADE, db_constraint=False, db_index=True)
    killmail_date = models.DateTimeField(db_index=True)
    posted_date = models.DateTimeField(db_index=True)

    damage_taken = models.IntegerField(default=0)
    involved_count = models.IntegerField(default=1)
    value = models.DecimalField(max_digits=16, decimal_places=2, default=0, db_index=True)

    position_x = models.FloatField(null=True, default=None)
    position_y = models.FloatField(null=True, default=None)
    position_z = models.FloatField(null=True, default=None)

    class Meta:
        db_table = "killmail"


class Item(models.Model):
    killmail = models.ForeignKey(Killmail, on_delete=models.CASCADE)
    type = models.ForeignKey(Type, on_delete=models.CASCADE, db_constraint=False, db_index=True)

    flag = models.IntegerField()
    dropped = models.IntegerField(default=0)
    destroyed = models.IntegerField(default=0)
    singleton = models.BooleanField(default=False)
    value = models.DecimalField(max_digits=16, decimal_places=2, default=0, db_index=False)

    class Meta:
        db_table = "item"


class Involved(models.Model):
    killmail = models.ForeignKey(Killmail, on_delete=models.CASCADE)

    ship_type = models.ForeignKey(Type, null=True, on_delete=models.CASCADE, related_name="involved_ships", db_constraint=False, db_index=True)
    weapon_type = models.ForeignKey(Type, null=True, on_delete=models.CASCADE, related_name="involved_weapons", db_constraint=False, db_index=True)
    damage_done = models.IntegerField(default=0)

    is_attacker = models.BooleanField(default=True)
    final_blow = models.BooleanField(default=False)
    character = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, default=None, db_constraint=False, db_index=True)
    corporation = models.ForeignKey(Corporation, on_delete=models.SET_NULL, null=True, default=None, db_constraint=False, db_index=True)
    alliance = models.ForeignKey(Alliance, on_delete=models.SET_NULL, null=True, default=None, db_constraint=False, db_index=True)

    class Meta:
        db_table = "involved"