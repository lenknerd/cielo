![Cielo](static/cielo-icon-192.png?raw=true "Cielo")

`Cielo` is the ultimate lazy-day indoor game. It's a ball throwing game, but you can play it without getting up,
and in fact the best position to play in is lying flat on your back on the floor, looking up at the celing.

General idea:
 * Throw the ball up towards the ceiling, trying to get it as close as you can without hitting
 * The closer you get, the more points you get
 * You also build up your point award with each close approach, i.e., the point value of each subsequent score increases
 * But, if you overthrow and *hit* the ceiling, you lose the benefit of your streak - it wipes your awards back to the starting value

This sets up a two fun, common game dynamics:
 * You want to get as close as you can without going over (the classic "Price Is Right" dynamic)
 * The stakes increase as you get more in a row (think bowling, two strikes in a row > 2 strikes separately)

## Architecture

Some sensors record what happens and a web app lets you track your current score and high scores on your phone.

In the current implementation, it doesn't measure your exact distance, only whether the ball crosses either of two beams (close and "really close" to the top).

More notes/diagrams on the build to come.
