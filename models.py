#!/usr/bin/env python3
"""Logic around storing and retrieving Cielo game and event data.

Run directly to exercise IO in test database.
"""
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Final, List, Optional, Tuple

import mariadb


# Yeah auth is not a thing in Cielo right now
_CONN_INFO: Final = {
    "user": "cielo",
    "password": "cielo",
    "database": "cielo_test",
    "port": 3306,
    "host": "localhost",
}

# Game scoring parameters
_INIT_AWARD_LOWER: Final = 2
_INIT_AWARD_UPPER: Final = 5


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
class GameState:
    """The events in the latest game if any, and latest score."""

    events: List[NetEvent] = field(default_factory=list)  # Events so far
    latest_score: Optional[int] = None            # Score (None indicates no calc yet)
    high_score: int = 0                           # All time high score
    time_remaining_s: Optional[float] = None      # None if no game on
    award_lower: int = _INIT_AWARD_LOWER          # Point award for next LOWER
    award_upper: int = _INIT_AWARD_UPPER          # Point award for next UPPER
    game_t_start: Optional[int] = None            # Start t of current game


def get_handler(override_db: Optional[str] = None) -> Handler:
    """Connect to the database and open cursor."""
    conn_info = {**_CONN_INFO, "database": override_db} if override_db else _CONN_INFO
    db_conn = mariadb.connect(**conn_info)
    db_cur = db_conn.cursor()
    return Handler(db_conn, db_cur)


# Information on latest game
_LATEST_GAME_Q: Final = """
WITH last_g AS (
    SELECT * FROM games
    ORDER BY t_start DESC
    LIMIT 1
)
SELECT last_g.t_start, last_g.end_score, last_g.duration_seconds, events.kind
FROM last_g
LEFT JOIN events ON events.t_ref >= last_g.t_start
    AND events.t_ref < last_g.t_start + last_g.duration_seconds
"""


def get_state(handler: Optional[Handler] = None) -> GameState:
    """Get the latest game state from database."""
    state = GameState()

    if not handler:
        handler = get_handler()

    handler.cur.execute(_LATEST_GAME_Q)

    t_now = time.time()
    try:
        for g_t_start, g_end_score, g_dur_s, evt_kind in handler.cur:
            # No events in the most recent game is possible, in which case
            # we get start/score/dur but no event due to LEFT join above
            if evt_kind is not None:
                state.events.append(NetEvent[evt_kind])
                print("Whee! Event found:", evt_kind)

            # These get re-asserted each iteration >0, but no harm...
            state.game_t_start = g_t_start
            t_left = g_t_start + g_dur_s - t_now
            if t_left > 0:
                state.time_remaining_s = t_left
            state.latest_score = g_end_score

    except TypeError:
        print("derp.")
        pass  # NoneType is not iterable - just means no games yet

    # If any games so far
    if state.game_t_start:
        # Fill in the awards and current score (updates games table if needed)
        _fill_score_and_awards(handler, state)

        # Get high score
        handler.cur.execute("SELECT MAX(end_score) FROM games")
        state.high_score = handler.cur.fetchone()[0]

    return state


def _fill_score_and_awards(handler: Handler, state: GameState) -> None:
    """Fill the current game score and awards.

    Relies on init of state.events, state.game_t_start, and state.latest_score
    with values from the database.
    """

    current_g_score = 0
    for event in state.events:
        print("hmm yes iter...")
        if event == NetEvent.LOWER:
            # You get points equal to the award for lower beam cross
            current_g_score += state.award_lower
            # Plus your next awards go up by factor of _INIT_AWARD_LOWER
            state.award_lower *= _INIT_AWARD_LOWER
            state.award_upper *= _INIT_AWARD_LOWER
        elif event == NetEvent.UPPER:
            # You get points equal to the award for upper beam cross
            current_g_score += state.award_upper
            # Plus your next awards go up by factor of _INIT_AWARD_UPPER (even more)
            state.award_lower *= _INIT_AWARD_UPPER
            state.award_upper *= _INIT_AWARD_UPPER
        elif event == NetEvent.HIT:
            # You "lose the benefit of your streak" if you hit - reset awards
            state.award_lower = _INIT_AWARD_LOWER
            state.award_upper = _INIT_AWARD_UPPER

    # Update in database if the value doesn't match that read from games tbl
    if current_g_score != state.latest_score:
        handler.cur.execute(f"UPDATE games SET end_score = {current_g_score} "
                            f"WHERE t_start = {state.game_t_start}")
        handler.conn.commit()
        state.latest_score = current_g_score

    print("Ya. Now score", current_g_score)
    state.latest_score = current_g_score


def start_new_game(handler: Optional[Handler] = None) -> None:
    """Start a new game."""
    if not handler:
        handler = get_handler()

    # Now start the new game
    handler.cur.execute("INSERT INTO games (t_start, duration_seconds) "
                        f"VALUES (UNIX_TIMESTAMP(), 60)")
    handler.conn.commit()


def store_event(handler: Optional[Handler],
                event_name: str, event_tstamp: int) -> None:
    """Store an event in the database."""
    if not handler:
        handler = get_handler()

    handler.cur.execute("INSERT INTO events (kind, t_ref)"
                        f"VALUES ('{event_name}', {event_tstamp})")
    handler.conn.commit()


if __name__ == "__main__":

    print("Running tests. Getting handler...")
    handler = get_handler(override_db="cielo_test")

    print("State to start:", get_state(handler))
    print("Okay let's start a game...")
    start_new_game(handler)
    print("Okay wait a sec...")
    time.sleep(1)
    print("Now record a low...")
    store_event(handler, NetEvent.LOWER.name, int(time.time()))
    print("Now state is", get_state(handler))
    print("Now wait again and record an upper...")
    time.sleep(0.5)
    store_event(handler, NetEvent.UPPER.name, int(time.time()))
    print("Now state is", get_state(handler))
    time.sleep(0.5)
    print("Now a hit...")
    store_event(handler, NetEvent.HIT.name, int(time.time()))
    print("Final state is", get_state(handler))

