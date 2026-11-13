# The university

Another placed zone, in each tile between the factories and the next Strip. Old brick halls
(`UNIVERSITY`, the red palette, pitched roofs) drawn by `draw_campus_column()`: tall windows with
arched heads, warm light in about half of them, and ivy up one bay in three, thick at the foot
and thinning upwards. In the middle **the quad** (`quad_at()`, `QUAD_HI` by `QUAD_HJ`): open lawn,
`road_at()` no — the city's streets stop at it — mown like the suburbs' lawns, with paths
corner to corner and across it (`quad_path()`, in the ground pass), old lamps where they cross,
a bench with two students on it and their laptops glowing (`draw_quad()`). **The library** runs
down its west side, every window lit, LIBRARY over the door and bikes against the railings in
front; **the clock tower** stands in the middle of its north side (`clock_tower()`), over
everything round it. Both are `campus_solid()`: buildings whatever the street grid says, because
the grid ran a street through the library and left three of its seven cells open.

`draw_clock()` is the face, on whichever sides of the tower look at you: in screen space, lit
cream, ringed in gold, 12 / 3 / 6 / 9, and the hands at **the real time where you are**
(`time.localtime()`, the one thing in the city on your clock rather than its own). Its size has a
floor, for the signs' reason: true to scale it was two rows across the quad. And where it sits was
measured: at 42 the face was off the top of the screen from the far side of a seven-cell quad (the
camera's vertical focal length is bigger than it looks — 27.5 at 30 rows), so the tower is 30 and
the quad eleven cells deep. On the hour the HUD has it striking (`clock_hint()`). `{` in the menu
stands you at the south end of the quad looking at it.

**The library's doors** are open, lit, in the middle of its quad side (`library_door()`, the
cell with `libdoor`), and walking in — a venue in `venue_at()`, so the hurry rule applies — is
**the reading room** (`render_reading_room()`, the `reading` flag in `main()`): the stacks, green
lamps on the long tables, and `LIBRARY_BOOKS` on the shelf — `w` Wikipedia, `x` back out
onto the quad, three steps out and facing away, or the doorway would take you straight back in.
There was a second reader, PsychonautWiki on `p`; the owner had it taken out of the city.

**The reader is a copy**, in `library/`: `wiki_tui.py` from the TUI
repo (noajwz/TUI, as of its `b65ec95`), byte for byte, so the city carries its own and does not
need that checkout beside it. They are **run, not imported** — `run_program()` hands one the
terminal (`def_prog_mode` / `endwin`, a plain `subprocess.run` with the same Python), then takes it
back (`reset_prog_mode`, `flushinp` so keys typed there do not walk you, nodelay and keypad
again) and you are in the reading room again. They are stdlib-only and self-contained, like the
city. A fix to one in the TUI repo does not reach here by itself: copy the file over again (and
the reverse). A missing file is "that shelf is empty", not a crash.

Both readers open on their search prompt, so from a test it is Esc, then q. And walk in with the
arrow, not `w`: in the room `w` is Wikipedia. The pty harness sends the city's `q` last and then
`waitpid`s on it, so a test that leaves you inside a reader hangs. `"` in the menu stands you in
front of the doors.

**The menu has a column for the rest**, AND THE REST (`CHEAT_MORE`). It was a fifth column
with Tab paging it in on an 80-column window until the panel was trimmed to four.
