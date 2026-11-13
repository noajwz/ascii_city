# The casino, and the one door in the city that opens

Same odds as the club (`CLUB_ODDS`, different salt) and mutually exclusive with it, so a building is
never both — but a building with **no street frontage does not get to be one**. `_road_face()` is
what enforces that, and it is not fussiness: a casino down a five-foot alley can never be stood far
enough back from to read, its marquee lands off the top of the screen, and reporting "the casino
doesn't work" is the only possible outcome. It also gives the city a division of labour worth
having — the casinos out on the main roads shouting about it, the club down a back street with no
sign at all. It costs about a fifth of them (one every 335 units against the club's 265).

Asking about the neighbours from inside `lot()` is safe, and worth understanding: `is_open()` and
`road_at()` are pure functions of *their own* coordinates and never call `lot()`, so there is no
circle. Determinism is untouched.

`draw_casino_column()` is the club's opposite in every respect: bulbs chasing round the roof and the
door canopy, and every window in the place lit. `chase()` is the running-bulb pattern — a function
of where the bulb is and what time it is, so the whole building agrees without anything being
stored. Space those bulbs by half a world unit and at arm's length one bulb covers eight columns,
which reads as a lit stripe and not as lights; they sit close together on purpose.

`draw_marquee()` is what actually says *casino*. It is laid out in **screen space, letters side by
side**, unlike everything else on a facade. A marquee that shrank with distance is a smear long
before you can stand far enough back to see the whole building — and on a fifteen-foot street you
never can — so it is a stylised fixed size. Unreadable is worse than the wrong size, which is the
same call the hung signs make about their rows.

**From the street it has three more things.** `draw_blade()` puts the name up the front corner on
a blade sign, the old Las Vegas way: a tall board standing `BLADE_OUT` out of the wall at right
angles, from over the canopy to `BLADE_RISE` above the roofline, the letters stacked down it and
bulbs chasing down both edges. Its edges are projected from the world like a hung sign's, so it is
edge-on from straight across the road and opens out as you come down the street — which is when a
blade is meant to be read, and when the marquee over the door is hardest to. The letters are in
screen rows spread down the whole board, closed up under the top of the screen when its top is
above it (the name with its first letters gone is worse than the name a little squeezed), and in
the big font once the board is wide and tall enough to take them. The first try capped their
spacing at a hung sign's and they bunched at the foot of the board. They light one at a time from
the top, flash, and hold. `draw_red_carpet()` runs a red carpet from the door across the pavement
to the kerb between brass posts and a red rope, and a `DOORMAN` in braid stands beside it.

**And it celebrates.** A 777 on the slot (`main()` sees the payout and calls `hit_jackpot()`) puts
that casino — by its cell, which the casino dict now carries — into `jackpot_on()` for
`JACKPOT_LONG`: every bulb on, every window lit, the blade, the marquee and the doorman flashing gold
and white, and inside the room's ceiling all lit. Walk out and the building is still going. A 777 is
about one pull in nine thousand, so `%` in the menu (`rig_jackpot()`) makes the next pull one
(and the next plinko ball an edge, the next race the long shot's, the next flight a
hundred), once —
the one place the slot is not honest, and only when asked.

**It is one of the two buildings you can enter.** `venue_at()` is the trigger for both: stand in a
doorway and the room is drawn around you. Neither is an interior you walk about in, because a
five-metre cell has no inside to walk about in — what you get is a room drawn around where you are
standing, and `s` walks you back out of it.

Going into a casino gets you a room rather than a screenful of wheel. `render_casino_room()` puts the wheel in the middle of one: a ceiling with the lights chasing
along it, a back wall of slot machines with their reels going, the table with five people round it,
and the way out behind you. It degrades twice — no room for the furniture gets you the bare wheel,
no room for that gets you a line of text — because it has to survive a 20x8 window like everything
else. Everything else in the city is a solid cell that
`can_stand()` keeps you out of; the casino is a proximity trigger instead of an interior.
`casino_at()` scans the 5x5 cells around you for a door within `CASINO_REACH`, and while you are
standing in one, `main()` renders the wheel instead of the street. Walk back out and it is gone.
Stand there and it deals you another after `CASINO_AGAIN` seconds, which is the joke and also
correct. Movement keys stay live throughout — `s` is how you leave.

`Spin` draws the result first and then solves the flight to end on it: the ball eases to a stop over
a whole number of turns plus exactly the offset that lands it in the right pocket. So the wheel is
honest — a uniform `randrange(37)` — but the animation never has to guess where it is going, and
there is a test that casts 2000 spins back from the final angle and checks they agree.

`WHEEL` is the real single-zero pocket order, which is not decorative: it is what puts high next to
low and red next to black the whole way round, and you can watch it turn. `_spin_rng` is the one
random source in this file that is deliberately **not** seeded from position — everything else is a
hash of where you are so the city is the same city every time, but a wheel you could predict is not
a wheel.

**The slot machine** stands to the right of the wheel from 62 columns and 15 rows — it used to
need 78 columns and a full room, and on an ordinary terminal it simply was not there, so a request
to "add a slot machine" arrived for one that existed. `Slot` is honest the way `Spin` is: the result
is drawn first from `SLOT_WEIGHTS` (a 7 is rare, a `%` is not) and the reels are then shown stopping
on it, left to right, `SLOT_STAGGER` apart.

It is played for dollars, out of the one `Wallet` (see *Money*), so a win at the slot is money
at the table, at the exchange and everywhere else. `p` pays the bet
and pulls, `+`/`-` step the bet through `SLOT_BETS`; three of a kind pays `SLOT_PAYS` times the bet
by symbol (777 is a hundred), a pair gives the bet back, and `settle()` pays out once, when the
last reel stops. Against `SLOT_WEIGHTS` that returns about 82 dollars in 100, which there is a
test for — the house wins slowly. A pull you cannot cover is refused and says `NOT ENOUGH`. The
house used to stake you again at zero; with one balance for the whole city that was free money,
so it does not. It no longer pulls itself: a machine that spent your money while you stood there
would be a bug.

The one trap from before still holds: the casino jump (`c`, then a few steps in), and the panel used to stay open
so `p` was the park. A jump closes the panel now.

**Blackjack** is on the other side of the wheel, from 92 columns; the wheel moves over and gives
up radius so all three fit (`left`/`right` in `render_casino_room()` — the wheel's `cx` is not the
screen's centre once the tables are in). One deck, reshuffled under fifteen cards, dealer stands
on 17, blackjack pays three to two, `BJ_BET` a hand out of the shared purse. `b` deals, `h`
hits, `k` stands — `s` is taken, it walks you out. The dealer's second card stays face down until
you stand, and the dealer then takes a card every `BJ_DEAL` seconds rather than all at once: a
hand that resolves in one frame is a number, not a game. The one thing that bit: `now - t >= 0.8`
is false at `t + 0.8` in floating point, so the timer compares with an epsilon.

**The plinko machine** is the casino's fourth game, and `o` goes over to it: it takes the
wheel's place in the room, the slot machine stands aside, and blackjack stays if the window is
108 wide. `Plinko` is honest the way `Spin` and `Slot` are: `drop()` pays the bet and draws every
bounce there and then — `PLINKO_ROWS` fair coins off `_spin_rng` — and the fall is a timeline from
them, so `where()` says where the ball is at any moment and `settle()` pays it once, as it lands,
`PLINKO_PAYS[rights]` times the bet. The pays are symmetric and climb to the outside, 120x at the
edges against 0.3x in the middle, which is where the binomial puts most of them: an edge is one
ball in 2048, and the machine gives back 94% (a test works that out from the table, and another
drops six thousand). Up to `PLINKO_MAX` balls in the air at once. `draw_plinko()` lays the pegs
`PLINKO_SX` apart — even, so a half step is a whole column, and wide enough for "120" under its
bin; at three the pegs jumbled and the labels ran together — and a window without
`plinko_wide()` x `plinko_tall()` for it gets a line of text.

**Bigger and harder are yours to set**: `[`/`]` step the rows through `PLINKO_ROW_SET` (8 to 16)
and `1`/`2`/`3` the risk (`PLINKO_RISKS`). `plinko_table()` makes every one of the fifteen tables
rather than anybody typing them: the edge is set by the risk and grows with the rows, since an
edge on sixteen is one ball in 32768 (high risk tops out at 1000x), the middle is 0.5, 0.3 or
0.2, and the curve between is solved by bisection so the table pays `PLINKO_BACK`; rounding to
what a machine would print (`_nice()`) leaves them between 92 and 97%, and a test holds all
fifteen to it. Each ball carries its own path and table, and the machine refuses to change while
any are falling. A board too tall for the room goes up over the ceiling and the back wall; 1000
is printed 1k under its bin, or it runs into the 180 next to it. A ball to the edge sets the building
off the way a 777 does (`hit_jackpot()`), and `%` in the menu, now *jackpot next*, rigs the next
ball to go all the way as well as the next pull.

**The races** are the fifth, on `r`, taking the middle of the room the way plinko does (the slot
machine and the table stand aside). `Races` puts up a card of `RACE_FIELD` horses every
`RACE_CYCLE`: `RACE_BET` seconds of betting — `1`-`6` puts the stake on a horse, `+`/`-` step it
through `RACE_STAKES`, out of the one wallet — then `RACE_RUN` of race and `RACE_SHOW` of result.
Each horse's real chance (`q`) is drawn when the card is made, and the board's odds are a fair
price times `RACE_CUT` rounded **down** onto `RACE_LADDER`, so the board is honest and pays back
about 87% (the rounding takes more than you would think: at a cut of 0.88 it was 79%). At the off
`update()` draws the whole finishing order from those chances, one place at a time, and
`progress()` is solved from it — each horse's line time set by where it finishes, with a wobble
that vanishes at the gate and the post, small enough that nobody runs backwards and big enough
that the lead changes in nearly every race (there are tests of all three). Winners are paid once
at the result; a winner at 20/1 or longer lights the building, and `%` in the menu brings the
longest shot home in the next race. `draw_races()` is the board and the track: number, name in
the silks' colour, odds and your money, the horse galloping to a chequered line, where it came
once it is past the post, and the commentator; a window without `RACE_WIDE` x `RACE_TALL` gets a
line of text.

**High Flyer** is the crash game, the sixth, on `f`. A round every so often: `FLY_BET` seconds of
bets (`p` puts the stake on, `+`/`-` step it), then a plane takes off and the multiplier is
`fly_mult()` — e to `FLY_GROW` times the seconds flown — until it flies away; `p` again cashes
you out at whatever it says, and the plane gone first is the stake gone. `Flyer._start()` draws
where it goes when the round starts, `FLY_BACK / (1 - u)` to the cent and capped at `FLY_TOP`, so
the chance it gets past m is `FLY_BACK / m` for every m: whatever you cash out at, the game pays
back 97%, which the tests measure both ways (the distribution, and six thousand rounds at 2x).
Truncating to the cent puts one round in 25 on 1.00x, off the ground before it leaves. `u` cycles
an automatic target (`FLY_AUTO`), which `update()` cashes the moment the multiplier passes it —
whether or not you are looking. `draw_flyer()` is the graph: a log scale up the side, the curve
drawn behind the plane, a burst where it went, the figure in the big font, green while it flies
and red when it has gone, what your stake is worth, four others at the table cashing out or not
(`FLY_PEOPLE`), and where the last ones went. Cashing out at 20x or better lights the building;
`%` sends the next one to a hundred.
