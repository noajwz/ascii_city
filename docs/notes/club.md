# The club

One building in `CLUB_ODDS` is not offices — roughly one every 265 world units, so you come across
one every few minutes of wandering. It is decided last in `lot()`, after the faces are made, so that
being a club changes nothing about the building it was otherwise going to be.

It carries **no sign of any kind**, which is the point: `draw_club_column()` replaces the whole
normal facade path, so there is no neon, no hung sign, no awning and no window grid — just a squat
windowless slab, speckled rather than filled so it reads as a mass instead of a hole in the street.
What gives it away is `club_light()`: four to the floor at 134 BPM, white on the kick, holding a
laser colour for a fifth of a beat after it, and the strobe let off the leash for the whole of every
eighth bar. That one function drives the slit windows under the roof, the door, how far the
light spills across the wet pavement — `collect_glow()` calls it too, so the puddles pulse in time —
and the five people outside, who go white together on the kick.

Three of those five are ravers and the rest are smoking about it. `draw_raver()` puts them on the
same clock as the sound system, offset by a fraction of a beat each so the pavement is in time
without being in lockstep, and gives them a glow stick in each hand. A stick is drawn as a short
trail of its own past positions: one moving cell reads as a speck, three read as a light. Keep the
swing tight — at arm's length the trails of five dancers overlap into noise.

**They are a queue now**, and the door opens. `club_door()` swings it open once every `CLUB_DOOR`
seconds, at a hashed moment within each, for `CLUB_OPEN`: shut, the steel door shows only the beat
leaking under it; open, it is solid light, a wedge of it lies across the street
(`draw_door_light()`), and `collect_glow()` throws a second pool of it further out. `club_line()`
is everything outside. Every person has a number, and their place in the line is that number less
how many have gone in — a count that rises smoothly while the door stands open — so the one at the
front walks in at the door, the rest shuffle up a place, and somebody new joins the back, with
nothing stored. Who they are, raver or smoker, is a hash of the number, so the same person moves up
the line rather than turning into someone else, and there is a test that says so. A `BOUNCER` in
shades stands the other side of the door, arms folded, not dancing; three brass posts and a red
rope (`draw_rope()`) stand between the line and the street. The line runs whichever way along the
wall has more room from the door.

**Closing time** is the last `CLOSE_LEN` of every night but the strange one (`club_closing()`),
and runs on into the dawn on a night that has one. `club_light()` returns the house lights — a
steady `BULB`, no beat — so the slit windows, the door and the pool on the pavement all go flat and
warm at once; `club_door()` stands open and the count stops where it was; and `club_line()` gives
no queue but `going_home()`: one out of the door every `LEAVE_GAP` for `LEAVE_FOR` seconds, onto the
pavement and off down the street one way or the other, each a number whose place is a function of
how long ago they came out, until the street is empty. The bouncer stays. Inside, the rig is off,
nobody dances, the floor empties as the minutes go and the lights are up. `/` in the menu goes to
a few seconds before it.

**The bass you can see.** `club_kick()` is how far through the beat a club is (none at closing
time; the sky's on the strange night). On the kick, `bass_lots()` — found per frame by
`near_clubs()`, which tests the hash before building a lot, so it costs a few hundred multiplies —
is every building within `BASS_REACH` of the sound system, and `draw_wall_column()` drops their
windows a row while it lasts: the windows next door shake. The lot dict carries its own `ij` now
for that. And when it has rained, `draw_bass()` sends a ring of ripples out across the wet pavement
from the door on every kick, with the last one fainter behind it. The kick's window was a single
frame at 30 a second at first and easy to miss; it is a fifth of a beat now.
