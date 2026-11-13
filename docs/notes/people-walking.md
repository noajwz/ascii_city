# People walking

The streets used to be empty but for smokers and queues. `near_walkers()` puts a **lane down each
pavement of every street** in view — avenues along z, cross streets along x, found by stepping
across the view and asking `road_span()` — with slots `WALK_SLOT` apart sliding along it at the
lane's own pace and direction, and one slot in `CROWD_ODDS` filled. That shape is the whole
design: position is a function of time so nothing is stored and a walker is where they should be
whether or not you were looking; and because everyone on a lane moves at the lane's pace, two of
them can never walk through each other, which per-walker speeds would do within a minute. A
walker is drawn only where the cell is a street and dry — so they stop at the river where there
is no bridge, cross where there is one, and never go into the woods or onto the headland.

Two stride frames swapped on distance walked, not time, so the legs match the ground going by.
In the rain one in two has an umbrella up. Coats are the city's own colours. On the alien night
they all stop where they were when it began and look up — `now` is pinned to the start of the
night for them — which is what the smokers and the queue already do. `a` in the menu cycles
`some` / `busy` / `none`, a condition rather than a place, like the weather. They cost about
0.3 ms a frame.
