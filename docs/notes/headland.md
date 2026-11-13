# The headland, and the lighthouse

The far side of the bay is not the city. `headland_home()` puts a rocky promontory at the bridge's
far landing — centred six cells beyond the **bay's** bank, not the channel's, which was the first
bug: the centre sat in the water. `headland_at()` is rock: open ground with nothing built on it, no
street, `the headland` on the HUD. `moat_at()` is the water round the other three sides, the third
kind of water in the city and, like the lake, free — `water_at()` is river-or-lake-or-moat and
nothing downstream asks which. The far city's avenue stops at the moat, so the only way onto the
rock is over the bridge, and there is a test for both directions: you can walk off the deck to the
foot of the lighthouse, and you cannot walk there from the far bank.

**The big bridge is the only way on.** `bridge_at()` gives no ordinary crossing to any avenue within
the headland's reach of the big one (`HEAD_RI * HEAD_MOAT` cells): one avenue in four used to get a
footbridge wherever it was, and the ones near the bay landed on the rock or in the water round it.
And **the water reaches further behind the point than at the sides** — `HEAD_MOAT` at the sides,
`HEAD_BACK` behind, through `headland_r()`'s `back` stretch — so the far town stands back across
the water instead of crowding up behind the lighthouse; from the landing, looking out to the
point, the middle of the view is sky now and not a wall of buildings. Not stretched on the bay
side: that way it would flood the near bank. Even unstretched it did: away from the bridge the
bay narrows, and the ellipse reached over it and put a strip of the near bank under water — found
when the carousel turned out to be standing in it — so `moat_at()` stops at the river's near edge. `HEAD_BACK` is held where it is by `near_river()`:
the water's furthest edge, wobble and all, has to stay inside its 48 cells of the river's centre,
and at 2.7 it went over.

`draw_lighthouse()` is world points: a stack of rings, white with red bands, so it tapers and stays
round from wherever you see it; the lantern room on top with a light that is never off; a bench
at the point and a lamp by it. The **beam** is the reason the headland exists — a line of points
from the lantern out to `BEAM_REACH`, with a fainter one thrown the other way the way a real lens
does, going round once every `BEAM_TURN` seconds. It goes over the bridge, the bay and the town
without asking any of them, and where it passes over water it is drawn on the water too: a beam
that only exists in the air reads as a stick. Drawn from 420 units, further than the bridge,
because a moving light is the first thing the eye finds. ctrl-a `i` in the checks' menu puts you at the landing
looking out to the point.

### Up the lighthouse, and firing your own show from it

The lighthouse has a door at its foot, facing the bridge's landing (`LIGHT_DOOR` out from the
middle), and walking into it is on to the stair: `lighthouse_door()` starts the same lift state
the sky decks use, with `kind: "lighthouse"`, `climb_times()` for its timing and `render_stairs()`
for the climb — the steps winding down past you round the post in the middle, slit windows going
by with the beam crossing them, a count of `STAIR_STEPS`. At the top you are on the gallery:
`gallery_view()` puts the camera `GALLERY_R` from the middle and `LIGHT_H + 1.5` up, and turning
walks you round the lantern. `lighthouse_info()` is the one description of all of it — where it
stands, the door, where you come out again, and where a show goes up. `+` in the menu stands you
outside the door; one step in and you are climbing; `s` on the gallery climbs back down.

From the gallery, `draw_lighthouse()` draws neither the tower under your feet nor the lantern at
your back, and `draw_gallery()` draws the rail round you, solved per screen column against the
rail's circle the way the sky deck's parapet is solved against its square. **You stand nearer the
lantern than the rail on purpose**: at the rail itself the rail is under your chin and off the
bottom of the screen; a step in, it frames the bottom of the view.

`f` on the gallery lights a `Show`; it used to be a firing box down on the rock, which is gone.
The show goes up over the bay between the bridge and the carnival's wheel (`lighthouse_info()`'s
`show`), so from the gallery the three are in the one view, and at that height the bursts are at
eye level rather than over your head — every spark on screen, measured, where from the rock a
third went off the top. Anybody on the bridge or the far bank sees it too, since
`draw_fireworks()` draws the show's shells over its bay whatever night it is.

**The game is a beat bar**, `draw_show_bar()`, over the bottom of the view while you are up on
the gallery: cues come in from the left to a line on the right at `SHOW_BPM`, after a
count-in. The cues are laid out when the show is lit, a bar at a time from `SHOW_BARS_EASY` for the
first two and `SHOW_BARS_ALL` after; `2` is a big cue and puts a gold willow up as well. `press()`
judges against the nearest cue still waiting, `SHOW_GREAT` or `SHOW_GOOD` either side, and puts a
shell up straight away: a great one at 1.25 size, a good one smaller, and a press with no cue near
it a fizzle that breaks the streak. `update()` marks the cues that went by as misses, and once the
last has gone lays out a finale of 3 to 24 shells by how near the score came to `best`, the score
of a perfect run. A press during the finale does nothing; it is the show's own.

It is one key on purpose, the same reason the claw machine is: curses sees key repeats and never a
key going up, so nothing here can ask you to hold one. And frames are 1/30 s apart, which is why
`SHOW_GREAT` is as wide as 0.09: a press is only seen at the start of the next frame.

`shell_sparks()` grew `size`, `spread` and `willow` for this, all defaulting to what the night show
already did.
