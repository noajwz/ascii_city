# Traffic

Cars, on one condition that matters more than anything about how they look: **they must not
ruin the walking.** So they drive only on the wide streets — three cells across, `road_span()`
width 3 — and only in two lanes down the middle, two units either side of the centre line, well
clear of the pavements the walkers have; nothing comes down an alley, a lane or a narrow street.
A car that would pass within `CAR_CLEAR` of you is not drawn, so crossing the road is never a car
driving through your face. `near_cars()` is the walkers' design again: each lane is slots
`CAR_SLOT` apart sliding along at the lane's own pace and direction, one in `TRAFFIC_ODDS` filled,
so two cars on a lane can never collide and nothing is stored. They stop at the river where
there is no bridge (`dry_at()`), drive through the tunnels, and on the strange night stop where
they were with everyone else.

What you see is the end of the car facing you: two white headlights coming, two red tail lights
going, and a pool of light on the road ahead of each. One in `BUS_ODDS` on an avenue is a bus with
its windows lit. One in `POLICE_ODDS` is a **police car**: the lightbar going red, blue, red, blue,
and the street round it washed in the same colours through `collect_glow()`; within earshot the
HUD says `~ a siren somewhere ~`. ctrl-a `<` in the checks' menu stands you on the pavement eighteen units ahead
of one coming towards you — at thirty it was three columns wide and lost among the shopfronts —
and `>` sets the traffic: some, busy, none. About 0.3 ms a frame.
