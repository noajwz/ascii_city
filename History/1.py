#!/usr/bin/env python3
"""
ascii_city.py - walk through an endless, procedurally generated ASCII skyline.

Controls:
    left / right  or  h / l     walk
    H / L                       run
    space                       toggle autopilot
    q                           quit

No dependencies on Linux/macOS (curses ships with Python).
On Windows:  pip install windows-curses
"""

import curses
import random
import time

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CHUNK_W = 200          # how many "world columns" one generated chunk covers
FPS = 30
WALK_SPEED = 20.0      # world columns per second
RUN_MULTIPLIER = 3.0
KEY_GRACE = 0.15       # how long a keypress keeps you moving (smooths key repeat)

# Each layer is one depth plane of the city.
# parallax: 0.0 = infinitely far away (never moves), 1.0 = right next to you.
# h and w are (min, max); h is a fraction of the available screen height.
LAYERS = [
    dict(parallax=0.20, h=(0.20, 0.45), w=(5, 12),  gap=(1, 4), palette="far"),
    dict(parallax=0.45, h=(0.30, 0.70), w=(7, 16),  gap=(1, 5), palette="mid"),
    dict(parallax=1.00, h=(0.25, 0.98), w=(9, 24),  gap=(2, 7), palette="near"),
]

WINDOW_GLYPHS = "08XZ:+=*%@o.#"

# ---------------------------------------------------------------------------
# Colour setup
#
# curses works with numbered "colour pairs" (foreground + background). We build
# one pair per colour we care about, then remember which pair number is which.
# ---------------------------------------------------------------------------

PALETTES = {}      # e.g. {"near": [3, 7, 12, ...]} -> lists of curses pair numbers
STAR = STREET = HUD = 0


def init_colors():
    global PALETTES, STAR, STREET, HUD

    curses.start_color()
    try:
        curses.use_default_colors()   # lets us keep the terminal's own background
        bg = -1
    except curses.error:
        bg = curses.COLOR_BLACK

    if curses.COLORS >= 256:
        # xterm-256 colour numbers. Bright saturated up front, muted in back.
        groups = {
            "near": [226, 33, 202, 48, 51, 201, 220, 39, 208, 84, 214, 45],
            "mid":  [31, 130, 100, 65, 96, 67, 137, 72],
            "far":  [24, 60, 23, 238, 59, 66],
        }
        extras = {"star": 254, "street": 240, "hud": 245}
        attrs = {}
    else:
        # 8-colour fallback: bold = the "bright" version of a colour.
        groups = {
            "near": [curses.COLOR_YELLOW, curses.COLOR_BLUE, curses.COLOR_RED,
                     curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_MAGENTA],
            "mid":  [curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_GREEN],
            "far":  [curses.COLOR_BLUE, curses.COLOR_BLACK],
        }
        extras = {"star": curses.COLOR_WHITE, "street": curses.COLOR_BLACK,
                  "hud": curses.COLOR_WHITE}
        attrs = {"near": curses.A_BOLD}

    pair = 1
    for name, colours in groups.items():
        ids = []
        for c in colours:
            curses.init_pair(pair, c, bg)
            ids.append(curses.color_pair(pair) | attrs.get(name, 0))
            pair += 1
        PALETTES[name] = ids

    made = {}
    for name, c in extras.items():
        curses.init_pair(pair, c, bg)
        made[name] = curses.color_pair(pair)
        pair += 1

    STAR = made["star"]
    STREET = made["street"]
    HUD = made["hud"] | curses.A_BOLD


# ---------------------------------------------------------------------------
# Building generation
#
# A building is just a list of strings (its rows, top to bottom) plus a colour.
# ---------------------------------------------------------------------------

def make_building(rng, avail_rows, spec):
    w = rng.randint(*spec["w"])
    h = max(3, int(avail_rows * rng.uniform(*spec["h"])))

    glyphs = rng.sample(WINDOW_GLYPHS, 2)   # each building uses its own 2 glyphs
    col_step = rng.choice([1, 2, 2, 3])     # spacing between window columns
    row_step = rng.choice([1, 1, 2])        # spacing between window rows
    density = rng.uniform(0.45, 0.90)       # how many of those slots are lit

    rows = []

    # Optional antenna / mast on the roof.
    if w > 3 and rng.random() < 0.55:
        col = rng.randrange(1, w - 1)
        mast = [rng.choice("^|H+")] + ["|"] * rng.randint(0, 3)
        for ch in mast:
            line = [" "] * w
            line[col] = ch
            rows.append("".join(line))

    rows.append("=" * w)                    # the roof line

    for r in range(1, h):
        line = []
        for c in range(w):
            if c == 0 or c == w - 1:
                line.append("|")            # bright vertical edge of the tower
            elif c % col_step == 0 and r % row_step == 0 and rng.random() < density:
                line.append(rng.choice(glyphs))
            else:
                line.append(" ")            # a dark, unlit window
        rows.append("".join(line))

    return {"w": w, "rows": rows, "color": rng.choice(PALETTES[spec["palette"]])}


# ---------------------------------------------------------------------------
# Chunks
#
# The city is infinite, so we can't generate it all up front. Instead the world
# is cut into fixed-width chunks. Chunk number 7 of layer 1 always gets the same
# random seed, so it always generates the exact same buildings - walk away and
# come back and the city is unchanged, without storing anything.
# ---------------------------------------------------------------------------

_cache = {}


def get_chunk(layer_i, chunk_i, avail_rows):
    key = (layer_i, chunk_i, avail_rows)
    if key not in _cache:
        if len(_cache) > 400:
            _cache.clear()   # walked a long way; the seeds rebuild it identically
        spec = LAYERS[layer_i]
        rng = random.Random(f"city|{layer_i}|{chunk_i}")   # the deterministic seed
        buildings = []
        x = chunk_i * CHUNK_W
        end = x + CHUNK_W
        while x < end:
            b = make_building(rng, avail_rows, spec)
            b["x"] = x
            buildings.append(b)
            x += b["w"] + rng.randint(*spec["gap"])
        _cache[key] = buildings
    return _cache[key]


# ---------------------------------------------------------------------------
# Rendering
#
# We never draw straight to the screen. We fill two grids - one of characters,
# one of colours - back to front, so nearer buildings paint over farther ones.
# Then the whole thing gets blitted in one go, which stops the picture flickering.
# ---------------------------------------------------------------------------

def blit(dst_ch, dst_co, b, sx, ground):
    rows = b["rows"]
    height = len(dst_ch)
    width = len(dst_ch[0])
    top = ground - len(rows) + 1
    for i, line in enumerate(rows):
        y = top + i
        if not (0 <= y < height):
            continue
        for j, ch in enumerate(line):
            if ch == " ":
                continue
            x = sx + j
            if 0 <= x < width:
                dst_ch[y][x] = ch
                dst_co[y][x] = b["color"]


def draw_stars(ch, co, cam_x, ground):
    width = len(ch[0])
    off = cam_x * 0.05          # stars drift very slowly = very far away
    for sx in range(width):
        rng = random.Random(f"star|{int(sx + off)}")
        if rng.random() < 0.07:
            y = rng.randrange(0, max(1, ground - 4))
            ch[y][sx] = rng.choice(".*'`")
            co[y][sx] = STAR


def draw_street(ch, co, cam_x, ground):
    height = len(ch)
    width = len(ch[0])

    # Lamp posts, at fixed world positions, drawn in front of everything.
    for wx in range(int(cam_x) - 2, int(cam_x) + width + 2):
        if wx % 17 == 0:
            sx = int(wx - cam_x)
            if 0 <= sx < width:
                for dy, glyph in ((0, "|"), (1, "|"), (2, "|"), (3, "o")):
                    y = ground - dy
                    if 0 <= y < height:
                        ch[y][sx] = glyph
                        co[y][sx] = STAR if glyph == "o" else STREET

    # The road itself, below the buildings.
    for y in range(ground + 1, height):
        for x in range(width):
            wx = int(x + cam_x)
            if y == ground + 2 and wx % 6 < 3:
                ch[y][x] = "-"            # centre line, scrolls as you walk
                co[y][x] = STREET
            elif y == ground + 1 and wx % 11 == 0:
                ch[y][x] = "."
                co[y][x] = STREET


def render(cam_x, width, height):
    ground = max(3, height - 4)          # the row the buildings stand on
    avail = ground + 1

    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]

    draw_stars(ch, co, cam_x, ground)

    for li, spec in enumerate(LAYERS):
        off = cam_x * spec["parallax"]   # nearer layers slide past faster
        first = int(off // CHUNK_W) - 1
        last = int((off + width) // CHUNK_W) + 1
        for ci in range(first, last + 1):
            for b in get_chunk(li, ci, avail):
                sx = int(round(b["x"] - off))
                if sx + b["w"] < 0 or sx >= width:
                    continue
                blit(ch, co, b, sx, ground)

    draw_street(ch, co, cam_x, ground)
    return ch, co


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main(stdscr):
    init_colors()
    curses.curs_set(0)          # hide the cursor
    stdscr.nodelay(True)        # don't block waiting for a keypress
    stdscr.keypad(True)         # decode arrow keys into KEY_LEFT / KEY_RIGHT

    cam_x = 0.0
    velocity = 0.0
    last_key_at = 0.0
    autopilot = False
    frame_time = 1.0 / FPS

    while True:
        now = time.monotonic()

        # --- input -----------------------------------------------------
        key = stdscr.getch()
        while key != -1:
            if key in (ord("q"), 27):
                return
            elif key in (curses.KEY_LEFT, ord("h")):
                velocity, last_key_at, autopilot = -WALK_SPEED, now, False
            elif key in (curses.KEY_RIGHT, ord("l")):
                velocity, last_key_at, autopilot = WALK_SPEED, now, False
            elif key == ord("H"):
                velocity, last_key_at, autopilot = -WALK_SPEED * RUN_MULTIPLIER, now, False
            elif key == ord("L"):
                velocity, last_key_at, autopilot = WALK_SPEED * RUN_MULTIPLIER, now, False
            elif key == ord(" "):
                autopilot = not autopilot
            elif key == curses.KEY_RESIZE:
                _cache.clear()
            key = stdscr.getch()

        # A held-down key repeats, but with gaps. Rather than moving once per
        # keypress (jerky), we keep moving for a moment after each one.
        if autopilot:
            velocity = WALK_SPEED * 0.6
        elif now - last_key_at > KEY_GRACE:
            velocity = 0.0

        cam_x += velocity * frame_time

        # --- draw ------------------------------------------------------
        height, width = stdscr.getmaxyx()
        ch, co = render(cam_x, width, height)

        stdscr.erase()
        for y in range(height):
            row_ch, row_co = ch[y], co[y]
            for x in range(width):
                c = row_ch[x]
                if c == " ":
                    continue
                # The very last cell of the screen can't be written to.
                if y == height - 1 and x == width - 1:
                    continue
                try:
                    stdscr.addch(y, x, c, row_co[x])
                except curses.error:
                    pass

        hud = " x=%-7d  arrows/hl walk  HL run  space autopilot  q quit " % cam_x
        try:
            stdscr.addstr(0, 0, hud[:width - 1], HUD)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(max(0.0, frame_time - (time.monotonic() - now)))


if __name__ == "__main__":
    curses.wrapper(main)
