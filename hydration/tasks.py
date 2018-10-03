import esi
import psycopg2
import requests

from app import app
from db import DAO, redis_conn
from exceptions import (
    ZkillFetchError,
    KillmailHydrationException,
    CharacterHydrationException,
    CorporationHydrationException,
    AllianceHydrationException,
    TypePriceHydrationException
)


@app.task(queue="parse_killmail")
def fetch_zkill_day(datetime):
    """
    Fetch all kills that happened on a particular day from the zkill API and schedule the killmails for processing.
    Returns the number of kills queued.
    """
    r = requests.get("https://zkillboard.com/api/history/%s/" % datetime.strftime("%Y%m%d"))
    if r.status_code != 200:
        raise ZkillFetchError("Received HTTP %s while trying to fetch kills on %s" % datetime)

    return len([parse_killmail.delay(id, hash) for id, hash in r.json().items()])


@app.task(queue="parse_killmail", bind=True, ignore_result=True)
def parse_killmail(self, id, hash):
    """
    Parse a killmail from ESI
    """
    r = esi.get("/v1/killmails/%s/%s/" % (id, hash))
    if r.status_code != 200:
        exc = KillmailHydrationException("Received HTTP %i while fetching %s:%s" % (r.status_code, id, hash))
        self.retry(exc=exc)
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

    # Get set of type ids used in this killmail...
    type_ids = set(filter(None,
        [
            victim['ship_type_id'],
            *[item['item_type_id'] for item in victim['items']],
            *[attacker.get('ship_type_id') for attacker in attackers],
            *[attacker.get('weapon_type_id') for attacker in attackers]
        ]
    ))
    # ... and use it to fetch and build sell price mapping
    db.execute(
        """
        SELECT id, sell
        FROM sde_type
        WHERE id = ANY(%s)
        """,
        (list(type_ids), )
    )
    prices = {type_id: float(sell) for type_id, sell in db.fetchall()}

    # Calculate kill total value
    total_value = sum([
        prices.get(victim['ship_type_id'], 0),
        *[prices.get(item['item_type_id'], 0) * (item.get('quantity_dropped', 0) + item.get('quantity_destroyed', 0)) for item in victim['items']]
    ])

    # Insert the kill
    try:
        if victim.get('position') is not None:
            position = victim['position']
            position = (position.get('x'), position.get('y'), position.get('z'))
        else:
            position = (None, None, None)
        db.execute(
            """
            INSERT INTO killmail (
                id, hash,
                type_id, system_id, killmail_date, posted_date,
                damage_taken, involved_count, value,
                position_x, position_y, position_z
            ) VALUES (
                %s, %s,
                %s, %s, %s, CURRENT_TIMESTAMP,
                %s, %s, %s,
                %s, %s, %s
            )
            """,
            (
                id, hash,
                victim['ship_type_id'], data['solar_system_id'], data['killmail_time'],
                victim['damage_taken'], len(data['attackers']), total_value,
                *position
            )
        )
    except psycopg2.IntegrityError:
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
                bool(item['singleton']),
                prices.get(item['item_type_id'], 0) * (item.get('quantity_dropped', 0) + item.get('quantity_destroyed', 0))
            )
            for item in victim['items']
        ]
        db.execute_many(
            """ INSERT INTO item (
                killmail_id, type_id,
                flag, dropped, destroyed, singleton, value
            ) VALUES """,
            values
        )

    # Insert involved
    if len(data['attackers']) > 0:
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
            """ INSERT INTO involved (
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


@app.task(bind=True, queue="hydrate_character", ignore_result=True)
def hydrate_character(self, id):
    """
    Hydrate a character from ESI
    """
    r = esi.get("/v4/characters/%s/" % id)
    if r.status_code != 200:
        exc = CharacterHydrationException("Received HTTP %i while fetching Character %i" % (r.status_code, id))
        raise self.retry(exc=exc)
    data = r.json()

    db = DAO()
    db.execute(
        """ INSERT INTO character (
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


@app.task(bind=True, queue="hydrate_corporation", ignore_result=True)
def hydrate_corporation(self, id):
    """
    Hydrate a corporation from ESI
    """
    r = esi.get("/v4/corporations/%s/" % id)
    if r.status_code != 200:
        exc = CorporationHydrationException("Received HTTP %i while fetching Corporation %i" % (r.status_code, id))
        raise self.retry(exc=exc)
    data = r.json()

    db = DAO()
    db.execute(
        """ INSERT INTO corporation (
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


@app.task(bind=True, queue="hydrate_alliance", ignore_result=True)
def hydrate_alliance(self, id):
    """
    Hydrate an alliance from ESI
    """
    r = esi.get("/v3/alliances/%s/" % id)
    if r.status_code != 200:
        exc = AllianceHydrationException("Received HTTP %i while fetching Alliance %i" % (r.status_code, id))
        raise self.retry(exc=exc)
    data = r.json()

    r = esi.get("/v1/alliances/%s/corporations/" % id)
    if r.status_code != 200:
        exc = AllianceHydrationException("Received HTTP %i while fetching Alliance Corporations %i" % (r.status_code, id))
        raise self.retry(exc=exc)
    corporation_ids = r.json()

    db = DAO()
    db.execute(
        """ INSERT INTO alliance (
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


@app.task(bind=True, queue="hydrate_prices", ignore_result=True)
def hydrate_type_prices(self):
    """
    Fetches prices from fuzzworks market API
    """
    # Get all market saleable IDs
    db = DAO()
    db.execute(
    """ SELECT id
        FROM sde_type
        WHERE market_group_id is not null
        AND published = true"""
    )
    item_ids = [item_id for item_id, in db.fetchall()]

    def chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]
    item_id_sets = chunks(item_ids, 400)

    # Hit the API for Forge prices
    price_data = {}
    for item_id_set in item_id_sets:
        r = requests.get(
            "https://market.fuzzwork.co.uk/aggregates/",
            params={
                "region": 10000002,
                "types": ",".join([str(item_id) for item_id in item_id_set])
            }
        )
        if r.status_code != 200:
            exc = TypePriceHydrationException("Fuzzworks market API returned HTTP %s" % r.status_code)
            self.retry(exc=exc)
        price_data.update(r.json())

    # Loop through update queries
    count = 0
    for id, data in price_data.items():
        db.execute("""
            UPDATE sde_type
            SET sell = %s, buy = %s
            WHERE id = %s
            """,
            (data['sell']['percentile'], data['buy']['percentile'], id)
        )
        count += 1

    print("Hydrated prices for %s items" % count)
    db.commit()
    db.close()