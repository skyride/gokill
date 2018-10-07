from datetime import datetime, timedelta

from flask import Flask, jsonify

from backend.app import app
from db import ReadOnlyDAO
from utils import json_response, idname_pair


def _get_char(db, char_id):
    """Returns the character info as a JSON object"""
    db.execute(
        """
        SELECT
            character.name as char_name,
            corporation.id as corp_id, corporation.name as corp_name, corporation.ticker as corp_ticker,
            alliance.id as alliance_id, alliance.name as alliance_name, alliance.ticker as alliance_ticker
        FROM character
        LEFT JOIN corporation ON corporation.id = character.corporation_id
        LEFT JOIN alliance ON alliance.id = corporation.alliance_id
        WHERE character.id = %s
        """,
        (char_id, )
    )
    r = db.fetchall()
    if len(r) < 1:
        return None
    char = r[0]

    def filter_alliance(alliance):
        if alliance['id'] is not None:
            return {"alliance:": alliance}
        return {}

    return {
        "id": char_id,
        "name": char['char_name'],
        "corp": {
            "id": char['corp_id'],
            "name": char['corp_name'],
            "ticker": char['corp_ticker']
        },
        **filter_alliance({
            "id": char['alliance_id'],
            "name": char['alliance_name'],
            "ticker": char['alliance_ticker']
        })
    }


@app.route("/character/<int:char_id>")
def get_char(char_id):
    """Returns the character JSON object"""
    with ReadOnlyDAO() as db:
        char = _get_char(db, char_id)
        if char is None:
            return json_response({}, status_code=404)
        return json_response(char)


@app.route("/character/<int:char_id>/stats")
def get_char_with_stats(char_id):
    """Returns the character JSON object with aggregated stats"""
    with ReadOnlyDAO() as db:
        char = _get_char(db, char_id)
        if char is None:
            return json_response(char, status_code=404)

        # Get char aggregated stats
        db.execute(
            """
            SELECT count(killmail.id) as kills, coalesce(sum(killmail.value), 0) as isk
            FROM (
                SELECT DISTINCT involved.killmail_id
                FROM involved
                WHERE involved.character_id = %s AND involved.is_attacker = true
            ) as kill
            INNER JOIN killmail ON killmail.id = kill.killmail_id
            """,
            (char_id, )
        )
        kill_stats = db.fetchall()[0]
        db.execute(
            """
            SELECT count(killmail.id) as kills, coalesce(sum(killmail.value), 0) as isk
            FROM (
                SELECT DISTINCT involved.killmail_id
                FROM involved
                WHERE involved.character_id = %s AND involved.is_attacker = false
            ) as kill
            INNER JOIN killmail ON killmail.id = kill.killmail_id
            """,
            (char_id, )
        )
        loss_stats = db.fetchall()[0]

        return json_response({
            **char,
            "stats": {
                "killed": kill_stats,
                "lost": loss_stats,
            }
        })