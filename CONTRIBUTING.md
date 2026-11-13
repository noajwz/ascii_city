# Contributing to ascii_city

Thanks for wanting to help. Bug reports, ideas and code are all welcome. This page says how to
send each, and the handful of rules the city is built on, so that what you make fits in.

## Reporting a bug

Open an [issue](https://github.com/noajwz/ascii_city/issues) and include:

- **What you did and what you saw.** Where you were (the HUD at the top names the part of town),
  which keys you pressed, and what went wrong.
- **Your setup.** The OS, the terminal app, the window size in columns × rows, and the output
  of `python3 --version`.
- **The traceback**, if it crashed. It is printed in the terminal after the game exits.
- **A screenshot or a short recording**, if it is about how something looks. Many bugs here are
  only visible on screen, at a particular size or moment.

The cheat menu (F1) gets you to most places quickly, which helps with "it happens at the
lighthouse" kinds of report.

## Suggesting an idea

Open an issue describing what you would see and do. Say where in the city it belongs and how
someone would find it. Ideas that build on what is already there (the weather, the traffic,
the night's events, the cab, the plane) tend to fit best.

## Sending code

1. Fork the repo and make a branch.
2. Make your change, small and focused: one feature or one fix per pull request.
3. Run the tests (below) and add a check for what you changed.
4. Open a pull request saying what it does, why, and how you checked it. For anything visual,
   include a screenshot or recording at a normal size (around 160×45) and at a big one (300×90).

Commit messages are a plain sentence of what changed, with the why in the body if it is not
obvious: `The cab's steering, gentler: a slower wheel, wider circles at speed`.

## How the city is built

These are the rules that hold the project together. A change that breaks one will be asked to
change, so it is worth reading them before you start.

- **One file of standard-library Python.** No third-party imports, no build step. The only other
  code is the two small programs in `library/`, which are run, not imported.
- **Python 3.9 and up.** Don't use newer syntax (`match`, `X | Y` type unions and the like).
- **The city is a pure function of its coordinates.** Nothing about the world is stored: a
  building, a sign or a night's weather comes from a hash of where and when it is. Things that
  move are functions of time. Caches are only for speed, and clearing them must change nothing
  on screen.
- **Nothing is saved between sessions.** That is a choice, not a missing feature.
- **Rare things stay rare.** The cheat menu searches for what is already out there and moves you
  to it; it never creates anything.
- **The street's look is settled.** It has been restyled and reverted twice. Before changing how
  the street is drawn in general, open an issue; offer a visual change behind an in-game toggle
  so it can be compared.
- **Speed.** A frame must stay under 33 ms at 300×90 columns. A speed-up must leave every frame
  identical: render a set of views before and after and compare them character by character.
- **Big windows use one system.** Screens that grow on a big window all use `big_scale()`, and
  at scale 1 they must be exactly what they were.
- **Everything new can be reached.** A new place gets a way to it: a taxi destination, or an
  entry in the cheat menu if the taxi does not go there. Keys in the menu are never two of the
  same letter in different case.
- **Style.** Lines under 89 characters; [ruff](https://docs.astral.sh/ruff/) with its default
  settings. Name things and comment them the way the code around them does.

## Tests

```bash
python3 tests/checks.py && python3 tests/pty_checks.py
```

Both must pass. `checks.py` renders frames headlessly and asserts on what landed where (about a
minute); `pty_checks.py` plays the real game in a pseudo-terminal (a couple of minutes). There
is no framework and nothing to install. When you fix a bug, add the check that would have caught
it: nearly every bug here was found by measuring rather than looking, and the checks are why
they stayed fixed.

## Going deeper

[`CLAUDE.md`](CLAUDE.md) is the long version: how the renderer works, why things are the way they
are, and the traps that have cost time. Read the section for the part you are changing, and add
to it what you learned.

## License

By contributing, you agree that your work is released under the project's
[MIT License](LICENSE).
