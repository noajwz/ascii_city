# The festival in Chinatown

One night in `FESTIVAL_ODDS` is Chinatown's festival - on its own hash (`_mix(k, 9, 613)`),
and never the strange night (everyone is looking up), a blackout (it would take the lanterns)
or a fog night. Fog was not excluded at first, and the first festival night the menu found was
a fog night: the dragon was gone a dozen steps off. The festival is something to look at, so
it does not share a night with the one thing that hides everything.

**What changes, only on that night and only in Chinatown:**

- **Lanterns over the streets** (`draw_festival_strings()`): a wire across every street every
  other cell, across the avenues and the cross streets but not over a crossing, sagging, red
  lanterns with the odd gold one - the yokocho's string, slung over a whole road.
- **Lanterns on every front with no sign** (in `draw_props()`): the one-sign rule still holds -
  a front with a hung sign gets nothing extra, or the street turns back into "a wall of light
  with no buildings in it" (see Parts of town). The lanterns are made on the spot from a hash,
  not stored on the face: `lot()` is cached and does not know what night it is.
- **The parade.** One to each Chinatown tile (`parade()`): down the avenue nearest its middle,
  for as far as that runs unbroken through Chinatown - road, dry, no tunnel - and not under the
  highway, whose piers stand in the road. Fewer than `PARADE_MIN` cells and there is none.
  `near_parades()` finds them by district tile, which is staggered row by row the way
  `district_at()` is (`district_tile()`).
- **The street is shut**: `near_cars()` drops the avenue's own traffic and `near_walkers()`
  everyone on it (`on_parade()`). Cross-street traffic still crosses it.
- **The crowd** along both kerbs (`WATCHER`), three places in five taken, a crossing kept
  clear; near the head some of them cheer (`RAVER_UP`, arms up).
- **The dragon** (`draw_parade()`): a head and `DRAGON_SEGS` poles behind it, the last the
  tail, a dancer under each (`DANCER_A`/`B`, striding on distance gone), a pearl on a pole
  ahead of it and a drum cart behind (`DRUMMER`, a flash on the beat). The body rides up and
  down in a wave along it. Head, body and tail are drawn in layers at one anchor, as Aku is
  (`_layer()`): gold outline, horns and whiskers, red face, white eyes and teeth, red scales
  with every third segment gold.
- **Firecrackers** under its nose (`draw_firecrackers()`): a white crack, a spray of red and
  gold, then smoke hanging where it went off - where the head *was* at that moment, so the
  smoke is left behind as it goes on. And red paper all down the road.
- **Sky lanterns** (`draw_sky_lanterns()`): `SKY_LANTERNS` going up over each parade, drifting
  on the wind and dimming to a dot, each coming round from somewhere new once it is out of
  sight. Drawn out to `SKY_SEEN`, so from up high you can find Chinatown by them.

**The dragon goes round a loop, not up and down.** Up the street one side of the middle
(`DRAGON_LANE`), round a half circle at the end, down the other side and round again
(`parade_point()`), with a weave on top. A path that went up and back would fold the body back
through itself at every turn; on a loop every pole follows the head exactly, `DRAGON_GAP`
behind the one in front. The weave is keyed on the unwrapped distance, so it never jumps
where the loop comes round. The check walks the loop in steps of 0.1 and asserts no point
moves more than 0.3 and none leaves the road.

**The art is drawn for the distance you see it from.** `blit_sprite()` is nearest-neighbour,
so a small drawing seen close is every character doubled - the first head, nine columns wide,
came out "{{{\/O\\##" at a dozen units. The head is 18 columns, about one to one there. It is
five rows, not seven: squeezed into fewer rows, the sampler dropped the eye row first.

**The menu: `*`, dragon dance** (AND THE REST). `find_place()` gives a spot on the nearest
parade's street (pure, as the checks need); then, like the rave's `v`, the jump goes on to the
festival's night if this is not it, and `festival_front()` stands you at the front of the
crowd on the far side of the road from the dragon, a dozen units ahead of it, looking at it
coming. Not in the middle of the road: head on, the head hides the whole of the rest of it.

**The HUD**: `~ the festival in Chinatown: the dragon dance ~` within 30 units of a parade's
street, and `~ drums to the NE: ... ~` out to `FEST_HEARD`. It comes before the rave's hint.

Costs about 2.5 ms a frame at 300x90 standing at the parade (median of a short walk), nothing
on any other night: every pass starts with `night(now)["festival"]`.
