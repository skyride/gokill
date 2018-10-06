from flask import Flask, jsonify

from db import ReadOnlyDAO
from utils import json_response, id_name_pair

app = Flask(__name__)


@app.route("/kill/<int:killmail_id>")
def get_kill(killmail_id):
    with ReadOnlyDAO() as db:
        # Fetch the killmail
        db.execute("""
            SELECT 
                killmail.id, killmail.hash, killmail.value, killmail.damage_taken,
                killmail.type_id as ship_type_id, ship_type.name as ship_type_name,
                ship_group.id as ship_group_id, ship_group.name as ship_group_name,

                victim.character_id as victim_char_id, victim_char.name as victim_char_name,
                victim.corporation_id as victim_corp_id, victim_corp.name as victim_corp_name,
                victim.alliance_id as victim_alliance_id, victim_alliance.name as victim_alliance_name,

                killmail.system_id as system_id, system.name as system_name, system.security as system_security,
                const.id as const_id, const.name as const_name,
                region.id as region_id, region.name as region_name,

                killmail.killmail_date, killmail.posted_date

            FROM killmail
                LEFT JOIN sde_type as ship_type ON ship_type.id = killmail.type_id
                LEFT JOIN sde_group as ship_group ON ship_group.id = ship_type.group_id

                LEFT JOIN involved as victim ON victim.killmail_id = killmail.id AND victim.is_attacker = false
                LEFT JOIN character as victim_char ON victim_char.id = victim.character_id
                LEFT JOIN corporation as victim_corp ON victim_corp.id = victim.corporation_id
                LEFT JOIN alliance as victim_alliance ON victim_alliance.id = victim.alliance_id

                LEFT JOIN sde_system as system ON system.id = killmail.system_id
                LEFT JOIN sde_constellation as const ON const.id = system.constellation_id
                LEFT JOIN sde_region as region ON region.id = system.region_id

            WHERE killmail.id = %s
            """,
            (killmail_id, )
        )
        r = db.fetchall()
        if len(r) < 1:
            return json_response({}, status_code=404)
        killmail = r[0]

        # Fetch attackers
        db.execute("""
            SELECT
                involved.final_blow, involved.damage_done,
                involved.ship_type_id, ship_type.name as ship_type_name,
                involved.weapon_type_id, weapon_type.name as weapon_type_name,
                involved.character_id, character.name as character_name,
                involved.corporation_id, corporation.name as corporation_name,
                involved.alliance_id, alliance.name as alliance_name
            FROM involved
                LEFT JOIN sde_type as ship_type ON ship_type.id = involved.ship_type_id
                LEFT JOIN sde_type as weapon_type ON weapon_type.id = involved.weapon_type_id
                LEFT JOIN character ON character.id = involved.character_id
                LEFT JOIN corporation ON corporation.id = involved.corporation_id
                LEFT JOIN alliance ON alliance.id = involved.alliance_id
            WHERE involved.killmail_id = %s AND involved.is_attacker = true
            ORDER BY involved.damage_done DESC
            """,
            (killmail_id, )
        )
        attackers = db.fetchall()

        # Fetch items
        db.execute("""
            SELECT
                item.flag, item.singleton, item.value,
                item.type_id, type.name as type_name,
                item.dropped, item.destroyed
            FROM item
            INNER JOIN sde_type as type ON type.id = item.type_id
            WHERE item.killmail_id = %s
            ORDER BY item.flag DESC, item.value DESC
            """,
            (killmail_id, )
        )
        items = db.fetchall()

    # Build JSON response and return
    return json_response({
        "killmail_id": killmail_id,
        "victim": {
            "ship": id_name_pair(
                killmail['ship_type_id'], killmail['ship_type_name'],
                group=id_name_pair(killmail['ship_group_id'], killmail['ship_group_name'])
            ),
            "character": id_name_pair(killmail['victim_char_id'], killmail['victim_char_name']),
            "corporation": id_name_pair(killmail['victim_corp_id'], killmail['victim_corp_name']),
            "alliance": id_name_pair(killmail['victim_alliance_id'], killmail['victim_alliance_name']),
            "value": killmail['value'],
            "damage_taken": killmail['damage_taken']
        },
        "attackers": [
            {
                "final_blow": attacker['final_blow'],
                "damage_done": attacker['damage_done'],
                "character": id_name_pair(attacker['character_id'], attacker['character_name']),
                "corporation": id_name_pair(attacker['corporation_id'], attacker['corporation_name']),
                "alliance": id_name_pair(attacker['alliance_id'], attacker['alliance_name'])
            }
            for attacker in attackers
        ],
        "items": [
            {
                "type": id_name_pair(item['type_id'], item['type_name']),
                "flag": item['flag'],
                "singleton": item['singleton'],
                "value": item['value'],
                "dropped": item['dropped'],
                "destroyed": item['destroyed']
            }
            for item in items
        ],
        "location": {
            "system": id_name_pair(killmail['system_id'], killmail['system_name'], security=killmail['system_security']),
            "constellation": id_name_pair(killmail['const_id'], killmail['const_name']),
            "region": id_name_pair(killmail['region_id'], killmail['region_name'])
        },
        "meta": {
            "killmail_date": killmail['killmail_date'],
            "posted_date": killmail['posted_date'],
            "hash": killmail['hash']
        }
    })