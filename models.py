#!/usr/bin/env python3
"""Logic around storing and retrieving Cielo game and event data.

Run directly to exercise IO in test database.
"""
import os
from dataclasses import dataclass
from enum import Enum
from typing import Final, List, Optional

import mariadb


# Yeah auth is not a thing in Cielo right now
_CONN_INFO: Final = {
    "user": "cielo",
    "password": "cielo",
    "database": "cielo",
    "port": 3306,
    "host": "localhost",
}


@dataclass
class Handler:
    """Database connection and cursor."""

    conn: mariadb.Connection
    cur: mariadb.cursors.Cursor


class NetEvent(Enum):
    """A net event (i.e., UPPER means crossed lower, but did NOT hit)."""

    HIT = 0
    LOWER = 1
    UPPER = 2


@dataclass
class EventTPair:
    """Event and time at which it happened."""

    event: NetEvent
    time_s: float  # Timestamp in seconds


@dataclass
class GameState:
    """The events in the current game if any, and latest score."""

    events: Optional[List[EventTPair]]  # None if no game on
    latest_score: int


def get_handler(override_db: Optional[str] = None) -> Handler:
    """Connect to the database and open cursor."""
    conn_info = {**_CONN_INFO, "database": override_db} if override_db else _CONN_INFO
    db_conn = mariadb.connect(**_CONN_INFO)
    db_cur = db_conn.cursor()
    return Handler(db_conn, db_cur)


def start_new_game() -> None:
    """Start a new game.

    Check if last game score needs to be updated, do that too if needed.
    """
    if not handler:
        handler = get_handler()

    # If last score not filled in, do it whenever new game starting.
    # Note we do this even if a game is "going on still" because ending it
    last_g_vals = handler.cur.execute("SELECT t_start, end_score FROM games "
                                        "ORDER BY t_start DESC LIMIT 1")
    if last_g_vals:  # If there is a last game (not clean slate)
        last_g_start_t, last_g_score = next(t_last_g_vals)
        if last_g_score is None:  # If the last score is not filled in
            latest_score = 3  # TODO update
            handler.cur.execute(f"UPDATE games SET end_score = {latest_score} "
                                f"WHERE t_start = {last_g_start_t}")
            handler.db_conn.commit()

    # Now start the new game
    handler.cur.execute("INSERT INTO games (t_start, duration_seconds) "
                        f"VALUES (UNIX_TIMESTAMP(), 60)")
    handler.db_conn.commit()


def store_event(handler: Optional[Handler],
                event_name: str, event_tstamp: int) -> None:
    """Store an event in the database."""
    if not handler:
        handler = get_handler()

    handler.cur.execute("INSERT INTO events (kind, t_ref)"
                        f"VALUES ('{event_name}', {event_tstamp})")
    handler.db_conn.commit()


def get_high_score(handler: Optional[Handler]) -> int:
    """Get the highest score from the games table."""
    vals = handler.cur.execute("SELECT MAX(end_score) FROM games")
    if vals:
        return next(val)[0]
    return 0  # No games recorded yet


def get_state() -> GameState:
    """Get the current game state."""
    # TODO do it
    pass


if __name__ == "__main__":
    print("Hi. Getting handler...")
    handler = get_handler(override_db="cielo_test")
    # Clear the database TODO to start off our test
    print("High score so far:")
    print(get_high_score(handler))
    print("Okay let's start a game...")
    start_new_game()
