# The rave in the hollow

The Samurai Jack episode is the reference — *Jack and the Rave* — and the thing taken from it is
not the lights, it is the crowd. In the club the queue is *in time*, each dancer a fraction of a
beat off the next. In the hollow they are **in step**: hoods up, and every one of `CROWD` figures
does the same thing at the same instant with no offset at all, arms up on one half of the beat
and down on the other, all facing the altar with their backs to you. That is what makes it not a
party. Between the kicks the hollow goes dark, and what is left is their eyes.

The **booth** stands at the far end — a stack with the decks on it — and **Aku is on the decks**.
In the episode it is one of his minions with headphones shaped like his horns, and Jack mistakes
him for Aku; here it is the real thing. He is the one sprite in the city that is not one colour:
four layers blitted at the same anchor (`AKU_BODY`, `AKU_FACE`, `AKU_BROW`, `AKU_WHITE`), which
works because `blit_sprite()` paints only the non-blank cells — the crest and horns in the dark
purple the rig leaves on things between hits (white when the strobe takes everything), the face a
filled green, the brows red, the eyes and the grin white. He stands up behind the booth, which hides
whatever he has for feet, towers over it, and bobs on the kick. The beams are drawn *before* him so
they come up from behind; drawn after, they were painted across his face. Beams go up out of the
booth into the canopy, which is what you see from far off; and on the ground `draw_ground()`
paints **rings** of light pulsing outward from the altar on every beat, keyed on `v.hollow`, which is
the one thing in the city meant to look like it is doing something to you. On the trails near the
hollow stand the ones still on their way, hoods up, facing it, not moving (`draw_drawn_in()`).

The rig's palette is `RAVE_TONES` — magenta, purple, green, cyan — never the full neon rainbow,
which is the club's. `rave_light()` is 168 BPM with no colour wash between kicks, just dark. On the
alien night it takes the sky's beat instead.

**And the one who is awake.** Jack stands at the near edge of the hollow, off to one side of the
path in, with his back to the altar and facing whoever comes down the path — topknot, white gi, the
sword at his hip. Everything about him is the crowd inverted: pale (`MOON_DIM`) where they are
dark, still where they move, and no light in his eyes between the kicks. Stand within seven units
and the HUD gives you his line instead of the bearing. He is only there while the rig is on; he
came for it.

**Rare and unreachable are different things, and the menu has to reach it.** `v` calls
`force_rave()` and stands you at the edge of the hollow facing the altar; the HUD gives a bearing
and a rough distance from up to 700 units (`rave_hint()`), because a wood is disorienting on purpose
and a fact you cannot walk on is no help.
