from datetime import datetime, timedelta

from flask import Flask, jsonify

from backend.app import app
from db import ReadOnlyDAO
from utils import json_response, idname_pair


def _get_corp(db, corp_id):
    """Returns the corporation info as a JSON object"""
    db.execute(
        """
        SELECT
            corporation.name as corp_name, corporation.ticker as corp_ticker,
            corporation.members as corp_members, corporation.disbanded as corp_disbanded,
            alliance.id as alliance_id, alliance.name as alliance_name, alliance.ticker as alliance_ticker
        FROM corporation
        LEFT JOIN alliance ON alliance.id = corporation.alliance_id
        WHERE corporation.id = %s
        """,
        (corp_id, )
    )
    r = db.fetchall()
    if len(r) < 1:
        return None
    corp = r[0]
    
    def filter_alliance(alliance):
        if alliance['id'] is not None:
            return {"alliance:": alliance}
        return {}

    return {
        "id": corp_id,
        "name": corp['corp_name'],
        "ticker": corp['corp_ticker'],
        "members": corp['corp_members'],
        "disbanded": corp['corp_disbanded'],
        **filter_alliance({
            "id": corp['alliance_id'],
            "name": corp['alliance_name'],
            "ticker": corp['alliance_ticker']
        })
    }


@app.route("/corporation/<int:corp_id>")
def get_corp(corp_id):
    """Returns the corp JSON object"""
    with ReadOnlyDAO() as db:
        corp = _get_corp(db, corp_id)
        if corp is None:
            return json_response(corp, status_code=404)
        return json_response(_get_corp(db, corp_id))


@app.route("/corporation/<int:corp_id>/stats")
def get_corp_with_stats(corp_id):
    """Returns the corp JSON object with aggregated stats"""
    with ReadOnlyDAO() as db:
        corp = _get_corp(db, corp_id)
        if corp is None:
            return json_response(corp, status_code=404)

        # Get corp aggregated stats
        db.execute(
            """
            SELECT count(killmail.id) as kills, coalesce(sum(killmail.value), 0) as isk
            FROM (
                SELECT DISTINCT involved.killmail_id
                FROM involved
                WHERE involved.corporation_id = %s AND involved.is_attacker = true
            ) as kill
            INNER JOIN killmail ON killmail.id = kill.killmail_id
            """,
            (corp_id, )
        )
        kill_stats = db.fetchall()[0]
        db.execute(
            """
            SELECT count(killmail.id) as kills, coalesce(sum(killmail.value), 0) as isk
            FROM (
                SELECT DISTINCT involved.killmail_id
                FROM involved
                WHERE involved.corporation_id = %s AND involved.is_attacker = false
            ) as kill
            INNER JOIN killmail ON killmail.id = kill.killmail_id
            """,
            (corp_id, )
        )
        loss_stats = db.fetchall()[0]
        db.execute(
            """
            SELECT COUNT(DISTINCT involved.character_id) as active_pilots_7d
            FROM involved
            INNER JOIN killmail ON killmail.id = involved.killmail_id
            WHERE 	killmail.killmail_date > %s
                AND	involved.corporation_id = %s
            """,
            (datetime.now() - timedelta(days=7), corp_id)
        )
        active_pilots_7d = db.fetchall()[0]['active_pilots_7d']

        return json_response({
            **corp,
            "stats": {
                "killed": kill_stats,
                "lost": loss_stats,
                "active_pilots_7d": active_pilots_7d
            }
        })