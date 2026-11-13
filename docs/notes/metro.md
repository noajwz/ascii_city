# The metro

One city block in `METRO_ODDS` has a station (`station_of_block()`, cached): its entrance on
the pavement in front of a building with a street front, named from `STATION_WORDS` for its part
of town. Never in the woods, a park or a placed zone, and only where `can_stand()` — one landed
on a pier. `draw_station_entrances()` puts up the lit red M on its post, the railings round the
stairs, the light coming up out of them and `(M) NAME` once you are near enough to read it;
the HUD says `e` goes down (checked before the manhole, which also takes `e`).

Down the stairs is a screen of its own, like the taxi's (`metro`, `render_platform()`): tiles,
the name on a blue band, the board with the next train and the destinations
(`metro_dests()`: the nearest station in each other part of town first, then the nearest
others, eight at most, never one with this station's own name), people at the yellow line.
`train_phase()` runs each station's train on its own `METRO_EVERY` cycle — in out of the tunnel,
doors open for `METRO_DWELL`, away. `w`/`s` choose, Enter pays `METRO_FARE` from the wallet and
waits; when the doors are open you board and `render_ride()` takes over: the line map with you
moving along it, the tunnel's lights streaking past the windows (slowing at both ends), the
platform sliding in, "Next stop" then "This is". Six to fourteen seconds by distance. You come up
the destination's stairs facing the street. `x` or Esc goes back up without riding.
`metro_dests()` costs a third of a second cold — once, going down — and nothing per frame.
`-` in the menu stands you in front of an entrance.
