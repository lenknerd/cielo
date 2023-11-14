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
    # If last game exists (nonempty table) and score not filled in, do it
    pass


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
    for val in vals:
        return val[0]
    return 0  # No games recorded yet


def get_state() -> GameState:
    """Get the current game state."""
    pass


if __name__ == "__main__":
    print("Hi.")
