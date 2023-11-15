#!/usr/bin/env python3
"""Process to run and populate game-level events in database."""

import time
import traceback
from dataclasses import asdict
from typing import Final, Optional, Tuple

import click

from cielo_io import Interface as CieloIO, LatestTimes, LED
from models import Handler, NetEvent, get_handler, store_event


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

# How to indicate a net event visually to player
_NET_EVENT_LED_SIGNIFIERS: Final = {
    NetEvent.HIT: LED.RED,
    NetEvent.LOWER: LED.WHITE,
    NetEvent.UPPER: LED.GREEN,
}

# How long to leave the LED on for an event
_LED_DUR_S: Final = 2


def get_net_event(times: LatestTimes, ref_time: float) -> Optional[Tuple[NetEvent, float]]:
    """Decide which thing is most relevant (see above event window example).

    So looking from (_EVENT_WINDOW_S * 2) ago until _EVENT_WINDOW_S ago.

    Arguments:
        times: The latest times things happened.
        ref_time: The reference time of "now" (stamp from time.time())

    Returns:
        The relevant net event, and the timestamp at which occurred
    """
    nonnull_ts = [t for t in [times.hit, times.lower_beam_cross, times.upper_beam_cross]  if t]
    if len(nonnull_ts) == 0:
        raise ValueError("Only call get_net_event if something has happened.")

    latest_thing_tstamp = max(nonnull_ts)
    t_ago_s = ref_time - latest_thing_tstamp
    if t_ago_s < _EVENT_WINDOW_S:
        # It hasn't been long enough to conclude what happened... let dust settle
        return None

    # If it hit, doesn't matter if other beams crossed (prioritize hit)
    if times.hit and ref_time - times.hit < _EVENT_WINDOW_S * 2:
        return (NetEvent.HIT, latest_thing_tstamp)
    # Next prioritize upper beam - went through lower to get to the upper, no hit
    if times.upper_beam_cross and ref_time - times.upper_beam_cross < _EVENT_WINDOW_S * 2:
        return (NetEvent.UPPER, latest_thing_tstamp)
    # Lastly check for lower beam
    if times.lower_beam_cross and ref_time - times.lower_beam_cross < _EVENT_WINDOW_S * 2:
        return (NetEvent.LOWER, latest_thing_tstamp)

    # This should generally not happen... didn't call frequently enough
    raise RuntimeError("In get_net_event, didn't find anything to handle.")


def handle_cycle(db_handler: Handler,
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

        print("Something unprocessed happened, checking for net event criteria...")
        maybe_evt_info = get_net_event(new_read_of_times, now)
        if maybe_evt_info:
            relevant_event, event_tstamp = maybe_evt_info
            # Light an LED based on the event
            io_interf.set_on_for(_LED_DUR_S, _NET_EVENT_LED_SIGNIFIERS[relevant_event])

            # Record the event in the database for use in webapp
            store_event(db_handler, relevant_event.name, int(event_tstamp))

            print("Processed the event, report times as current (processed) state")
            return new_read_of_times
        else:
            print("Change but not ready to 'sign off' on event, return old state.")
            return times
    else:
        # No change, doesn't matter which we return...
        return times


@click.command("populate_events")
def populate_events() -> None:
    """Entrypoint for script to populate events in DB."""

    print("Initializing IO...")
    io_interf = CieloIO()

    print("IO ready. Connecting to database...")
    db_handler = get_handler()

    print("Connected. Starting measurement loop.")
    times = LatestTimes()
    loop_iter = 0
    while True:
        # Just a debug print that something is running
        loop_iter += 1
        if loop_iter % 50 == 0:
            print(f"Loop iteration {loop_iter}")

        # All the action is in here
        times = handle_cycle(db_handler, io_interf, times)

        time.sleep(_CHECK_PERIOD_S)


if __name__ == "__main__":
    # Run stuff and whatever happens, clean up (stop threads, reset IO, etc.)
    try:
        populate_events()
    except Exception as ex:
        print(f"Caught exception {ex}, traceback:")
        print(traceback.format_exc())
        print("Still cleaning up IO...")
    except SystemExit as _:
        # Click throws this on Ctl-C, catch separately as inherits from BaseException
        print(f"Cleaning up IO...")
    finally:
        CieloIO().cleanup()
        print("Done cleaning up.")
