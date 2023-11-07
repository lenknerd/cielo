#!/usr/bin/env python3
"""The web service for the Cielo game."""

import logging
from typing import Optional

from flask import Flask, render_template

import click


app = Flask("cielo")


@app.route("/")
def index() -> str:
    """The main landing page for the Cielo web app."""
    return render_template("index.html")


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
