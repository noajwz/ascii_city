# The woods

Not a park. The parks are the small green squares the city has everywhere; the woods are one great
dark block of trees a few districts across — Central Park sized, 700 by 420 units — with trails
through it, a hollow in the middle, and no street, light or building in it at all. There is one per
`WOODS_TILE` (2400 units) in each direction, jittered inside its tile, so from anywhere the nearest
is a long walk. ctrl-a `o` in the checks' menu takes you to a gate.

**It is placed, not picked.** `WOODS` is a district row that is not in `DISTRICTS`: `district()`
returns it for any cell `woods_at()` says yes to, so `lot()` builds a tree there with no changes of
its own, and the HUD says *the woods*. The trees are much taller than a park's — `WOODS` builds 18 to 30, a park 5 to 10 — and `draw_tree_column()` starts their canopy half way up and draws the trunks under it as whole columns a bay apart, with undergrowth at their feet, so in among them you see the wood and not only the leaves; a park's clump stays low and bushy to the ground. The leaf tone is
scaled down to the dark end of the palette — by multiplying the *same* random draw, so nothing else
about the city moves.

**No street runs through it.** `road_at()` says no inside the woods, so an avenue stops dead at the
trees; what continues it is a **gate** in `trail_at()` — the cells where a road meets the edge are
open through to a **ring trail** that runs a couple of cells inside the edge all the way round.
Three long trails and two cross trails wander through the interior and run into the ring, and a
straight path goes down into the hollow. The trails are two or three cells wide — one cell was
reported as "hard to walk through", and it was: `BODY` leaves a cell and a bit of slack, so any
drift in your heading is a bump. Off the trails the wood is `WOODS_OPEN` percent open, held under
the percolation threshold on purpose: you get some way in and have to turn round, which is what
being lost in a wood is. There is a test that every gate reaches the hollow on foot, and a second
that a good part of the wood is *not* on the way — both matter. At 46% open two thirds of it was
off limits; at 54% it is a third, which is the balance that feels right.

The edge wanders (`woods_depth()`), and its slope is held under a cell per cell so the ring trail
that follows it cannot break: a band two cells wide shifted by more than two cells between one
column and the next would come apart into diagonal steps, which `can_stand()` does not walk.

**What is in there with you.** `draw_woods_life()` runs whenever you are in or near the woods:
fireflies over the open ground on a dry night — mostly over the trail you are on, because the rest
of the wood is behind the nearest trees — and now and then two points of light low under a tree
that go out if you look for long enough. They sit just clear of the trunk on the side facing you,
in the next cell over, and only if that cell is open; inside the tree's own cell the tree hides
its own eyes, which is how the first version showed none at all. Nothing is ever drawn attached
to them. Rain puts the fireflies out.

**The lake** lies off towards one end of the wood, away from the hollow — two different places to
end up, and between them is where you get lost. `lake_at()` is the second kind of water in the
city, and it cost almost nothing: `water_at()` is river-or-lake, and `is_open()`, `dry_at()` and the
ground pass ask that instead of `river_at()`. Everything else the river has — `v.water`, the mist,
the reflection — works off the cells that were drawn as water and never asks which water it is.
Any trail that reaches the shore joins the **shore path** that runs round it, because a trail that
simply ran into the lake would end in it. The gulls stay the river's.

The reflection pass reflects **the sky now, not only the facades** — it used to start at the
roofline, and over a lake ringed with trees that left nothing to mirror but black. Above the
roofline anything drawn is a light (stars, the moon, the beams on the strange night), and a canopy
lit by the rig counts as one too; on the facades it is still only the lights that cross. ctrl-a `~` in the checks'
menu stands you on the shore.
