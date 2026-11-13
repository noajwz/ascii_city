# The cheat menu

**Anything new in the city gets an entry here, in the same commit that adds it.** This is a standing
instruction, not a nicety: everything worth looking at is deliberately rare, so a feature with no way
to reach it cannot be checked by the person who asked for it, and will not be. If what you added is a
place, give it a row in `CHEAT_PLACES` and a predicate for `find_place()`; if it is a condition —
weather, time, a mode — give it a key that sets it, the way `w` and `L` do. Both are a few lines.

**The panel is for going somewhere, not for testing the generator.** It was pruned of everything
that was the latter — inside a casino and inside the club (the jump to the door is one step from
it), the pleasure pier (the carnival is on it), the lighthouse's foot (its top is the one you want),
back to start, far away, someone leaning, a bridge, the end of a pier, and the streets: a dark
alley, a dead end, a crossroads, a long street, the tunnels. Their kinds are still in
`find_place()`, which the tests use; they are just not keys. Ask before putting one back.
Adding the feature and leaving the menu alone is an unfinished job.

**The panel is F1, and only F1** (`CHEAT_KEY`), since 2026-11-13, when the owner asked for
`` ` `` to go. It had been `` ` `` from the start, and on US-International - the usual layout on
Windows in the Netherlands - `` ` `` is a dead key: it sends nothing until the next key and then
both, so the panel opened and shut in one frame, or opened and jumped at once, until
`read_key()` grew a page of handling for it. F1 was added then as the key that is never dead;
now it is the only one and `read_key()` is a plain `getch()`. On a Mac laptop F1 may want fn.
The pty cases open the panel with F1's keypad form, `\x1bOP`.

F1 opens a panel over the live view — over, not instead of, so that weather you change happens
in front of you. **A jump closes it** — you went somewhere to look at it, and with the panel still
up the next key is a district or another jump; the `-> where` note shows on the HUD for four
seconds instead.

**Nowhere a taxi goes is on the panel.** Asked for on 2026-11-08: "everywhere I can get with a
taxi can be thrown away", and the FUN, EAT and AROUND TOWN groups with it. So the casino, the
club, the pictures, the arcade, ramen, the diner, the temple, the exchange, a sky deck, the roof
party, the carnival, the lighthouse, the big bridge, the bank, the woods and the lake (all of
`TAXI_DESTS`), and the claw, the hammer, a manhole, a lit alley, the El, a fire escape, a car
park, a police car and the highway went. **Do not put a taxi destination back on the panel**, and
a new place the taxi will go to does not get a key: adding it to `TAXI_DESTS` is its way in.
They are not gone for the checks: `CHEAT_HIDDEN` keeps them, and with `ASCII_CITY_TEST` set
(`pty_checks.py` sets it) ctrl-a and a key from it jumps there - the pty cases walk into
casinos and up fire escapes from a jump, and a taxi would cost each a minute. Nobody playing
can reach them that way, so the keys are free for anything new on the panel; visible keys
are matched first anyway. `checks.py` looks at both tables for everything that is about where a
jump lands.

**Trimming it found a bug that had been there a while**: the rooftop bar, a low roof, washing
lines, bowling, the turtles and flying were on `1` `2` `3` `4` `5` `8`, and the mystery on `6`
and `7` - the parts of town's digits. Places are matched first, so downtown, residential, old
town, chinatown, market, park and financial could not be reached at all, and docks only when no
case was open. They are on letters now (`b` `r` `h` `k` `t` `f`, the mystery `m` and its next
clue `c`), and a check asserts that no key on the panel does two things and none are a case
pair.

**Four columns** (`draw_cheats()`): NIGHTLIFE, MONEY, VIEWS and THE MYSTERY; the PARTS OF TOWN
(the digits, `1`–`9` and `0`, with the placed zones); AND THE REST; then WEATHER & SKY and
NIGHTS. A new place goes into a group, not on the end of a list. It was once grouped by where things were — the city, the streets, out of town —
every new place went into the first, and it quietly grew past a 24-row terminal and then a 30-row
one — `draw_cheats()` draws nothing when there is no room, so the symptom is the
panel simply not opening. There is a test that it opens at 80x24. Letters belong to the panel while
it is up; the arrow keys do not, so you can still walk about with it open.

**It generates nothing.** The city is a pure function of its coordinates, so `find_place()` searches
for what is already out there and moves the camera to it. `CLUB_ODDS` and the rest are only ever
read. A jump is exactly equivalent to having walked there, and the test for it censuses every club
and casino cell in a patch, uses every cheat, and asserts the two sets are identical — the point
being that a debug tool that quietly made the rare things common would be worse than no tool.

The search rings outward from where you stand and skips anything within `CHEAT_SKIP`, so pressing
the same key twice hops to the next one rather than landing you back where you are. The woods and
the river are not ring searches: there is one of each per tile, at a known place, so they go
straight there. Order the
predicates by cost: `_door_spot()` tests the hash **before** `is_open()`, because it throws out 1199
cells in 1200 for one multiply and means `lot()` — which builds a whole building — is only reached
on a real hit. That is the difference between 7 ms and something you would notice. `_long_street()`
is the one that cannot be cheap, since it has to `probe()`, so it stops as soon as it finds a run
worth looking down.

Two traps worth remembering. Stand a teleport **back** from what it found — three units from a
facade is a nose against a wall — and make the alley search insist on being able to see somewhere,
or it happily drops you in a one-cell walled courtyard that is technically an alley and no use at
all. Both were caught by asserting on `probe()` distance at the landing spot rather than by looking.

Weather is two module-level overrides beside the weather functions: `WEATHER_STEPS` with an index
that `rain_intensity()` consults, and `_forced_strike`, which `lightning()` checks before its own
schedule so a strike can be had on demand even when dry. The flash envelope came out into
`_strike_flash()` so the one you asked for is the same strike the storm would have had. A test
compares 400,000 samples of both functions on `auto` against the formulas they replaced and requires
zero drift.
