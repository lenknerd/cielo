#!/usr/bin/env python3
"""Exercise IO of Cielo game.

Useful for confirming wiring connections, and functionality of cielo_io.py.
"""
import time

import inquirer

from cielo_io import Interface as CieloIO, LED


def main() -> None:
    # Basic stuff to exercise all the IO.

    print("Initializing...")
    io_interf = CieloIO()
    print("Done initializing Cielo IO.")

    # Get input on what to do
    questions = [
        inquirer.List(
            "which_test",
            message="Which output would you like to exercise?",
            choices=[
                "Read Inputs for 10s",
                "LED Test",
            ],
        )
    ]
    answer = inquirer.prompt(questions)["which_test"]

    match answer:

        case "Read Inputs for 10s":
            for i in range(20):  # Read at 2Hz
                print(io_interf.get_latest_times())
                time.sleep(0.5)

        case "LED Test":
            # Turn each on for 5s, waiting 2s between ons. They should then
            # turn themselves off staggered, via the upkeep thread.
            print("Orange first...")
            io_interf.set_on_for(5, LED.ORANGE)
            time.sleep(2)
            print("Next white...")
            io_interf.set_on_for(5, LED.WHITE)
            time.sleep(2)
            print("Then red...")
            io_interf.set_on_for(5, LED.RED)
            time.sleep(2)
            print("And finally green.")
            io_interf.set_on_for(5, LED.GREEN)

            # Wait a bit to see they turn themselves off, staggered fashion, not
            # just via the exit/cleanup
            time.sleep(5)
            print("Okay, now they should all be off.")
            time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Caught Ctl-C, will still try cleaning up IO/parallel thread.")
    finally:
        CieloIO().cleanup()
