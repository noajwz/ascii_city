# The pictures

A cinema is as rare as a club — `CLUB_ODDS` on its own hash, a street front required — and from
the pavement it is a marquee over lit doors: NOW SHOWING and the title in a ring of chasing bulbs,
in screen space for the casino marquee's reason. ctrl-a `m` in the checks' menu stands you in the doorway, and
`venue_at()` does the rest the way it does for the casino.

Inside you are in the back rows: the screen between red curtains, the projector's beam coming over
your head with dust turning in it, and three rows of the audience in silhouette — lit by the film,
so a bright scene throws light on them and a dark one leaves them as shapes. `film_frame()` is the
picture: a black-and-white short of six scenes, `SCENE_LEN` each — the title on grainy black, rain
on a window with a lamp outside, a night drive, two of them talking with subtitles (`FILM_LINES`),
the city with its windows going out, THE END — on a loop, and on the city's clock plus a per-cinema
offset, so you walk in on whatever is showing. Everything in the frame is keyed on the time within
the loop, grain and flicker included, so it really is the same film every time round; there is a
test that one loop on is the same frame.

**Half the cinemas are showing the action picture** instead (`_film_pick()`: `ACTION_TITLES`,
one in two on its own hash). `film_frame()` hands an action title to `action_frame()`, the
drama's other half on the same six-scene loop: the title slammed up in `BIG_FONT` with the screen
shaking and sparks off it, then the tagline (`ACTION_TAGS`); a car chase, side on, the hero's car
ahead and the van behind shooting, lamp posts going by and speed lines over the skyline; a leap
between rooftops in slow motion under a helicopter's searchlight; a fist fight with the blows
written up in the air (`ACTION_BLOWS`) until the villain is sent flying, K.O.; a countdown and an
explosion, fireball, debris coming down, the screen shaking, and him walking towards you without
looking back, with a line (`ACTION_QUIPS`); and THE END, ...OR IS IT?, the sequel. The explosion is
the brightest thing either film puts up, so it lights the audience the way nothing in the drama
does. And it is **in colour**: `render_cinema()` inks the fire (`@`, `%`) and the sparks (`*`, `!`)
by `ACTION_INK`, where the drama is all black and white. Its sprites are ASCII for the same reason
as the ramen room's.

The marquee's NOW SHOWING was in the star colour at first, and the stars-inside-buildings test
counted its letters as stars drawn inside a building. Anything in screen space on a facade needs a
colour that is not a star's.

**The title goes up in big letters** within `CINEMA_BIG`: the three-by-five `BIG_FONT` (the
roulette's `DIGITS` plus `LETTERS`, drawn through `big_cells()`), white, on a dark board blanked
behind it, NOW SHOWING over it and the bulbs chasing round the lot. `_title_lines()` breaks a title
too wide for the window at the space nearest the middle, and if even that will not go it is the
small sign; further off than `CINEMA_BIG` it is always the small one, because a seven-row sign on
a building a block away is bigger than the building.

**Two searchlights sweep the sky from the roof**, at the front corners, mirror to mirror, so they
cross over the street and open out again (`search_beam()`). `SEARCH_LEAN` off the vertical is what
makes them read: nearly upright they went straight off the top of the screen from anywhere near,
and from far off the nearer roofs hid them. Leant over, they cross the strip of sky over a street.
They are found per city block and cached (`cinemas_in_block()`), like the sky decks' beacons, and
drawn from `SEARCH_REACH` - and drawn *before* the props, so a sign out front is never painted over
by a beam going up behind it. Measured, a cinema's beams are in sight from about a sixth of the
street views round it, and there is a test that holds that. They are `BEAM`/`BEAM_DIM`, which are
the lamp colours under their own names: first time round they were the moon's colours, and the
star tests counted every beam cell as the moon drawn inside a building - the marquee lesson again.
