#!/usr/bin/env python3
"""Process to run and populate game-level events in database."""

import time
from dataclasses import asdict
from enum import Enum
from typing import Final

import click
import mariadb

from cielo_io import CieloIO, LatestTimes, LED


# Yeah auth is not a thing in this right now
_CONN_INFO: Final = {
    "user": "cielo",
    "password": "cielo",
    "database": "cielo",
    "port": 3306,
    "host": "localhost",
}

# How often to look at latest times and update LEDs and DB accordingly
_CHECK_PERIOD_S: Final = 0.2

# How long to "blur" - i.e., wait at least this long after event to
# assume that it is all that is going to happen for a given throw.
# In other words, consider how if the ball goes through the low beam,
# if I check latest event just after that, the latest event is "low"
# but if it continues up through high, then turns around goes through
# low again, the real desired "net result" is that the throw reached
# the high beam. So we need to wait a bit and check that other events
# aren't about to supercede a given one. This is that "wait time."
_EVENT_WINDOW_S: Final = 1.0


class NetEvent(Enum):
    """A net event (i.e., UPPER means crossed lower, but did NOT hit)."""

    HIT = 0
    LOWER = 1
    UPPER = 2


# How to indicate a net event visually to player
_NET_EVENT_LED_SIGNIFIERS: Final = {
    NetEvent.HIT: LED.RED,
    NetEvent.LOWER: LED.WHITE,
    NetEvent.UPPER: LED.GREEN,
}

# How long to leave the LED on for an event
_LED_DUR_S: Final = 2


def get_net_event(times: LatestTimes, ref_time: float) -> Optional[NetEvent]:
    """Decide which thing is most relevant (see above event window example).

    Arguments:
        times: The latest times things happened.
        ref_time: The reference time of "now" (stamp from time.time())

    Returns:
        The relevant net event
    """
    # If it hit, doesn't matter if other beams crossed (prioritize hit)
    if times.hit and ref_time - times.hit < _EVENT_WINDOW_S:
        return NetEvent.HIT
    # Next prioritize upper beam - went through lower to get to the upper, no hit
    if times.upper_beam_cross and ref_time - times.upper_beam_cross < _EVENT_WINDOW_S:
        return NetEvent.UPPER
    # Lastly check for lower beam
    if times.lower_beam_cross and ref_time - times.lower_beam_cross < _EVENT_WINDOW_S:
        return NetEvent.Lower

    # This should generally not happen if reading frequently enough... but throw elsewhere
    # since from this function's PoV, not knowing if/how often called, it is possible/valid
    return None


def handle_cycle(db_cur: mariadb.cursors.Cursor,
                 io_interf: CieloIO,
                 times: LatestTimes) -> LatestTimes:
    """Handle one cycle of the read/process loop.

    Arguments:
        db_cur: The database cursor
        io_interf: The IO interface
        times: The (previous-cycle) read of the latest times of beam hits/contacts

    Returns:
        A new read of the latest times of any beam hits/contacts (vals may be same).
    """
    new_read_of_times = io_interf.get_latest_times()
    now = time.time()

    if new_read_of_times != times:

        # Something happened not yet processed. Check if the window is up so can process...
        latest_thing_t = max(asdict(new_read_of_times).values())
        t_ago_s = now - latest_thing_t
        if t_ago_s > _EVENT_WINDOW_S:

            # Okay, something not yet process, but is long enough ago to process
            relevant_event = get_net_event(new_read_of_times)

            if not relevant_event:
                # Shouldn't happen unless we didn't check within event window
                raise RuntimeError("No relevant event... missed, loop rate too slow?")

            # Light an LED based on the event
            io_interf.set_on_for(_LED_DUR_S, _NET_EVENT_LED_SIGNIFIERS[relevant_event])

            # Record the event in the database for use in webapp
            db_cur.execute("INSERT INTO events (kind, t_ref)"
                           f"VALUES ('{relevant_event.name}', {latest_thing_t})")

    # Return state (more or less just to use w/ change detection btw calls of this)
    return new_read_of_times


@click.command("populate_events")
def populate_events() -> None:
    """Entrypoint for script to populate events in DB."""

    print("Initializing IO...")
    io_interf = CieloIO()

    print("IO ready. Connecting to database...")
    db_conn = mariadb.connect(**_CONN_INFO)
    db_cur = db_conn.cursor()

    print("Connected. Starting measurement loop.")
    times = LatestTimes()
    loop_iter = 0
    while True:
        # Just a debug print that something is running
        loop_iter += 1
        if loop_iter % 50 == 0:
            print(f"Loop iteration {loop_iter}")

        # All the action is in here
        times = handle_cycle(db_cur, io_interf, times)

        time.sleep(_CHECK_PERIOD_S)


if __name__ == "__main__":
    populate_events()
