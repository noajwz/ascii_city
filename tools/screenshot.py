"""Regenerate the screenshots in docs/.

    python3 tools/screenshot.py

Writes an SVG rather than a bitmap, on purpose: it is text, so it can be
generated with the standard library alone, it stays sharp at any size, and the
colours are exactly the ones the renderer chose. Every run of same-coloured
characters gets an explicit textLength, so the columns cannot shear apart on a
machine whose monospace font has a different advance width.

There is no colour table here. Rather than copy the palette out of
init_colors() - which would rot the first time someone edited it - this fakes
just enough curses for the real init_colors() to run, and records which
xterm-256 colour each attribute stands for.
"""
import math
import os
import sys
import unicodedata

import curses

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import sys

import curses

BOLD = 1 << 20
PAIRS = {}          # attribute value -> xterm-256 colour number


def _init_pair(pair, fg, bg):
    PAIRS[pair] = fg


curses.start_color = lambda: None
curses.use_default_colors = lambda: None
curses.COLORS = 256
curses.init_pair = _init_pair
curses.color_pair = lambda n: n
curses.A_BOLD = BOLD
curses.A_REVERSE = 1 << 21

import ascii_city as ac
ac.init_colors()


def rgb(attr):
    """Attribute -> (r, g, b), using the standard xterm-256 ramp."""
    n = PAIRS.get(attr & 0xFFFF)
    if n is None:
        return (200, 200, 200)
    if n < 16:
        base = [(0, 0, 0), (170, 0, 0), (0, 170, 0), (170, 85, 0),
                (0, 0, 170), (170, 0, 170), (0, 170, 170), (170, 170, 170),
                (85, 85, 85), (255, 85, 85), (85, 255, 85), (255, 255, 85),
                (85, 85, 255), (255, 85, 255), (85, 255, 255), (255, 255, 255)]
        return base[n]
    if n < 232:
        n -= 16
        steps = (0, 95, 135, 175, 215, 255)
        return (steps[n // 36], steps[n // 6 % 6], steps[n % 6])
    g = 8 + (n - 232) * 10
    return (g, g, g)



CW, LH, FS = 8.6, 17.0, 14.5
BG = "#0a0c10"
FONT = ("ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', "
        "monospace")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def to_svg(ch, co, title=""):
    h, w = len(ch), len(ch[0])
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%.0f" height="%.0f" '
           'viewBox="0 0 %.0f %.0f" font-family="%s" font-size="%.1f">'
           % (w * CW, h * LH + 8, w * CW, h * LH + 8, FONT, FS)]
    out.append('<rect width="100%%" height="100%%" fill="%s"/>' % BG)
    if title:
        out.append("<title>%s</title>" % esc(title))
    for y in range(h):
        x = 0
        while x < w:
            if ch[y][x] == " ":
                x += 1
                continue
            attr = co[y][x]
            run = x
            while (run < w and ch[y][run] != " " and co[y][run] == attr):
                run += 1
            text = "".join(ch[y][x:run])
            # A CJK glyph is two cells wide and the renderer leaves the cell
            # after it blank, so a run's length on screen is not its length in
            # characters.
            cells = sum(2 if unicodedata.east_asian_width(c) in ("W", "F")
                        else 1 for c in text)
            r, g, b = rgb(attr)
            bold = ' font-weight="bold"' if attr & BOLD else ""
            out.append(
                '<text x="%.1f" y="%.1f" fill="#%02x%02x%02x"%s '
                'textLength="%.1f" lengthAdjust="spacing" '
                'xml:space="preserve">%s</text>'
                % (x * CW, (y + 1) * LH, r, g, b, bold,
                   cells * CW, esc(text)))
            x = run
    out.append("</svg>")
    return "\n".join(out)


W, H = 160, 45          # a window you would actually use, not the old postcard


def write(docs, name, ch, co, title):
    open(os.path.join(docs, name + ".svg"), "w").write(
        to_svg(ch, co, "ascii_city - " + title))
    print("wrote docs/%s.svg" % name)


def best_view(kind, backs=(0.0,), turns=(0.0,), hops=6, now=300.0):
    """The most to look at of a kind of place: from the first few of them
    round the start, a step or two back and a turn either way, whichever
    frame carries the most signage - a CJK sign counts most, then letters."""
    x0, z0 = ac.start_position()
    best = None
    for hop in range(hops):
        sp = ac.find_place(x0 + hop * 700, z0 - hop * 500, kind)
        if sp is None:
            continue
        for back in backs:
            for turn in turns:
                yaw = sp[2] + turn
                x, z = sp[0] - math.sin(yaw) * back, sp[1] - math.cos(yaw) * back
                if not ac.can_stand(x, z):
                    continue
                g, _, _ = ac.render_street(ac.View(x, z, yaw, W, H), now)
                s = sum(40 if unicodedata.east_asian_width(c) in ("W", "F")
                        else (3 if c.isalpha() else 1) for r in g for c in r if c != " ")
                if best is None or s > best[0]:
                    best = (s, x, z, yaw)
    _, x, z, yaw = best
    g, c, _ = ac.render_street(ac.View(x, z, yaw, W, H), now)
    return g, c


def main():
    ac.WIDE_OK = True          # a real terminal reports this; headless does not
    ac._lots.clear()
    while ac.weather_name() != "dry":
        ac.cycle_weather()     # cloud eats the stars, and half the point of it
    here = os.path.dirname(os.path.abspath(__file__))
    docs = os.path.join(os.path.dirname(here), "docs")
    os.makedirs(docs, exist_ok=True)
    x0, z0 = ac.start_position()

    # A street, picking whichever chinatown view carries the most signage.
    best, score = None, -1
    for hop in range(6):
        sp = ac.find_place(x0 + hop * 700, z0 - hop * 500, "@3")
        if sp is None:
            continue
        g, _, _ = ac.render_street(ac.View(sp[0], sp[1], sp[2], W, H), 300.0)
        s = sum(40 if unicodedata.east_asian_width(c) in ("W", "F") else 1
                for r in g for c in r if c != " ")
        if s > score:
            best, score = sp, s
    g, c, _ = ac.render_street(ac.View(best[0], best[1], best[2], W, H), 300.0)
    write(docs, "street", g, c, "a street")

    # The rest under a sky held clear.
    while ac.clouds_name() != "clear":
        ac.cycle_clouds()

    # A lit alley, and a casino out on the avenue.
    g, c = best_view("yokocho", backs=(0.0, 4.0), turns=(0.0, math.pi))
    write(docs, "alley", g, c, "a lit alley")
    g, c = best_view("casino", backs=(0.0, 6.0, 12.0), turns=(0.0, -0.4, 0.4), hops=4)
    write(docs, "casino", g, c, "a casino on the avenue")

    # Inside the arcade, at the moment its cabinets have the most lit.
    sp = ac.find_place(x0, z0, "arcade")
    arc = None
    for k in range(40):
        place = ac.venue_at(sp[0] + math.sin(sp[2]) * k * 0.3,
                            sp[1] + math.cos(sp[2]) * k * 0.3)
        if place and place[0] == "arcade":
            arc = place[1]
            break
    now = max((300.0 + k * 0.37 for k in range(40)), key=lambda t: sum(
        1 for r in ac.render_arcade(arc, W, H, t)[0] for ch in r if ch != " "))
    g, c = ac.render_arcade(arc, W, H, now)
    write(docs, "arcade", g, c, "inside the arcade")


if __name__ == "__main__":
    main()
