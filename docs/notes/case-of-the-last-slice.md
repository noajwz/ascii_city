# The case of the last slice

A mystery, one to a sitting (`case` in `main()`, `new_case()`; nothing kept when you quit). It
ties the city together: `CASE_TRAIL` is where to go, in order, what to call it, how to find it
(`find_place()`), and what they say there. A note starts it: in your pocket after `CASE_AFTER` of
play, with your first drink at a bar, on the pigeon you sent off, or `m` in the menu. Each step is
just **being there**: `main()` works out where you are each frame and `case_arrive()` moves on if
it is the next place. So there is no case logic in any of the venues.

`draw_case()` puts what they said in the middle for `CASE_SHOW`, on a board of its own, and all the
time a small line at the foot with who to ask next, which way relative to where you are facing, and
roughly how far (`case_line()`), the rave's reasoning: a fact you cannot walk on is no help. `j`
hides the line, and it stays off while you are inside somewhere. `c` in the menu jumps to the next
clue, for testing and for the impatient. **Spoilers are in `CASE_TRAIL`.** It ends on a low roof, and
pays `CASE_REWARD`, which is the one time money comes to you for nothing: somebody earned it.
