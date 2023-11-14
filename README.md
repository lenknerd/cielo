![Cielo](static/cielo-icon-192.png?raw=true "Cielo")

`Cielo` is the ultimate lazy-day indoor game. It's a ball throwing game, but you can play it without getting up,
and in fact the best position to play in is lying flat on your back on the floor, looking up at the celing.

General idea:
 * Throw the ball up towards the ceiling, trying to get it as close as you can without hitting
 * The closer you get, the more points you get
 * You also build up your point multiplier with each close approach, i.e., the point value of each subsequent score increases
 * But, if you overthrow and *hit* the ceiling, it wipes your multiplier back to the starting value

Some sensors record what happens and a web app lets you track your current score and high scores on your phone.

In the current implementation, it doesn't measure your exact distance, only whether the ball crosses either of two beams (close and "really close" to the top).
