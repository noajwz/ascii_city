# The submarine, and the sea from inside it

Asked for on 2026-11-16: "I've been wanting to add a submarine as well ... With the sub I could
dive in the ocean trench and see ascii fishes." Driven yourself (their choice over a ride), from a
pen at the harbour (their choice over the Herring towing her out).

**The pen** (`sub_pen()`, `sub_pen_near()`, `draw_sub_pen()`): on the quay's south edge,
`SUB_PEN_OUT` (70) further out than the boat hire - a booth, DEEP DIVES in lights, the Lantern
tied up `SUB_MOOR` (10) off the edge, clear of the lane the speedboats leave by. Yellow. `p`
there (like the boat hire, not walked into: see the speedboat in The harbour), `SUB_FEE`; `x`
anywhere and you are back at the pen. The quay's hint says so. ctrl-a `[` for the checks.

**`Sub` is a `Boat`**, which is a `Cab`: the same gentle wheel and the same throttle steps,
asked for when the cab's steering was "way too sharp" - do not work it out again. `Boat` reads
its numbers from class attributes (`TOP`, `ACCEL`, `GRIP`, ...) and asks `self.clear()` where
it can go, so the Sub overrides both and the speedboat is unchanged. On top of that her tanks:
`f` (or PgDn) adds `SUB_SINK_STEP` to the rate she goes down, `r` (PgUp) takes it off, up to
`SUB_SINK` either way, and she eases to it (`SUB_SINK_ACCEL`) - stepped like the throttle,
because a held key in a terminal is a stutter. Space stops her both ways. `l` the lamp, `h` a
sonar ping. She cannot go through the bottom (`clear()`: wherever the speedboat can, and the
bottom `SUB_HULL` under her) - into a trench wall she glances along it or stops, onto the bottom
she settles on her skids. Over `SUB_CREAK` her hull talks now and then.

## The bottom

`seabed(x, z)`, in units down from the surface, kept per unit (`_seabed_cache`, evicted like
the others; nothing finer shows, and it is asked ten thousand times a frame). By distance off
the beach: 1 at the water's edge going down gently to 21 at 400, a shelf to 63 at
`DEEP_SHELF` (1100), the slope to about 200 at `DEEP_PLAIN` (1500), then the plain, nearly
flat. Long humps and sand ripples on top, more of them deeper.

**The trench is where the Herring fishes it**: centred `DEEP_OUT` (1900) off the beach,
`DEEP_ALONG` (150) along the coast from each harbour's quay - the trench expedition's `out` and
`along`, and a check holds them equal. `DEEP_WIDE` (170) half across rim to rim, its floor
`DEEP_FLOOR_W` (55) half across, `DEEP_BOTTOM` (650: the captain's "four hundred fathom, near
enough"), ledges down the walls, running `DEEP_LONG` (1300) either way along the coast and
easing out at the ends. Placed by the harbour period alone (`_trench_mid()`), so there is a
stretch of trench even off the one place a harbour is not (the river's mouth). The ice floes and
Treasure Island are outside it, along the coast.

The dash points the way: `trench_pointer()` gives the distance and the compass word to the
nearest stretch, or OVER THE TRENCH.

## The sea from inside (`draw_deep()`)

The street renderer has nothing to draw down there - no ground plane, no fronts - so this is its
own, into the top rows of the grid, with the same camera (`PLANE`, `fx`, `fy = fx / 2`) as
`View`:

- **The bottom** is cast column by column, the way a heightmap is: march out along the ray in
  steps that grow with distance (`0.35 + t * 0.045`), and each step that comes up over what is
  drawn so far in the column fills down to it. Only out to what can be seen - the lamp
  (`SUB_LAMP`, 52), the light from above, a ping - and nothing beyond is drawn at all: past the
  lamp the sea is black. Sand in the warm palette, mud grey below 250, rock where the bottom
  climbs faster than the step (a wall). **Textured by where each cell is in the world** - the
  bottom by where that row of it lies, a wall by its depth too - so it holds still as she moves;
  the first try hashed the screen row and it crawled.
- **Light**: her lamp is a cone (brightest straight ahead, falling off to the sides and with
  distance); from above, `amb` - the moon (`moon_light()`) and the dawn - fading out by
  `DEEP_SUNLIT` (70). In the shallows the underside of the surface ripples with it.
- **The tilt**: going down, the horizon rises a little - you look down the way you are going.
- **Snow**: specks on a 4-unit grid round her, a quarter of the cells, falling slowly, lit only
  in the lamp: what makes moving read when there is nothing else near.
- **Bubbles** up past the bubble while the tanks are working, and for a moment as she goes under.
- **The ping**: a ring going out at `SUB_PING_SPEED`; for `SUB_PING_LIFE` everything inside it
  that the lamp is not lighting is painted green - the top edge of each stretch of bottom, and
  whatever is swimming. For finding things in the black.

**What lives there** (`DEEP_LIFE`, `deep_groups()`): the sea is cut into cells `DEEP_CELL`
across and `DEEP_LAYER` deep; `DEEP_ODDS` in a hundred hold a group. Its kind is picked by
weight from those that live at its depth (`_deep_pick()`), so each depth has its own: mackerel,
bass, moon jellies, turtles and rays in the shallows; lanternfish, firefly squid, moonfish,
swordfish, comb jellies in the twilight; and only in the trench, since nowhere else is deeper
than about 260, anglerfish, barreleye, grenadier, frilled shark, scabbardfish, vampire squid,
the dumbo octopus. The legends (oarfish, giant squid) are a few percent of the groups where they
live. A group goes round a circle about where it lives, facing the way it swims, a shoal's
members spread about the leader. Nothing stored: all of it from the cell's hash and the time.
At 48 to a cell it was nearly empty - one group in view - and it is 16 now.

**What lies on the bottom** (`DEEP_PROPS`, `deep_props()`): a patch every `DEEP_PATCH`, by the
depth of the bottom there - kelp (strands swaying up from the floor), rocks, starfish, spider
crabs, glass sponges, tripod fish, a herd of sea pigs, a black smoker with its tube worms, a whale
fall, and - rarest - a brass diving helmet (the one the Herring's line brings up from the trench).

**How they are drawn** (`DEEP_DRAW`): from maths, by how big they are on the screen, not
stretched drawings - a dash far off, then `><>`, then a row of it (`_fish_line()`), then a body
whose back and belly are worked out along it, with edge glyphs by slope, a forked tail, an eye
and a gill, and whatever the kind has: a sword, a dorsal fin, teeth, the angler's lure on its
bent rod, lights down its sides. Eels are ribbons in waves, jellies a bell and trailing
tentacles (comb jellies their rows of colour running round), squid go mantle first with fins and
trailing arms (the giant squid's two long tentacles with clubs), the ray flaps, the turtle rows,
the dumbo flaps its ears. Things on the bottom are fixed drawings stood on it and stretched by
distance (`_deep_blit()`), as the city's sprites are. Colours are named (`_deep_colour()`)
because none exist until the terminal does.

**In the dark only the lights show**: a creature the lamp does not reach is drawn as just its
glow - lanternfish as dotted lines, the angler as its lure alone, firefly squid blinking, comb
jellies' colours. That is most of the trench with the lamp off, and it is the best of it.

**The log**: anything that comes within `SUB_SEES` lit (or a glowing thing a bit nearer) goes in
`sub.seen`; the first time, the top of the bubble says NEW (or !! THE GIANT SQUID !!) and the
count of `DEEP_LOG`. For the session, like everything else (no persistence).

## The bubble and the dash

`render_sub()`: on the top (shallower than `SUB_UNDER`) the street renderer from just over the
water, and going under the water comes up the bubble; under, `draw_deep()`. Round it the
bubble's rim, an ellipse, her yellow lip along its foot. The dash: depth, the zone, knots,
heading, the tanks, the lamp, the bottom under her, the way to the trench, the log. Big windows
by the one system (`big_scale()`): depth and knots in block letters; the sea itself is worked
out at whatever size and needs nothing.

**What it costs**, at 300x90: 5 to 14 ms a frame under water, moving, pinging (the bottom cast
is most of it; more of it in the shallows, where the light from above reaches too). On the top
it is the street renderer, as the speedboat.

## Not done (yet)

Nothing else on the bottom is drawn: the wreck of the Mary Ellen (the wreck expedition's, 380
off), the piers' legs, the ships' hulls from below, the cave. Each would be a thing to find.
