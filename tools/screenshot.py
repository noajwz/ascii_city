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


def jet(home, x, z, heading, alt, now, outside=False, flaps=0, speed=70.0,
        pitch=0.0, lag=0.0):
    """A cockpit set up in the air, as if flown there, with nothing being said."""
    ck = ac.Cockpit(home, 0.0)
    ck.state, ck.alt, ck.v, ck.throttle, ck.flaps = "air", alt, speed, 0.6, flaps
    ck.x, ck.z, ck.heading, ck.pitch, ck.outside = x, z, heading, pitch, outside
    ck.said_at, ck.shown = -99.0, ck.said
    ck.cam = [heading - lag, alt + 1.5 + ac.CHASE_UP, now]
    return ac.render_cockpit(W, H, now, ck)


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

    # The waterfront, on the clearest night with the milky way up.
    night = max(range(300),
                key=lambda k: ac.night(k * ac.NIGHT_LENGTH + 200)["clarity"]
                + (0.3 if ac.night(k * ac.NIGHT_LENGTH + 200)["band"] else 0))
    g, c = ac.render_skyline(140.0, W, H, night * ac.NIGHT_LENGTH + 200)
    write(docs, "waterfront", g, c, "the waterfront")

    # The plane: on final to the first airport, from the seat and from behind,
    # with no storm about to spoil the view.
    home = ac.zone_home("airport", 100, 100)
    rx, zn, zs = ac.runway(*home)
    cells = ac.air_cells
    ac.air_cells = lambda x, z, now, reach=0.0: []
    g, c, _ = jet(home, rx + 2.0, zn + 350.0, math.pi, 30.0, 300.0, flaps=2,
                  speed=48.0, pitch=-0.03)
    write(docs, "cockpit", g, c, "on final")
    g, c, _ = jet(home, rx + 4.0, zn + 700.0, math.pi, 58.0, 300.0, outside=True,
                  flaps=2, speed=48.0, pitch=0.02, lag=-0.06)
    write(docs, "outside", g, c, "the jet from outside")
    ac.air_cells = cells

    # And a thunderstorm ahead, caught as it strikes.
    cell = min(ac.air_cells(rx, zn, 300.0, 20000.0),
               key=lambda cl: math.hypot(cl[0] - rx, cl[1] - zn))
    now = next(300.0 + k * 0.05 for k in range(2000)
               if (ac.air_strike(cell, 300.0 + k * 0.05) or (0.0,))[0] > 0.8)
    ahead = 0.8
    g, c, _ = jet(home, cell[0] - math.sin(ahead) * (cell[2] + 1200.0),
                  cell[1] - math.cos(ahead) * (cell[2] + 1200.0), ahead, 135.0, now)
    write(docs, "storm", g, c, "a storm ahead")

    # Inside the casino, the wheel going round.
    g, c = ac.render_casino_room(ac.Spin(500.0, "ROYALE"), W, H, 502.2,
                                 ac.Slot(ac.Wallet(1000)))
    write(docs, "casino", g, c, "the casino")


if __name__ == "__main__":
    main()
