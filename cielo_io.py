"""IO utilities for Cielo game.

Everything outside of here should be relatively platform-agnostic - only this module
cares that we're on a Raspberry Pi and what the IO setup is.

Interface to this module is a singleton class, Interface. Key methods:
    Interface.get_latest_times() # To check latest times of beam crosses or contact
    Interface.set_on_for(LED, sec)  # Non-blocking, parallel thread turns off)
"""
import datetime
import logging
import sys
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Final, Optional, Set

import RPi.GPIO as GPIO


# See https://learn.microsoft.com/en-us/previous-versions/windows/iot-core/learn-about-hardware/pinmappings/pinmappingsrpi
# Have to pick between GPIO.BOARD and GPIO.BCM numbering. BOARD means use
# numbering system of pins on board, otherwise use Broadcom numbers (e.g. GPIO 3 on that page)
_PIN_NUMBERING_SYSTEM: Final = GPIO.BCM  # Either okay, diagrams I've seen so far use this more

# Pins 3 and 4 have built-in pull-up resistors - important for the beam sensors
# See https://www.adafruit.com/product/2168
_UPPER_BEAM_SENSOR_INPUT_PIN: Final = 4
_LOWER_BEAM_SENSOR_INPUT_PIN: Final = 3

# Pin 19 per same page has a pull-down, also set in code here but PD by default
_TOUCH_SENSOR_INPUT_PIN: Final = 19

_DEBOUNCE_MILLISECS: Final = 1000  # Not expecting multiple throw events sub-second

_PAR_THREAD_UPKEEP_PERIOD_S: Final = 0.3

# Mods to state and/or initialization go in here to avoid race conditions where
# setpoint might end up not matching output state, or other issues
_io_mod_lock = threading.Lock()


class LED(Enum):
    """LED colors (values are the BCM pins corresponding)."""

    RED = 12
    ORANGE = 16
    WHITE = 20
    GREEN = 21


_ON: Final = 1
_OFF: Final = 0


@dataclass
class LatestTimes:
    """The last times at which each thing happened to beam or hit sensors.

    This does NOT include logic like 'yes crossed beams but then you hit,
    so the end result is just a hit (bad)' - it just gives raw latest times.
    """
    hit: Optional[datetime.datetime] = None
    lower_beam_cross: Optional[datetime.datetime] = None
    upper_beam_cross: Optional[datetime.datetime] = None


# Time that the module has last been touched by ball
_T_OF_LAST_HIT: Optional[datetime.datetime] = None
# Time of last beam interrupt of lower down beam
_T_OF_LAST_LOWER_BEAM_CROSS: Optional[datetime.datetime] = None
# Time of last interrupt of higher up beam
_T_OF_LAST_UPPER_BEAM_CROSS: Optional[datetime.datetime] = None


# Interrupt callback functions - each one is only modifier of above globals

def _broken_upper_beam_callback(channel) -> None:
    print("Broke upper beam!")
    global _T_OF_LAST_UPPER_BEAM_CROSS
    _T_OF_LAST_UPPER_BEAM_CROSS = datetime.datetime.now()


def _broken_lower_beam_callback(channel) -> None:
    print("Broke lower beam!")
    global _T_OF_LAST_LOWER_BEAM_CROSS
    _T_OF_LAST_LOWER_BEAM_CROSS = datetime.datetime.now()


def _sensor_hit_callback(channel) -> None:
    print("Detected sensor hit!")
    global _T_OF_LAST_HIT
    _T_OF_LAST_HIT = datetime.datetime.now()


class Interface:
    """Interface to Cielo IO."""

    def __new__(cls):
        """Make this a singleton by storing the one instance in the class itself."""
        with _io_mod_lock:
            if not hasattr(cls, "instance"):
                cls.instance = super(Interface, cls).__new__(cls)
            return cls.instance

    def __init__(self) -> None:
        """Init interface to all IO pins."""
        with _io_mod_lock:
            if hasattr(self, "_setpoints"):
                return  # Already initialized in another thread

            GPIO.setmode(_PIN_NUMBERING_SYSTEM)

            # LED setpoint and state setup
            self._setpoints: Mapping[LED, Optional[datetime.datetime]] = {
                    color: None for color in LED}

            for led in LED:  # LED enum values are pin numbers
                GPIO.setup(led.value, GPIO.OUT)

            # For timed but non-blocking set_on_for, a parallel thread checks to turn off
            self._kill_par_thread = False
            def _upkeep() -> None:
                print("Starting upkeep thread.")
                while True:
                    if self._kill_par_thread:
                        break
                    self.upkeep()
                    time.sleep(_PAR_THREAD_UPKEEP_PERIOD_S)
            self._upkeep_thread = threading.Thread(name="upkeep_thread", target=_upkeep)
            self._upkeep_thread.start()

            # Init input pins
            GPIO.setup(_UPPER_BEAM_SENSOR_INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(_UPPER_BEAM_SENSOR_INPUT_PIN,
                GPIO.FALLING,  # Reading a false from the signal pin means beam broken
                callback=_broken_upper_beam_callback,
                bouncetime=_DEBOUNCE_MILLISECS)

            GPIO.setup(_LOWER_BEAM_SENSOR_INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(_LOWER_BEAM_SENSOR_INPUT_PIN,
                GPIO.FALLING,  # Reading a false from the signal pin means beam broken
                callback=_broken_lower_beam_callback,
                bouncetime=_DEBOUNCE_MILLISECS)

            GPIO.setup(_TOUCH_SENSOR_INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(_TOUCH_SENSOR_INPUT_PIN,
                GPIO.RISING,  # Going high on this input indicates a touch
                callback=_sensor_hit_callback,
                bouncetime=_DEBOUNCE_MILLISECS)

    def set_on_for(self, n_seconds: float, color: LED) -> None:
        """Set a particular LED on for N seconds (puts setpoint and turns on)."""
        with _io_mod_lock:
            self._setpoints[color] = datetime.datetime.now() + datetime.timedelta(0, n_seconds)
            GPIO.output(color.value, _ON)

    def upkeep(self) -> None:
        """Upkeep IO (turn off as necessary)."""
        # Make par thread
        with _io_mod_lock:
            for led, turn_off_time in self._setpoints.items():
                if turn_off_time and turn_off_time <= datetime.datetime.now():
                    GPIO.output(led.value, _OFF)
                    self._setpoints[led] = None

    def all_off(self) -> None:
        """Turn all LEDs off (setpoint AND actual IO)."""
        with _io_mod_lock:
            for led in LED:
                GPIO.output(led.value, _OFF)
                self._setpoints[led] = None

    def get_latest_times(self) -> LatestTimes:
        """Get the latest times of various input sensor events."""
        # No lock needed, just a read
        return LatestTimes(
            hit=_T_OF_LAST_HIT,
            lower_beam_cross=_T_OF_LAST_LOWER_BEAM_CROSS,
            upper_beam_cross=_T_OF_LAST_UPPER_BEAM_CROSS,
        )

    def cleanup(self) -> None:
        """Clean up IO."""
        try:
            self.all_off()
            self._kill_par_thread = True
        finally:
            try:
                GPIO.cleanup()
            except Exception as ex:
                print(f"Error {ex} cleaning up GPIO.")
                pass  # Assume already cleaned up

