#!/usr/bin/env python3
"""The web service for the Cielo game."""

import logging
from typing import Mapping, Optional

import click
import mariadb
from flask import Flask, render_template

import models


app = Flask("cielo")


def _start_newgame() -> None:
    """Record a new game entry into the games table."""



@app.route("/")
def index() -> str:
    """The main landing page for the Cielo web app."""
    return render_template("index.html")


@app.route("/highscore")
def highscore() -> str:
    """Get the high score text (if any games so far)."""
    return f"High Score: {models.get_high_score()}"


@app.route("/newgame")
def newgame() -> str:
    """Start a new game. No response really needed... but okay."""
    return "Okay"


@app.route("/state")
def state() -> Mapping[str, str]:
    """Get the state of the game - the feed and summary.

    Returns:
        JSON-serializable {"feed": "text", "summary": "text"}
    """
    return {
        "summary": "Most recent score, or time left.",
        "feed": "Events...\nevents...\nmore events"
    }


@click.command()
@click.option("--debug/--no-debug",
              default="False",
              help="Whether to enable debug mode")
@click.option("-p", "--port", help="Port to listen on", default=5000, type=int)
@click.option("-h", "--host", help="Use 0.0.0.0 for LAN, else localhost only")
def run(debug: bool, port: int, host: Optional[str]) -> None:
    """Run the back end of the Cielo game web app."""
    if debug:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)

    app.logger.info("Running Cielo web server.")
    app.run(port=port, host=host)


if __name__ == "__main__":
    run()
