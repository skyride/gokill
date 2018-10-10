from flask import request

from backend.app import app
from db import ReadOnlyDAO
from utils import idname_pair, json_response


@app.route("/kill/<int:killmail_id>")
def get_killmail(killmail_id):
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

    def involved_filter(involved):
        if involved['character']['id'] is None:
            del involved['character']
        if involved['corporation']['id'] is None:
            del involved['corporation']
        if involved['alliance']['id'] is None:
            del involved['alliance']
        if "ship" in involved and involved['ship']['id'] is None:
            del involved['ship']
        if "weapon" in involved and involved['weapon']['id'] is None:
            del involved['weapon']
        return involved

    # Build JSON response and return
    return json_response({
        "id": killmail_id,
        "victim": involved_filter({
            "ship": idname_pair(
                killmail['ship_type_id'], killmail['ship_type_name'],
                group=idname_pair(killmail['ship_group_id'], killmail['ship_group_name'])
            ),
            "character": idname_pair(killmail['victim_char_id'], killmail['victim_char_name']),
            "corporation": idname_pair(killmail['victim_corp_id'], killmail['victim_corp_name']),
            "alliance": idname_pair(killmail['victim_alliance_id'], killmail['victim_alliance_name']),
            "value": round(killmail['value'], 2),
            "damage_taken": killmail['damage_taken']
        }),
        "attackers": [
            involved_filter({
                "final_blow": attacker['final_blow'],
                "damage_done": attacker['damage_done'],
                "character": idname_pair(attacker['character_id'], attacker['character_name']),
                "corporation": idname_pair(attacker['corporation_id'], attacker['corporation_name']),
                "alliance": idname_pair(attacker['alliance_id'], attacker['alliance_name']),
                "ship": idname_pair(attacker['ship_type_id'], attacker['ship_type_name']),
                "weapon": idname_pair(attacker['weapon_type_id'], attacker['weapon_type_name'])
            })
            for attacker in attackers
        ],
        "items": [
            {
                "type": idname_pair(item['type_id'], item['type_name']),
                "flag": item['flag'],
                "singleton": item['singleton'],
                "value": round(item['value'], 2),
                "dropped": item['dropped'],
                "destroyed": item['destroyed']
            }
            for item in items
        ],
        "location": {
            "system": idname_pair(killmail['system_id'], killmail['system_name'], security=round(killmail['system_security'], 2)),
            "constellation": idname_pair(killmail['const_id'], killmail['const_name']),
            "region": idname_pair(killmail['region_id'], killmail['region_name'])
        },
        "meta": {
            "killmail_date": killmail['killmail_date'],
            "posted_date": killmail['posted_date'],
            "hash": killmail['hash']
        }
    })



def filter_kills(kills=50, page=1):
    # Check we have parameters to work with
    if len(request.form) < 1:
        return json_response({"message": "No valid parameters provided"}, status_code=400)

    with ReadOnlyDAO() as db:
        # Build join and wheres list
        join_keys = set()
        form_keys = set(request.form.keys())
        wheres = []
        parameters = dict()
        try:
            # Involved
            if "alliance" in form_keys:
                join_keys.update(["involved"])
                wheres.append("involved.alliance_id = ANY(%(alliance)s)")
                parameters['alliance'] = [int(i) for i in request.form.getlist('alliance')]
            if "corporation" in form_keys:
                join_keys.update(["involved"])
                wheres.append("involved.corporation_id = ANY(%(corporation)s)")
                parameters['corporation'] = [int(i) for i in request.form.getlist('corporation')]
            if "character" in form_keys:
                join_keys.update(["involved"])
                wheres.append("involved.character = ANY(%(character)s)")
                parameters['character'] = [int(i) for i in request.form.getlist('character')]

            # Location
            if "system" in form_keys:
                wheres.append("killmail.system_id = ANY(%(system)s)")
                parameters['system'] = [int(i) for i in request.form.getlist('system')]
            if "constellation" in form_keys:
                join_keys.update(["system"])
                wheres.append("system.constellation_id = ANY(%(constellation)s)")
                parameters['constellation'] = [int(i) for i in request.form.getlist('constellation')]
            if "region" in form_keys:
                join_keys.update(["system"])
                wheres.append("system.region_id = ANY(%(region)s)")
                parameters['region'] = [int(i) for i in request.form.getlist('region')]

            # Meta
            if "value_gte" in form_keys:
                wheres.append("killmail.value >= %(value_gte)s")
                parameters['value_gte'] = int(request.form.get('value_gte'))
            if "value_lte" in form_keys:
                wheres.append("killmail.value <= %(value_lte)s")
                parameters['value_lte'] = int(request.form.get('value_lte'))
            wheres = " AND ".join(wheres)

            if len(parameters) < 1:
                return json_response({"message": "No valid parameters provided"}, status_code=400)
        except ValueError:
            return json_response({"message": "There was an error in the provided filter body"}, status_code=400)

        # Implement joins list
        joins = []
        if "involved" in join_keys:
            joins.append("involved ON involved.killmail_id = killmail.id")
        if "system" in join_keys:
            joins.append("sde_system as system ON system.id = killmail.system_id")
        joins = "\n".join([" INNER JOIN %s " % join for join in joins])
        
        # Run query
        db.execute(
            """
            SELECT  killmail.id as killmail_id, killmail.killmail_date as killmail_date,
                    killmail.involved_count as involved_count, killmail.value as value,
                    system.id as system_id, system.name as system_name,
                    region.id as region_id, region.name as region_name,
                    type.id as type_id, type.name as type_name,
                    victim_character.id as victim_character_id, victim_character.name as victim_character_name,
                    victim_corporation.id as victim_corporation_id, victim_corporation.name as victim_corporation_name,
                    victim_corporation.ticker as victim_corporation_ticker,
                    victim_alliance.id as victim_alliance_id, victim_alliance.name as victim_alliance_name,
                    victim_alliance.ticker as victim_alliance_ticker,
                    final_blow_character.id as final_blow_character_id, final_blow_character.name as final_blow_character_name,
                    final_blow_corporation.id as final_blow_corporation_id, final_blow_corporation.name as final_blow_corporation_name,
                    final_blow_corporation.ticker as final_blow_corporation_ticker,
                    final_blow_alliance.id as final_blow_alliance_id, final_blow_alliance.name as final_blow_alliance_name,
                    final_blow_alliance.ticker as final_blow_alliance_ticker
            """ +\
                "FROM (SELECT DISTINCT killmail.id, killmail.killmail_date FROM killmail" +\
                joins + " \n WHERE " +\
                wheres + " \n " +\
                """
                ORDER BY killmail.killmail_date DESC
                LIMIT %(limit)s OFFSET %(offset)s) as origin
                """ +\
            """
            INNER JOIN killmail ON killmail.id = origin.id
            LEFT JOIN sde_system as system ON system.id = killmail.system_id
            LEFT JOIN sde_region as region ON region.id = system.region_id
            LEFT JOIN sde_type as type ON type.id = killmail.type_id
            LEFT JOIN involved as victim ON victim.killmail_id = killmail.id AND victim.is_attacker = false
            LEFT JOIN character as victim_character ON victim_character.id = victim.character_id
            LEFT JOIN corporation as victim_corporation ON victim_corporation.id = victim.corporation_id
            LEFT JOIN alliance as victim_alliance ON victim_alliance.id = victim.alliance_id
            LEFT JOIN involved as final_blow ON final_blow.killmail_id = killmail.id AND final_blow.final_blow = true
            LEFT JOIN character as final_blow_character ON final_blow_character.id = final_blow.character_id
            LEFT JOIN corporation as final_blow_corporation ON final_blow_corporation.id = final_blow.corporation_id
            LEFT JOIN alliance as final_blow_alliance ON final_blow_alliance.id = final_blow.alliance_id
            """,
            {
                **parameters,
                "limit": kills, "offset": kills * page * (page - 1)
            }
        )
        return json_response(db.fetchall())


app.route("/kills/filter", methods=["POST"])(filter_kills)
app.route("/kills/filter/<int:page>", methods=["POST"])(filter_kills)
app.route("/kills/filter/<int:page>/<int:kills>", methods=["POST"])(filter_kills)