from datetime import datetime, timedelta

from flask import Flask, jsonify

from backend.app import app
from db import ReadOnlyDAO
from utils import json_response, idname_pair


def _get_alliance(db, alliance_id):
    """Returns the alliance info as a JSON object"""
    db.execute(
        """
        SELECT
            alliance.id as alliance_id, alliance.name as alliance_name, alliance.ticker as alliance_ticker
        FROM alliance
        WHERE alliance.id = %s
        """,
        (alliance_id, )
    )
    r = db.fetchall()
    if len(r) < 1:
        return None
    alliance = r[0]

    return {
        "id": alliance_id,
        "name": alliance['alliance_name'],
        "ticker": alliance['alliance_ticker']
    }


@app.route("/alliance/<int:alliance_id>")
def get_alliance(alliance_id):
    """Returns the alliance JSON object"""
    with ReadOnlyDAO() as db:
        alliance = _get_alliance(db, alliance_id)
        if alliance is None:
            return json_response(alliance, status_code=404)
        return json_response(alliance)


@app.route("/alliance/<int:alliance_id>/stats")
def get_alliance_with_stats(alliance_id):
    """Returns the alliance JSON object with aggregated stats"""
    with ReadOnlyDAO() as db:
        alliance = _get_alliance(db, alliance_id)
        if alliance is None:
            return json_response(alliance, status_code=404)

        # Get char aggregated stats
        db.execute(
            """
            SELECT count(killmail.id) as kills, coalesce(sum(killmail.value), 0) as isk
            FROM (
                SELECT DISTINCT involved.killmail_id
                FROM involved
                WHERE involved.alliance_id = %s AND involved.is_attacker = true
            ) as kill
            INNER JOIN killmail ON killmail.id = kill.killmail_id
            """,
            (alliance_id, )
        )
        kill_stats = db.fetchall()[0]
        db.execute(
            """
            SELECT count(killmail.id) as kills, coalesce(sum(killmail.value), 0) as isk
            FROM (
                SELECT DISTINCT involved.killmail_id
                FROM involved
                WHERE involved.alliance_id = %s AND involved.is_attacker = false
            ) as kill
            INNER JOIN killmail ON killmail.id = kill.killmail_id
            """,
            (alliance_id, )
        )
        loss_stats = db.fetchall()[0]

        return json_response({
            **alliance,
            "stats": {
                "killed": kill_stats,
                "lost": loss_stats,
            }
        })