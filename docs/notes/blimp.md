# The blimp

From the ideas list of the 2026-11-11 review ("a blimp with a scrolling message"), asked for on
2026-11-16: "make it rare ofcourse, I don't wanna see that blimp all the time."

**When**: one night in `BLIMP_ODDS` (10; about one in thirteen once the strange night and fog
are taken off), on its own hash (`night()["blimp"]`). `p` on the panel (NIGHTS) goes to the
next one; it stands aside for ctrl-a, whose `p` is the roof party.

**Where** (`blimps_near()`): one to every square of the city `BLIMP_TILE` (3000) across, so
wherever you are on its night there is one about - each going slowly (`BLIMP_SPEED`) round its
own loop (`BLIMP_LOOP` across), at `BLIMP_Y`. **Low on purpose**: the street camera cannot look
up, so a blimp overhead is a blimp nobody sees; at 70 units it is over the roofs from a few
blocks off, which is where you find it. Seen to `BLIMP_SEEN`. The top bar says
`~ a blimp over the city ~` near one.

**How it is drawn** (`draw_blimp()`): in screen space from where its nose, tail and middle
project - long side on it is long, end on it is round (the half-length is the projected span
and its fatness together) - filled dark through `put_cell()`, so the stars and far towers go
behind it and nearer buildings in front; fins at the tail, the gondola lit underneath, red and
green lights at its ends and a white strobe on the tail. **The message** (`BLIMP_SAYS`, one a
blimp: made-up adverts and the city talking to itself) goes along a band of light down its middle
in a neon colour that changes every few seconds - only while enough of its side faces you to
read it (`side`). It is `BLIMP_L` long and `BLIMP_D` fat - a first try at 64 by 17 was a dozen
columns and one row from three blocks off.
