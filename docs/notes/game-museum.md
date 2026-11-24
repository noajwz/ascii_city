# The game museum

Asked for on 2026-11-24: "a videogame-museum you can walk in to and have ascii art of videogames
I love", with a list (Hollow Knight, Silksong, Enter the Gungeon, Realm of the Mad God, Stardew
Valley; two Kirbys, Pokemon generations one to four, Ocarina of Time) and "I may add more later".

**The pieces are the city's own.** For each game a scene in the spirit of it - a lamp down in a
cavern, bells on red thread, a spiral of shots round a vault door, an empty throne, a farm at
sunrise, a four-green path with something in the grass, a clay flute in a field - and a plaque with
the game, who made it and when, and a line written here. Not the games' characters, sprites, logos
or words, and nothing to play. Keep to that with new ones.

**Drawing** (`Canvas`, `art_*()`): a piece is a function that draws in a space 160 by 100, square, y
down, at whatever size it is asked for, so it is never stretched: `area()` asks a function what is
at the middle of every character; `ell()`, `poly()`, `line()`, `put()` and `words()` are on top of
it. What it says is how bright (through `MUS_RAMP`) or a glyph, and one of `MUS_256`, the museum's
own colours - 40 pairs, on a 256-colour terminal only; `mus()` finds the nearest of the city's on one
without (8-colour xterm has no pairs to spare). Every piece moves a little with `t`. They were
judged in colour and not as characters; 2-8 ms at 120 x 38. `_rough()` is cached: uncached, the
cavern was 18 ms and the mountain 23.

**To hang another**: write `art_something(c, t)` and add a row to a wing in `MUSEUM_WINGS` (piece,
title, game, maker and year, a line). The wing is longer by it. A third wing is another entry and
opens straight ahead of the door; three is the most. A check hangs twice as many and a third wing.

**Where** (`lot()`, last of all): one ordinary building with a street front in `MUSEUM_ODDS`, only
where there is nothing else and not in a placed zone, so it moved nothing: 44,869 buildings compared
with the code before it, none changed but the museums. One is usually 150-350 units off. A taxi goes
("the game museum"), so there is no key on the panel; ctrl-a `z` is the checks'. From the street:
pale stone, banners of squares that scroll, GAME MUSEUM over the doors and a heart that beats
(`draw_museum_column()`, `draw_museum_front()`). Walked in to, like any door. Free.

**Inside** (`Museum`, `render_museum()`): walked round in first person, a raycaster of its own over a
list of walls, not the grid. `museum_plan()` works the rooms out from the wings: a lobby with the
desk and a heart that turns, a wing through the arch on the left and one on the right, a piece every
`MUSEUM_BAY` down both sides and one on the end wall, benches, and four visitors who move along.
Walls are dark and the pieces are what is lit. On a wall a piece is drawn at the nearest of
`MUSEUM_SIZES` to the size it is on screen and looked up from that, and drawn again within
`MUSEUM_BUDGET` a frame. `w` `a` `s` `d`, `,` `.`, `W` hurries; its plaque comes up when you are stood
at it, and **enter** is a closer look (`render_piece()`): as big as the window has room for, moving,
with its line; `a` `d` along to the next, `x` back. `x` or walking out of the door leaves
(`museum_exit()`). 4-8 ms a frame at 300x90; a closer look is drawn again no more often than four
times what it cost.
