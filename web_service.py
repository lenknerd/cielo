#!/usr/bin/env python3
"""The web service for the Cielo game."""

import logging
from typing import Any, Mapping, Optional

import click
import mariadb
from flask import Flask, render_template

import models


app = Flask("cielo")


@app.route("/")
def index() -> str:
    """The main landing page for the Cielo web app."""
    return render_template("index.html")


@app.route("/newgame")
def newgame() -> str:
    """Start a new game. No response really needed... but okay."""
    models.start_new_game()
    return "Okay."


@app.route("/state")
def state() -> Mapping[str, Any]:
    """Get the state of the game - the feed, summary, and high score.

    Returns:
        {
            "feed": "<feed_html>",
            "summary": "Score: 12, X seconds left",
            "highscore": "High Score: 123"
        }
    """
    state = models.get_state()

    summary = f"Score: {state.latest_score}"
    if state.time_remaining_s:
        summary += f" <br/> {int(state.time_remaining_s)} seconds left"
        summary += f" <br/> Current Awards: {state.award_lower} / {state.award_upper}"

    return {
        "summary": summary,
        "feed": render_template("feed.html", events=[evt.name for evt in state.events]),
        "highscore": f"High Score: {state.high_score}",
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
