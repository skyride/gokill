import esi
import psycopg2

from app import app
from db import DAO, redis_conn
from exceptions import (
    KillmailHydrationException,
    CharacterHydrationException,
    CorporationHydrationException,
    AllianceHydrationException
)


@app.task(queue="parse_killmail", ignore_result=True)
def parse_killmail(id, hash):
    """
    Parse a killmail from ESI
    """
    r = esi.get("/v1/killmails/%i/%s/" % (id, hash))
    if r.status_code != 200:
        raise KillmailHydrationException("Received HTTP %i while fetching %i:%s" % (r.status_code, id, hash))
    data = r.json()
    attackers = data['attackers']
    victim = data['victim']

    # Get database connection
    db = DAO()

    # Get ID sets of all objects we'll need from ESI and trigger hydration requests if necessary
    characters = set(filter(None, [attacker.get('character_id') for attacker in attackers] + [victim.get('character_id')]))
    corporations = set(filter(None, [attacker.get('corporation_id') for attacker in attackers] + [victim.get('corporation_id')]))
    alliances = set(filter(None, [attacker.get('alliance_id') for attacker in attackers] + [victim.get('alliance_id')]))

    for character in characters:
        if db.redis.get('hydrate:character:%s' % character) is None:
            hydrate_character.delay(character)
            db.redis.set('hydrate:character:%s' % character, True, ex=86400)

    for corporation in corporations:
        if db.redis.get('hydrate:corporation:%s' % corporation) is None:
            hydrate_corporation.delay(corporation)
            db.redis.set('hydrate:corporation:%s' % corporation, True, ex=86400*2)

    for alliance in alliances:
        if db.redis.get('hydrate:alliance:%s' % alliance) is None:
            hydrate_alliance.delay(alliance)
            db.redis.set('hydrate:alliance:%s' % alliance, True, ex=86400*7)

    # Insert the kill
    try:
        db.execute(
            """
            INSERT INTO killmail (
                id, hash,
                type_id, system_id, killmail_date, posted_date,
                damage_taken,
                position_x, position_y, position_z
            ) VALUES (
                %s, %s,
                %s, %s, %s, CURRENT_TIMESTAMP,
                %s,
                %s, %s, %s
            )
            """,
            (
                id, hash,
                victim['ship_type_id'], data['solar_system_id'], data['killmail_time'],
                victim['damage_taken'],
                victim['position']['x'], victim['position']['y'], victim['position']['z']
            )
        )
    except psycopg2.IntegrityError as ex:
        print("Killmail %s already exists, skipping..." % id)
        return db.close()

    # Insert the items
    if len(victim['items']) > 0:
        values = [
            (
                id,
                item['item_type_id'],
                item['flag'],
                item.get('quantity_dropped', 0),
                item.get('quantity_destroyed', 0),
                bool(item['singleton'])
            )
            for item in victim['items']
        ]
        db.execute_many(
            """INSERT INTO item (
                killmail_id, type_id,
                flag, dropped, destroyed, singleton
            ) VALUES """,
            values
        )

    # Insert involved
    if len(data['attackers']):
        values = [
            (
                id,
                attacker.get('ship_type_id'),
                attacker.get('weapon_type_id'),
                attacker.get('damage_done', 0),
                True,
                bool(attacker.get('final_blow', False)),
                attacker.get('character_id'),
                attacker.get('corporation_id'),
                attacker.get('alliance_id')
            )
            for attacker in data['attackers']
        ] + [(
            id,
            victim['ship_type_id'],
            None,
            0,
            False,
            False,
            victim.get('character_id'),
            victim.get('corporation_id'),
            victim.get('alliance_id')
        )]
        db.execute_many(
            """INSERT INTO involved (
                killmail_id, ship_type_id, weapon_type_id, damage_done,
                is_attacker, final_blow, character_id, corporation_id, alliance_id
            ) VALUES """,
            values
        )

    db.commit()
    db.close()
    print (
        "Processed %s, involved=%s items=%s chars=%s corps=%s alliances=%s" % (
            id, len(attackers)+1, len(victim['items']), len(characters), len(corporations), len(alliances)
        )
    )


@app.task(queue="hydrate_character", ignore_result=True)
def hydrate_character(id):
    """
    Hydrate a character from ESI
    """
    r = esi.get("/v4/characters/%s/" % id)
    if r.status_code != 200:
        raise CharacterHydrationException("Received HTTP %i while fetching Character %i" % (r.status_code, id))
    data = r.json()

    db = DAO()
    db.execute(
        """INSERT INTO character (
            id, name, security_status, corporation_id,
            created, last_updated
        ) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id)
        DO
            UPDATE
                SET name=%s, security_status=%s, corporation_id=%s, last_updated=CURRENT_TIMESTAMP""",
        (
            id, data['name'], data['security_status'], data['corporation_id'],
            data['name'], data['security_status'], data['corporation_id']
        )
    )
    print("Hydrated character %s:%s" % (id, data['name']))
    db.commit()
    db.close()


@app.task(queue="hydrate_corporation", ignore_result=True)
def hydrate_corporation(id):
    """
    Hydrate a corporation from ESI
    """
    r = esi.get("/v4/corporations/%s/" % id)
    if r.status_code != 200:
        raise CorporationHydrationException("Received HTTP %i while fetching Corporation %i" % (r.status_code, id))
    data = r.json()

    db = DAO()
    db.execute(
        """INSERT INTO corporation (
            id, name, ticker, alliance_id, members, disbanded,
            created, last_updated
        ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id)
        DO
            UPDATE
                SET name=%s, ticker=%s, alliance_id=%s, members=%s, disbanded=%s, last_updated=CURRENT_TIMESTAMP""",
        (
            id, data['name'], data['ticker'], data.get('alliance_id'), data.get('member_count', 0), data['member_count'] < 1,
            data['name'], data['ticker'], data.get('alliance_id'), data.get('member_count', 0), data['member_count'] < 1
        )
    )
    print("Hydrated corporation %s:%s" % (id, data['name']))
    db.commit()
    db.close()


@app.task(queue="hydrate_alliance", ignore_result=True)
def hydrate_alliance(id):
    """
    Hydrate an alliance from ESI
    """
    r = esi.get("/v3/alliances/%s/" % id)
    if r.status_code != 200:
        raise AllianceHydrationException("Received HTTP %i while fetching Alliance %i" % (r.status_code, id))
    data = r.json()

    r = esi.get("/v1/alliances/%s/corporations/" % id)
    if r.status_code != 200:
        raise AllianceHydrationException("Received HTTP %i while fetching Alliance Corporations %i" % (r.status_code, id))
    corporation_ids = r.json()

    db = DAO()
    db.execute(
        """INSERT INTO alliance (
            id, name, ticker, disbanded,
            created, last_updated
        ) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id)
        DO
            UPDATE
                SET name=%s, ticker=%s, disbanded=%s, last_updated=CURRENT_TIMESTAMP""",
        (
            id, data['name'], data['ticker'], len(corporation_ids) < 1,
            data['name'], data['ticker'], len(corporation_ids) < 1
        )
    )
    print("Hydrated alliance %s:%s" % (id, data['name']))
    db.commit()
    db.close()