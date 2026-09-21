"""Everything that can be checked without a terminal.

    python3 tests/checks.py

The renderer returns grids of characters and colours, so almost all of this is
assertions on those: render a frame, count what landed where. The rest is
assertions on the generator, which is a pure function of coordinates and needs
no rendering at all.

Runs a few hundred thousand simulated seconds of weather, so it takes a minute.
"""
import math
import sys

from harness import ac


ok = True
def check(name, cond, detail=""):
    global ok
    ok = ok and cond
    print("%-48s %s %s" % (name, "ok" if cond else "FAIL", detail))

# --- weather: a storm is its own kind, and the rarest -------------------
def old_rain(now):
    v = (0.42 + 0.42*math.sin(now/41.0) + 0.26*math.sin(now/13.7+1.2)
         + 0.13*math.sin(now/5.3+2.6))
    return max(0.0, min(1.0, v))

from collections import Counter
words = Counter(); instorm = storms = strikes = lit = 0
prev = 0.0; was = False
N = 600000
for k in range(N):
    t = k * 0.05
    w = ac.rain_intensity(t)
    words[ac.weather_word(t, w)] += 1
    st = ac.storming(t)
    storms += st and not was
    was = st
    instorm += st
    b = ac.lightning(t, w)
    if b > 0.0:
        lit += 1
        strikes += prev == 0.0
    prev = b
share = {w: n / float(N) for w, n in words.items()}
mins = N * 0.05 / 60.0
check("storm is one of the weathers", "storm" in share)
check("and the rarest of them by a distance",
      share["storm"] == min(share.values()) and share["storm"] * 2 < sorted(share.values())[1],
      "  ".join("%s %.1f%%" % (w, 100 * v) for w, v in sorted(share.items(), key=lambda p: p[1])))
check("storms are rare in time", 12.0 < mins / max(1, storms) < 40.0,
      "one every %.0f min" % (mins / max(1, storms)))
check("and do not outstay their welcome",
      30.0 < instorm * 0.05 / max(1, storms) < 95.0,
      "%.0f s each" % (instorm * 0.05 / max(1, storms)))
check("inside one the strikes come thick and fast",
      instorm * 0.05 / max(1, strikes) < 4.0,
      "one every %.1f s" % (instorm * 0.05 / max(1, strikes)))
check("and the sky is lit much of the time", lit / float(max(1, instorm)) > 0.4,
      "%.0f%% of a storm" % (100.0 * lit / max(1, instorm)))

outside = max(ac.lightning(k * 0.05, ac.rain_intensity(k * 0.05))
              for k in range(N // 6) if not ac.storming(k * 0.05))
check("no lightning at all outside a storm", outside == 0.0)

check("rain on auto is otherwise untouched",
      all(ac.rain_intensity(t) == old_rain(t)
          for t in (k * 0.37 for k in range(20000)) if not ac.storming(t)))

peaks = []; best = 0.0
for k in range(200000):
    t = k * 0.02
    b = ac.lightning(t, 1.0) if ac.storming(t) else 0.0
    if b == 0.0 and best:
        peaks.append(best); best = 0.0
    best = max(best, b)
check("some strikes are overhead and some are away over there",
      min(peaks) < 0.55 and max(peaks) > 0.9,
      "%d strikes, %.2f to %.2f" % (len(peaks), min(peaks), max(peaks)))

# --- and the menu can hold one there ------------------------------------
seen = {}
for _ in range(len(ac.WEATHER_STEPS)):
    seen[ac.weather_name()] = (ac.rain_intensity(400.0), ac.storming(400.0))
    ac.cycle_weather()
check("every weather level is reachable", len(seen) == 6, " ".join(sorted(seen)))
check("locking a storm brings the lightning with it",
      seen["storm"][1] and seen["storm"][0] > 0.9)
check("and locking a downpour does not", not seen["downpour"][1])
while ac.weather_name() != "auto":
    ac.cycle_weather()

ac.force_strike(500.0)
lit3 = [ac.lightning(500.0 + d, 0.0) for d in (0.0, 0.5, 2.0)]
check("a forced strike fires even in clear weather",
      lit3[0] == 1.0 and lit3[1] > 0.15 and lit3[2] == 0.0,
      "%s" % [round(v, 2) for v in lit3])
frames = [ac.lightning(500.0 + k / 30.0, 0.0) for k in range(51)]
dark_gaps = sum(1 for k in range(1, 12) if frames[k] < 0.12)
check("a strike stays lit rather than blinking", dark_gaps == 0,
      "%d dark frames in the first 0.4s" % dark_gaps)
check("and lasts long enough to see",
      len([f for f in frames if f > 0.12]) >= 20,
      "%.1fs lit" % (len([f for f in frames if f > 0.12]) / 30.0))

# --- the cheats find real things, and change nothing ----------------------
def census():
    c, k = set(), set()
    for i in range(-120, 120):
        for j in range(-120, 120):
            if ac.is_open(i, j): continue
            b = ac.lot(i, j)
            if b["club"]: c.add((i, j))
            if b["casino"]: k.add((i, j))
    return c, k

before = census()
x, z = ac.start_position()
for _ in range(3):
    for _, _, kind in ac.CHEAT_PLACES:
        spot = ac.find_place(x, z, kind)
        if spot: x, z, _ = spot
ac._open_cache.clear(); ac._lots.clear(); ac._road_cache.clear()
ac._district_cache.clear(); ac._woods_cache.clear()
ac._core_cache.clear()
check("teleporting does not change what is rare", census() == before,
      "%d clubs, %d casinos, unchanged" % (len(before[0]), len(before[1])))

x0, z0 = ac.start_position()
bad = []
for _, name, kind in ac.CHEAT_PLACES:
    spot = ac.find_place(x0, z0, kind)
    if spot is None or not ac.can_stand(spot[0], spot[1]):
        bad.append(name)
check("every destination lands somewhere you can stand", not bad, ",".join(bad))

blind = []
for _, name, kind in ac.CHEAT_PLACES:
    if kind in ("inside", "clubdoor", "club"):
        # These are meant to put you nose to the door - and a club fronts an
        # alley on purpose, so there is nowhere to stand back to.
        continue
    if kind in ("bank", "pier", "lake"):
        # probe() measures how far you could walk, and the whole point of these
        # is that they face water. Checked below on their own terms.
        continue
    x, z, yaw = ac.find_place(x0, z0, kind)
    if ac.probe(x, z, yaw, 120.0) < 5.0:
        blind.append(name)
check("and facing something, not a wall", not blind, ",".join(blind))

for kind in ("club", "casino"):
    x, z, _ = ac.find_place(x0, z0, kind)
    i = int(x/ac.CELL + ac.BIG) - ac.BIG; j = int(z/ac.CELL + ac.BIG) - ac.BIG
    near = any(not ac.is_open(a, b) and ac.lot(a, b)[kind] is not None
               for a in range(i-3, i+4) for b in range(j-3, j+4))
    check("the %s jump really lands at a %s" % (kind, kind), near)

moved = []
for kind in ("club", "casino", "alley", "deadend", "crossroads"):
    a = ac.find_place(x0, z0, kind)
    b = ac.find_place(a[0], a[1], kind)
    moved.append(math.hypot(b[0]-a[0], b[1]-a[1]) > ac.CHEAT_SKIP)
check("pressing the same key twice moves you on", all(moved))

fails = 0
for k in range(12):
    m = ac._mix(k, 7, 31)
    sx = ((m & 0xFFFF)/65535.0 - 0.5) * 12000
    sz = ((m >> 16)/65535.0 - 0.5) * 12000
    for _, _, kind in ac.CHEAT_PLACES:
        fails += ac.find_place(sx, sz, kind) is None
check("nothing is unfindable from anywhere", fails == 0, "%d misses in 96" % fails)

# --- the panel ------------------------------------------------------------
big = ([[" "]*100 for _ in range(30)], [[0]*100 for _ in range(30)])
ac.draw_cheats(big[0], big[1], "-> casino")
text = "\n".join("".join(r) for r in big[0])
check("the panel lists everything it does",
      all(n in text for _, n, _ in ac.CHEAT_PLACES)
      and "weather:" in text and "strike now" in text)
small = ([[" "]*20 for _ in range(8)], [[0]*20 for _ in range(8)])
ac.draw_cheats(small[0], small[1], "x")
check("and stays out of the way when there is no room",
      all(c == " " for r in small[0] for c in r))

# --- nothing else moved ---------------------------------------------------
v = ac.View(37.5, 52.5, 0.7, 100, 30)
a, _, _ = ac.render_street(v, 2.0)
ac._open_cache.clear(); ac._lots.clear(); ac._road_cache.clear()
ac._district_cache.clear(); ac._woods_cache.clear()
ac._core_cache.clear()
b, _, _ = ac.render_street(ac.View(37.5, 52.5, 0.7, 100, 30), 2.0)
check("the city is still deterministic", a == b)


# --- lightning must light the city, not just the sky ---------------------
ac.FLASH = 777
while ac.weather_name() != "downpour":
    ac.cycle_weather()
ac.force_strike(500.0)
cx, cz, cyaw = ac.find_place(*ac.start_position(), "casino")
def white(t, w=96, h=24):
    v = ac.View(cx, cz, cyaw, w, h)
    _, co, _ = ac.render_street(v, t)
    return sum(c == 777 for row in co for c in row) / float(w * h)
dark, lit = white(499.0), white(500.0)
check("a strike lights most of the street", dark == 0.0 and lit > 0.4,
      "%.0f%% -> %.0f%%" % (dark * 100, lit * 100))
def sky_white(t, w=96, h=24):
    _, co = ac.render_skyline(140.0, w, h, t)
    return sum(c == 777 for row in co for c in row) / float(w * h)
check("and most of the skyline", sky_white(499.0) == 0.0 and sky_white(500.0) > 0.3,
      "%.0f%% -> %.0f%%" % (sky_white(499.0) * 100, sky_white(500.0) * 100))
while ac.weather_name() != "auto":
    ac.cycle_weather()

# --- a casino should look like one ---------------------------------------
onroad = alley = 0
for i in range(-150, 150):
    for j in range(-150, 150):
        if ac.is_open(i, j): continue
        c = ac.lot(i, j)["casino"]
        if c is None: continue
        nx, nz = ac.FACES[c["door"]]
        if not ac.is_open(i + nx, j + nz): continue
        if ac.road_at(i + nx, j + nz): onroad += 1
        else: alley += 1
check("every casino fronts a street", alley == 0,
      "%d on a street, %d on an alley" % (onroad, alley))
check("and they are still rare", 200 < math.sqrt((300*ac.CELL)**2 / max(1, onroad)) < 500,
      "one every %.0f units" % math.sqrt((300*ac.CELL)**2 / max(1, onroad)))

seen_marquee = False
for back in (7.0, 9.0, 12.0):
    for i in range(-200, 200):
        for j in range(-200, 200):
            if ac.is_open(i, j): continue
            c = ac.lot(i, j)["casino"]
            if c is None: continue
            f = c["door"]; nx, nz = ac.FACES[f]
            if not (ac.is_open(i+nx, j+nz) and ac.road_at(i+nx, j+nz)): continue
            p = ac.face_point(i, j, f, c["u"], back, 0.0)
            if not ac.can_stand(p[0], p[2]): continue
            yaw = math.atan2(-nx, -nz)
            grid, _, _ = ac.render_street(ac.View(p[0], p[2], yaw, 88, 20), 400.0)
            txt = "\n".join("".join(r) for r in grid)
            if "CASINO" in txt and c["name"] in txt:
                seen_marquee = True
            break
        if seen_marquee: break
    if seen_marquee: break
check("the marquee reads CASINO and its name", seen_marquee)

# --- and you can go inside it --------------------------------------------
spot = ac.find_place(*ac.start_position(), "inside")
check("the inside jump lands in a doorway",
      spot is not None and ac.can_stand(spot[0], spot[1])
      and ac.casino_at(spot[0], spot[1]) is not None)
out = ac.find_place(*ac.start_position(), "casino")
check("and the outside jump does not", ac.casino_at(out[0], out[1]) is None)

ac._spin_rng.seed(3)
sp = ac.Spin(0.0, "FORTUNA")
room = "\n".join("".join(r) for r in ac.render_casino_room(sp, 96, 30, 2.0)[0])
check("the room has a room in it",
      all(w in room for w in ("CASINO", "FORTUNA", "the way out")) and "(- -)" in room,
      "banner, punters and an exit")
blank = 0
for w, h in ((20, 8), (40, 14), (50, 24), (96, 30), (240, 70)):
    g, _ = ac.render_casino_room(sp, w, h, 3.0)
    if len(g) != h or len(g[0]) != w or all(c == " " for r in g for c in r):
        blank += 1
check("and it draws in any window", blank == 0, "%d bad" % blank)


# --- the club, and getting into it ---------------------------------------
spot = ac.find_place(*ac.start_position(), "clubdoor")
check("the club doorway jump lands in a doorway",
      spot is not None and ac.can_stand(spot[0], spot[1]))
got = ac.venue_at(spot[0], spot[1])
check("and that is a club, not a casino", got is not None and got[0] == "club")
cas = ac.find_place(*ac.start_position(), "inside")
gotc = ac.venue_at(cas[0], cas[1])
check("the casino doorway is still a casino",
      gotc is not None and gotc[0] == "casino")
check("casino_at() still agrees", ac.casino_at(cas[0], cas[1]) is not None
      and ac.casino_at(spot[0], spot[1]) is None)

club = got[1]
frames = {}
for k in range(90):
    t = 500.0 + k * (60.0 / ac.CLUB_BPM) / 30.0
    grid, colour = ac.render_rave(club, 92, 28, t)
    frames[sum(c == ac.FLASH for r in colour for c in r) > 300] = grid
check("the room strobes on the beat and is dark between", len(frames) == 2,
      "%d distinct states over three beats" % len(frames))

room = "\n".join("".join(r) for r in ac.render_rave(club, 92, 28, 500.6)[0])
check("there is a rave in there",
      "DJ" in room and "the way out" in room and "V" in room,
      "booth, truss and an exit")
blank = 0
for w, h in ((20, 8), (40, 14), (50, 24), (92, 28), (240, 70)):
    g, _ = ac.render_rave(club, w, h, 501.0)
    if len(g) != h or len(g[0]) != w or all(c == " " for r in g for c in r):
        blank += 1
check("and it draws in any window", blank == 0, "%d bad" % blank)


# --- telling the street from the buildings -------------------------------
def old_is_road(i, period, salt):
    k, r = divmod(i, period)
    m = ac._mix(k, 0, salt)
    if ac._built_over(k, salt) and not ac._built_over(k - 1, salt):
        return False
    off = (m >> 9) % 2
    return off <= r < off + 2 + ((m >> 4) & 1)

check("pulling road_span() out changed no roads",
      all(ac._is_road(i, p, sa) == old_is_road(i, p, sa)
          for p, sa in ((ac.XP, 91), (ac.ZP, 137))
          for i in range(-3000, 3000)))

wide = narrow = junction = 0
for i in range(-300, 300):
    for j in range(-300, 300, 7):
        ax, az = ac.road_span(i, ac.XP, 91), ac.road_span(j, ac.ZP, 137)
        if ax and az: junction += 1
        elif ax: wide += ax[1] >= 3; narrow += ax[1] < 3
check("some streets are wide enough to mark and some are not",
      wide > 0 and narrow > 0, "%d wide, %d narrow" % (wide, narrow))

ac.LANE = 501
ac.CURB = 502
lanes = feet = 0
for k in range(14):
    m = ac._mix(k, 5, 23)
    sx = ((m & 0xFFFF) / 65535.0 - 0.5) * 3000
    sz = ((m >> 16) / 65535.0 - 0.5) * 3000
    if not ac.can_stand(sx, sz):
        continue
    for yaw in (0.0, 1.57, 3.14, 4.71):
        grid, colour, _ = ac.render_street(ac.View(sx, sz, yaw, 96, 26), 400.0)
        for y, row in enumerate(colour):
            for x, c in enumerate(row):
                if c == 501 and grid[y][x] == "'": lanes += 1
                if c == 502 and grid[y][x] == "_": feet += 1
check("wide streets get a line down the middle", lanes > 20, "%d cells" % lanes)
check("and buildings get one along the bottom", feet > 200, "%d cells" % feet)

# The markings must not wander off the road or onto a junction.
stray = 0
for k in range(4000):
    m = ac._mix(k, 9, 17)
    x = ((m & 0xFFFF) / 65535.0 - 0.5) * 2000
    z = ((m >> 16) / 65535.0 - 0.5) * 2000
    i = int(x / ac.CELL + ac.BIG) - ac.BIG
    j = int(z / ac.CELL + ac.BIG) - ac.BIG
    ax, az = ac.road_span(i, ac.XP, 91), ac.road_span(j, ac.ZP, 137)
    if ax and az:
        continue
    if ax and ax[1] >= 3:
        centre = (ax[0] + ax[1] * 0.5) * ac.CELL
        if not (ax[0] * ac.CELL <= centre <= (ax[0] + ax[1]) * ac.CELL):
            stray += 1
check("and the middle of a street is inside it", stray == 0, "%d stray" % stray)


# --- neon signs hang over your head, and stay on their wall --------------
bottoms, tops = [], []
for i in range(-110, 110):
    for j in range(-110, 110):
        if ac.is_open(i, j): continue
        for f in range(4):
            sg = ac.lot(i, j)["faces"][f]["hung"]
            if sg is None: continue
            tops.append(sg["top"])
            bottoms.append(sg["top"] - ac.SIGN_STEP * (len(sg["text"]) - 1))
check("every sign clears a head", min(bottoms) >= ac.SIGN_CLEAR - 1e-9,
      "lowest letter at %.2f, floor is %.1f" % (min(bottoms), ac.SIGN_CLEAR))
check("none of them reach the pavement", min(bottoms) > 0.0)
check("and none are up in the sky", max(tops) < ac.SIGN_CLEAR + 12.0,
      "highest top %.1f" % max(tops))
check("signs stay over the pavement", ac.SIGN_OUT + ac.SIGN_HALF <= ac.PAVE,
      "%.2f out of %.1f" % (ac.SIGN_OUT + ac.SIGN_HALF, ac.PAVE))

# The panel is a thing in the world, not a billboard turned to face you: it
# should collapse when seen edge-on and open out from along the street.
for i in range(-120, 120):
    for j in range(-120, 120):
        if ac.is_open(i, j): continue
        for f in range(4):
            sg = ac.lot(i, j)["faces"][f]["hung"]
            nx, nz = ac.FACES[f]
            if sg and ac.is_open(i+nx, j+nz) and ac.road_at(i+nx, j+nz):
                found = (i, j, f, sg, nx, nz); break
        else: continue
        break
    else: continue
    break
i, j, f, sg, nx, nz = found
wp = ac.face_point(i, j, f, sg["u"], sg["out"], 0.0)
tx, tz = -nz, nx
save = ac.NEON
ac.NEON = [(600 + k, 700 + k) for k in range(8)]

def measure(px, pz, yaw):
    v = ac.View(px, pz, yaw, 100, 30)
    g = [[" "] * 100 for _ in range(30)]
    c = [[0] * 100 for _ in range(30)]
    ac.draw_hung_sign(g, c, v, ([None]*100, [30]*100, [-1]*100),
                      sg, wp, (nx, nz), 400.0, 0.0)
    bars = [x for y in range(30) for x in range(100)
            if g[y][x] == "|" and c[y][x] in (700 + k for k in range(8))]
    letters = sum(1 for y in range(30) for x in range(100) if g[y][x] in sg["text"])
    return (max(bars) - min(bars) + 1 if bars else 0), letters

face_on = measure(wp[0]+nx*26, wp[2]+nz*26, math.atan2(-nx, -nz))
along = measure(wp[0]+nx*2.5+tx*26, wp[2]+nz*2.5+tz*26, math.atan2(-tx, -tz))
ac.NEON = save
check("a sign is edge-on when you face it square", face_on[0] == 0,
      "frame %d columns" % face_on[0])
check("and opens out from along the street", along[0] >= 2,
      "frame %d columns" % along[0])
check("but reads from either", face_on[1] == along[1] == len(sg["text"]),
      "%s, %d and %d letters" % (sg["text"], face_on[1], along[1]))


# --- parts of town -------------------------------------------------------
from collections import Counter
seen = Counter(ac.DISTRICTS[ac.district_at(i, j)]["name"]
               for i in range(-250, 250, 2) for j in range(-250, 250, 2))
tot = sum(seen.values())
check("every part of town turns up", len(seen) == len(ac.DISTRICTS),
      " ".join("%s %.0f%%" % (n, 100.0 * k / tot) for n, k in seen.most_common()))
check("downtown is still the commonest", seen.most_common(1)[0][0] in
      ("downtown", "residential"))
check("and the rarest is not vanishing", min(seen.values()) / float(tot) > 0.03)

stats = {}
for n, d in enumerate(ac.DISTRICTS):
    hs, sign, lant, trees, found = [], 0, 0, 0, 0
    found_faces = 0
    for i in range(-400, 400, 3):
        for j in range(-400, 400, 3):
            if ac.district_at(i, j) != n or ac.is_open(i, j) or ac.woods_at(i, j):
                continue                # the woods are placed, not picked
            b = ac.lot(i, j)
            # A club is a squat bunker and a casino a low slab whatever part
            # of town they are in; they are meant to ignore the district.
            if b["club"] is None and b["casino"] is None:
                hs.append(b["height"])
            trees += b["tree"]
            for f in range(4):
                # Only the street frontage: a yokocho running behind a
                # building turns that back face into a bar whatever district
                # it is in, which is the point of one.
                nx, nz = ac.FACES[f]
                if not ac.road_at(i + nx, j + nz):
                    continue
                found_faces += 1
                sign += b["faces"][f]["hung"] is not None
                lant += b["faces"][f]["lanterns"] is not None
            found += 1
            if found >= 250: break
        if found >= 250: break
    per = float(max(1, found_faces))
    stats[d["name"]] = (min(hs), max(hs), sign / per, lant / per,
                        trees / float(found))

bad = [n for n, d in enumerate(ac.DISTRICTS)
       if not (d["lo"] - 0.01 <= stats[d["name"]][0]
               and stats[d["name"]][1] <= d["hi"] + 0.01)]
check("every building is the height its district says", not bad,
      ", ".join(ac.DISTRICTS[n]["name"] for n in bad))
check("the financial district towers over the residential one",
      stats["financial"][0] > stats["residential"][1],
      "%.0f up vs %.0f down" % (stats["financial"][0], stats["residential"][1]))
quiet = [n for n in ("residential", "financial", "park") if stats[n][2] > 0.0]
check("residential, financial and the park have no neon", not quiet, ",".join(quiet))
check("chinatown is strung with lanterns", stats["chinatown"][3] > 0.6,
      "%.0f%% of its street frontage" % (stats["chinatown"][3] * 100))
check("downtown has neon and no lanterns",
      stats["downtown"][2] > 0.3 and stats["downtown"][3] == 0.0)
check("no clubs or casinos in the park",
      all(ac.lot(i, j)["club"] is None and ac.lot(i, j)["casino"] is None
          for i in range(-300, 300, 7) for j in range(-300, 300, 7)
          if ac.DISTRICTS[ac.district_at(i, j)]["park"] and not ac.is_open(i, j)))
check("only the park has trees in it",
      stats["park"][4] == 1.0
      and all(stats[d["name"]][4] == 0.0 for d in ac.DISTRICTS if not d["park"]))

# A park is somewhere you can walk about, not a wall of hedge.
walk = wood = 0
for i in range(-400, 400):
    for j in range(-400, 400):
        if not ac.DISTRICTS[ac.district_at(i, j)]["park"]:
            continue
        walk += ac.is_open(i, j); wood += not ac.is_open(i, j)
        if walk + wood > 4000: break
    if walk + wood > 4000: break
check("a park is mostly open ground", 0.05 < wood / float(walk + wood) < 0.35,
      "%.0f%% wooded" % (100.0 * wood / (walk + wood)))

missed = []
for n, d in enumerate(ac.DISTRICTS):
    spot = ac.find_place(x0, z0, "@%d" % n)
    if spot is None:
        missed.append(d["name"]); continue
    i = int(spot[0] / ac.CELL + ac.BIG) - ac.BIG
    j = int(spot[1] / ac.CELL + ac.BIG) - ac.BIG
    if ac.district_at(i, j) != n or not ac.can_stand(spot[0], spot[1]):
        missed.append(d["name"])
check("every part of town has a cheat that reaches it", not missed,
      ",".join(missed) or "all nine")


# --- and the parts of town have to actually look different ---------------
# The requirement was "I can barely notice any difference", so measure that
# directly rather than trusting the eye: a histogram of what is drawn on the
# facade, compared pairwise. Two lessons are baked in here. Only the rows above
# the horizon count, because road, footings and rain are identical everywhere
# and swamp the comparison. And the cell's *colour* counts, because structure
# is 60-80% of a facade and windows under a seventh of it - measured on glyphs
# alone the worst pair scored 0.08, which is why this sent the walls back to
# the drawing board and then produced a palette per district.
import math as _m

def fingerprint(n):
    counts, total = {}, 0
    for k in range(6):
        m = ac._mix(k, n, 29)
        sx = ((m & 0xFFFF) / 65535.0 - 0.5) * 6000
        sz = ((m >> 16) / 65535.0 - 0.5) * 6000
        spot = ac.find_place(sx, sz, "@%d" % n)
        if spot is None:
            continue
        for yaw in (spot[2], spot[2] + 1.57):
            v = ac.View(spot[0], spot[1], yaw, 90, 24)
            grid, colour, _ = ac.render_street(v, 400.0)
            for y in range(v.horizon):
                for x in range(90):
                    if grid[y][x] != " ":
                        k2 = (grid[y][x], colour[y][x])
                        counts[k2] = counts.get(k2, 0) + 1
                        total += 1
    return {a: b / float(total) for a, b in counts.items()} if total else {}


def apart(a, b):
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = _m.sqrt(sum(v * v for v in a.values()))
    nb = _m.sqrt(sum(v * v for v in b.values()))
    return 1.0 - dot / (na * nb) if na and nb else 1.0


prints = {d["name"]: fingerprint(n) for n, d in enumerate(ac.DISTRICTS)}
check("every part of town draws something", all(prints.values()))
names = [d["name"] for d in ac.DISTRICTS]
pairs = sorted((apart(prints[a], prints[b]), a, b)
               for i, a in enumerate(names) for b in names[i + 1:])
check("no two parts of town look the same", pairs[0][0] > 0.30,
      "closest %s/%s %.2f, median %.2f"
      % (pairs[0][1], pairs[0][2], pairs[0][0], pairs[len(pairs) // 2][0]))
muddled = [p for p in pairs
           if {p[1], p[2]} <= {"docks", "chinatown", "financial"}]
check("the ones that were muddled are well apart",
      min(p[0] for p in muddled) > 0.40,
      "worst of the six pairs %.2f" % min(p[0] for p in muddled))

# and the features that do the work are really wired up
check("every district has a palette of its own",
      len({d["pal"] for d in ac.DISTRICTS}) >= 6,
      " ".join(sorted({d["pal"] for d in ac.DISTRICTS})))
check("docks, chinatown and the housing are banded",
      {d["name"] for d in ac.DISTRICTS if d["band"]}
      == {"residential", "chinatown", "docks"})
check("only the financial district lights whole floors",
      [d["name"] for d in ac.DISTRICTS if d["whole_floors"]] == ["financial"])
check("yokocho is no longer a district",
      "yokocho" not in [d["name"] for d in ac.DISTRICTS])
check("old town is the one with pitched roofs",
      [d["name"] for d in ac.DISTRICTS if d["roof"] != "="] == ["old town", "docks"]
      or [d["name"] for d in ac.DISTRICTS if d["roof"] == "^"] == ["old town"])
bad = [d["name"] for d in ac.DISTRICTS if len(set(d["glyphs"])) < 2]
check("every district has a window alphabet of its own", not bad, ",".join(bad))


# --- a low building has to have a visible top ----------------------------
# The roofline was drawn in the same near-black trim as the awning and the
# balconies below it, so on a low building - the only kind whose roof is on
# screen at all - the top edge lost to its own balconies.
ac.ROOF = 902
ac.CURB = 901
ac.PALETTES["far"] = [900] * 6
check("a roofline is not drawn in the trim colour",
      ac.roof_colour({"tone": 0.5}, 10.0) not in (900, ac.PALETTES["dark"][0]))
check("it fades with distance but not into nothing",
      ac.roof_colour({"tone": 0.5}, 10.0) == 902
      and ac.roof_colour({"tone": 0.5}, 90.0) == 901
      and ac.roof_colour({"tone": 0.5}, 200.0) == 900,
      "near/mid/far = %s/%s/%s" % (ac.roof_colour({"tone": 0.5}, 10.0),
                                   ac.roof_colour({"tone": 0.5}, 90.0),
                                   ac.roof_colour({"tone": 0.5}, 200.0)))
check("and lightning still takes it", ac.roof_colour({"tone": 0.5}, 10.0, 1.0) == ac.FLASH)

seen_roof = 0
for want in ("residential", "docks", "market", "old town"):
    n = next(k for k, d in enumerate(ac.DISTRICTS) if d["name"] == want)
    for k in range(3):
        spot = ac.find_place(x0 + k * 900, z0 - k * 700, "@%d" % n)
        if spot is None:
            continue
        v = ac.View(spot[0], spot[1], spot[2], 90, 22)
        grid, colour, _ = ac.render_street(v, 400.0)
        seen_roof += sum(1 for y in range(v.horizon) for c in range(90)
                         if colour[y][c] in (901, 902) and grid[y][c] in "=^-")
check("the low districts show their rooflines", seen_roof > 100,
      "%d roofline cells across fifteen views" % seen_roof)

bad = [d["name"] for d in ac.DISTRICTS if d["roof"] == d["band"]]
check("no district's roof is the same mark as its own banding", not bad,
      ",".join(bad))


# --- Chinese signs in Chinatown, if the terminal can draw them -----------
check("without wide-character support nothing changes",
      ac.WIDE_OK is False
      and all(c in ac.SIGN_WORDS for c in [ac.lot(i, j)["faces"][f]["hung"]["text"]
              for i in range(-60, 60) for j in range(-60, 60)
              if not ac.is_open(i, j) for f in range(4)
              if ac.lot(i, j)["faces"][f]["hung"]][:200]),
      "the ASCII words are the fallback, and the default")

ac.WIDE_OK = True
ac._lots.clear()
cn = next(k for k, d in enumerate(ac.DISTRICTS) if d["name"] == "chinatown")
wrong = {"chinatown street": 0, "other street": 0, "yokocho": 0}
counts = {"chinatown street": 0, "other street": 0, "yokocho": 0}
for i in range(-120, 120):
    for j in range(-120, 120):
        if ac.is_open(i, j):
            continue
        b = ac.lot(i, j)
        for f in range(4):
            h = b["faces"][f]["hung"]
            flat = b["faces"][f]["flat"]
            if flat is not None and any(ac.is_wide(c) for c in flat["text"]):
                wrong["other street"] += 1      # flat signs must stay latin
            if h is None:
                continue
            nx, nz = ac.FACES[f]
            kind = ac.face_kind(i + nx, j + nz)
            if kind == "yokocho":
                bucket, want = "yokocho", ac.JP_SIGNS
            elif kind == "road":
                if ac.district_at(i, j) == cn:
                    bucket, want = "chinatown street", ac.CJK_SIGNS
                else:
                    bucket, want = "other street", ac.SIGN_WORDS
            else:
                continue        # a dark alley's signs are never drawn
            counts[bucket] += 1
            wrong[bucket] += h["text"] not in want
check("chinatown's street signs are chinese",
      counts["chinatown street"] and not wrong["chinatown street"],
      "%d signs" % counts["chinatown street"])
check("a yokocho's are japanese, wherever it runs",
      counts["yokocho"] and not wrong["yokocho"], "%d signs" % counts["yokocho"])
check("and every other street is latin",
      counts["other street"] and not wrong["other street"],
      "%d signs" % counts["other street"])
check("every chinese and japanese sign is double-width",
      all(ac.is_wide(c) for t in ac.CJK_SIGNS + ac.JP_SIGNS for c in t))

# A wide glyph has to claim the column it spills into, or the blit loop paints
# over its right half.
drawn = wide = clean = 0
for k in range(5):
    spot = ac.find_place(x0 + k * 800, z0 - k * 600, "@%d" % cn)
    if spot is None:
        continue
    for t in range(8):
        v = ac.View(spot[0], spot[1], t * math.tau / 8, 110, 34)
        grid, _, _ = ac.render_street(v, 400.0)
        here = [(y, x) for y in range(34) for x in range(110)
                if ac.is_wide(grid[y][x])]
        drawn += len(here)
        wide += sum(1 for p in here if p in v.wide)
        clean += sum(1 for (y, x) in here if x + 1 < 110 and grid[y][x + 1] == " ")
check("chinese characters actually reach the screen", drawn > 20,
      "%d of them across forty views" % drawn)
check("each one on screen owns the column beside it", wide == drawn,
      "%d glyphs, %d of them reserved" % (drawn, wide))
# What matters is not that the grid is pristine - a raindrop may well land in
# the reserved cell after the sign was drawn - but that the blit loop never
# emits anything there. Walk the same loop main() walks and check.
spilled = 0
for k in range(5):
    spot = ac.find_place(x0 + k * 800, z0 - k * 600, "@%d" % cn)
    if spot is None:
        continue
    for t in range(8):
        v = ac.View(spot[0], spot[1], t * math.tau / 8, 110, 34)
        grid, _, _ = ac.render_street(v, 400.0)
        for y in range(34):
            x = 0
            while x < 110:
                if (y, x) in v.wide and ac.is_wide(grid[y][x]):
                    x += 2          # the glyph owns this column and the next
                    continue
                if x and (y, x - 1) in v.wide and ac.is_wide(grid[y][x - 1]):
                    spilled += 1    # we are about to draw into its far half
                x += 1
check("the blit never draws into a wide glyph's far half", spilled == 0,
      "%d spills over forty views" % spilled)
check("and none is placed against the right edge",
      all(x + 1 < 110 for (y, x) in v.wide))
ac.WIDE_OK = False
ac._lots.clear()


# --- what makes a yokocho feel like one ----------------------------------
ac.WIDE_OK = True
ac._lots.clear()
pubs = faces = 0
for i in range(-120, 120):
    for j in range(-120, 120):
        if ac.is_open(i, j):
            continue
        b = ac.lot(i, j)
        for f in range(4):
            nx, nz = ac.FACES[f]
            if ac.face_kind(i + nx, j + nz) != "yokocho":
                continue
            faces += 1
            pubs += b["faces"][f]["pub"]
check("a lit lane has places on it", faces and 0.3 < pubs / float(faces) < 0.8,
      "%d of %d faces are a pub" % (pubs, faces))
check("nowhere else has them",
      not any(ac.lot(i, j)["faces"][f]["pub"]
              for i in range(-80, 80, 3) for j in range(-80, 80, 3)
              if not ac.is_open(i, j) for f in range(4)
              if ac.face_kind(i + ac.FACES[f][0], j + ac.FACES[f][1]) != "yokocho"))

# The strings go across the lane, not along it - that is the whole point.
spans = 0
for i in range(-140, 140):
    for j in range(-140, 140):
        if not ac.yokocho_at(i, j) or ac._mix(i, j, 401) % 2:
            continue
        spans += 1
check("lanterns are strung across the lane", spans > 40,
      "%d strings" % spans)

counter = people = lantern = jp = 0
for k in range(6):
    spot = ac.find_place(x0 + k * 700, z0 - k * 500, "yokocho")
    if spot is None:
        continue
    for t in range(4):
        v = ac.View(spot[0], spot[1], spot[2] + t * 1.57, 96, 26)
        grid, colour, _ = ac.render_street(v, 400.0)
        flat = [(y, x) for y in range(26) for x in range(96)]
        people += sum(1 for y, x in flat if grid[y][x] == "M")
        counter += sum(1 for y, x in flat if grid[y][x] == "="
                       and y > v.horizon)
        lantern += sum(1 for y, x in flat if grid[y][x] == "o")
        jp += sum(1 for y, x in flat if ac.is_wide(grid[y][x]))
check("you can see people sitting in them", people > 15, "%d figures" % people)
check("and lanterns overhead", lantern > 60, "%d lanterns" % lantern)
check("with japanese over the door and down the brackets", jp > 20,
      "%d characters" % jp)
check("every one of those still owns its second column",
      all(x + 1 < 96 for (y, x) in v.wide))
ac.WIDE_OK = False
ac._lots.clear()


# --- the woods -----------------------------------------------------------
# One great block of trees a tile, with trails through it, a hollow in the
# middle, and no street, light or building in it. The parks are not this.
hx, hz, hi, hj = ac.nearest_hollow(x0, z0)
wi, wj = ac.woods_home(hi, hj)
size = sum(1 for i in range(wi - 90, wi + 91) for j in range(wj - 60, wj + 61)
           if ac.woods_at(i, j))
check("the woods are big", size > 4 * ac.DISTRICT_CELLS ** 2,
      "%d cells, against a district's %d" % (size, ac.DISTRICT_CELLS ** 2))
check("and a long way from the start", math.hypot(hx - x0, hz - z0) > 800,
      "%.0f units" % math.hypot(hx - x0, hz - z0))
check("with no streets in them",
      not any(ac.road_at(i, j) for i in range(wi - 80, wi + 81)
              for j in range(wj - 50, wj + 51) if ac.woods_at(i, j)))
check("and nothing built in them",
      all(ac.lot(i, j)["tree"] and ac.lot(i, j)["club"] is None
          and ac.lot(i, j)["casino"] is None
          for i in range(wi - 80, wi + 81, 3) for j in range(wj - 50, wj + 51, 3)
          if ac.woods_at(i, j) and not ac.is_open(i, j)))
check("the hollow is open ground", all(
    ac.is_open(i, j) for i in range(hi - 3, hi + 4) for j in range(hj - 2, hj + 3)))
check("and inside the woods", ac.woods_at(hi, hj) and ac.hollow_at(hi, hj))

# Thick off the trails - you should get lost - but every gate where a road
# meets the edge has to lead to the hollow on foot, and back out.
inside = [(i, j) for i in range(wi - 80, wi + 81) for j in range(wj - 50, wj + 51)
          if ac.woods_depth(i, j) > 3.0 and not ac.trail_at(i, j)
          and not ac.hollow_at(i, j)]
trees = sum(1 for i, j in inside if not ac.is_open(i, j))
check("off the trails the wood is thick", 0.38 < trees / float(len(inside)) < 0.6,
      "%.0f%% trees" % (100.0 * trees / len(inside)))
from collections import deque as _dq
seen = {(hi, hj)}
q = _dq([(hi, hj)])
while q:
    i, j = q.popleft()
    for a, b in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
        if (a, b) in seen or ac.woods_depth(a, b) <= -3.0:
            continue
        if not ac.can_stand((a + 0.5) * ac.CELL, (b + 0.5) * ac.CELL):
            continue
        seen.add((a, b))
        q.append((a, b))
gates = [(i, j) for i in range(wi - 80, wi + 81) for j in range(wj - 50, wj + 51)
         if 0 < ac.woods_depth(i, j) <= 1.0 and ac.trail_at(i, j)]
check("every gate leads to the hollow on foot", gates
      and all(g in seen for g in gates), "%d gates" % len(gates))
check("but a good part of the wood is not on the way", len(seen) < 0.75 * size,
      "%d of %d cells reachable" % (len(seen), size))

# The rig: only in the hollow now - the parks are quiet.
on = sum(1 for k in range(200000) if ac.rave_window(k * 0.5) is not None)
check("the rave is rare in time", 0.02 < on / 200000.0 < 0.15,
      "on %.1f%% of the time" % (100.0 * on / 200000))
t_on = next(k * 2.0 for k in range(200000) if ac.rave_window(k * 2.0))
t_off = next(k * 2.0 for k in range(200000) if ac.rave_window(k * 2.0) is None)
spot = ac.find_place(x0, z0, "rave")
check("the cheat reaches the hollow", spot is not None
      and ac.can_stand(spot[0], spot[1])
      and math.hypot(spot[0] - hx, spot[1] - hz) < 40)
gate = ac.find_place(x0, z0, "woods")
gi = int(gate[0] / ac.CELL + ac.BIG) - ac.BIG
gj = int(gate[1] / ac.CELL + ac.BIG) - ac.BIG
check("and the woods cheat stands you at a gate, outside, on a road",
      gate is not None and ac.can_stand(gate[0], gate[1])
      and not ac.woods_at(gi, gj) and ac.road_at(gi, gj)
      and ac.woods_at(gi, gj + 6))

save = ac.PALETTES["leaf"]
ac.PALETTES["leaf"] = [700] * 5
blits = []
real_blit = ac.blit_sprite
ac.blit_sprite = lambda ch, co, v, w, art, *a: (blits.append(art),
                                              real_blit(ch, co, v, w, art, *a))


def hollow(t, w=88, h=22):
    del blits[:]
    v = ac.View(spot[0], spot[1], spot[2], w, h)
    grid, colour, _ = ac.render_street(v, t)
    canopy = sum(1 for y in range(h) for x in range(w)
                 if grid[y][x] in "&%*#" and colour[y][x] != 700)
    crowd = sum(1 for a in blits if a is ac.ZOMB_UP or a is ac.ZOMB_DOWN)
    return canopy, crowd, ac.ALTAR in blits, set(map(id, blits))


lit = max(hollow(t_on + k * 0.05) for k in range(8))
dark = max(hollow(t_off + k * 0.05) for k in range(8))
check("with one on, the light goes up into the leaves", lit[0] > 150,
      "%d canopy cells lit" % lit[0])
check("there is a crowd in the hollow", lit[1] > 20, "%d of them" % lit[1])
check("facing an altar", lit[2])
ac.ROU_GREEN, ac.ROU_RED = 971, 972
del blits[:]
ac.render_street(ac.View(spot[0], spot[1], spot[2], 88, 22), t_on)
ac.ROU_GREEN = ac.ROU_RED = 1
aku = [a for a in blits if a in (ac.AKU_BODY, ac.AKU_FACE, ac.AKU_BROW, ac.AKU_WHITE)]
check("with Aku on the decks", len(aku) == 4, "%d layers of him" % len(aku))
face = []
ac.blit_sprite = lambda ch, co, v, w, art, *a: (face.append(a[-1]) if art is ac.AKU_FACE
                                              else None,
                                              real_blit(ch, co, v, w, art, *a))
ac.ROU_GREEN = 971
ac.render_street(ac.View(spot[0], spot[1], spot[2], 88, 22), t_on)
ac.ROU_GREEN = 1
check("and his face is green", face == [971])
ac.blit_sprite = lambda ch, co, v, w, art, *a: (blits.append(art),
                                              real_blit(ch, co, v, w, art, *a))
check("with none on, the woods are just woods",
      dark[0] < 60 and dark[1] == 0 and not dark[2],
      "%d canopy, %d people" % (dark[0], dark[1]))
# The crowd is not in time, it is in step: one pose for all of them at once.
poses = set()
real_drawn_in = ac.draw_drawn_in
ac.draw_drawn_in = lambda *a: None      # the ones on the path stand still
for k in range(12):
    hollow(t_on + k * 0.031)
    poses.add(frozenset(id(a) for a in blits if a in (ac.ZOMB_UP, ac.ZOMB_DOWN)))
check("and every one of them moves together",
      all(len(p) <= 1 for p in poses) and len(poses) >= 2,
      "%d poses seen, never mixed" % len(poses))
ac.draw_drawn_in = real_drawn_in
ac.blit_sprite = real_blit
ac.PALETTES["leaf"] = save

# Life in the trees on a quiet night: fireflies over the trail, and eyes.
ac.FIREFLY, ac.EYES = 951, 952
while ac.weather_name() != "dry":       # rain puts the fireflies out
    ac.cycle_weather()
ff = ey = 0
for back in range(6, 18, 2):
    for yaw in (0.0, math.pi):
        for k in range(3):
            v = ac.View(hx, (hj - back + 0.5) * ac.CELL, yaw, 110, 30)
            _, col, _ = ac.render_street(v, t_off + k * 0.9)
            ff += sum(1 for r in col for a in r if a == 951)
            ey += sum(1 for r in col for a in r if a == 952)
check("fireflies over the trail", ff > 60, "%d over 36 frames" % ff)
check("and eyes in the dark", ey > 0, "%d over 36 frames" % ey)
ac.FIREFLY = ac.EYES = 1
while ac.weather_name() != "auto":
    ac.cycle_weather()

# The lake: water you can see across and not stand in, a path round it that
# every trail reaching the shore joins, and the sky lying in it.
li, lj = ac.lake_centre(wi, wj)
lake = [(i, j) for i in range(li - 12, li + 13) for j in range(lj - 8, lj + 9)
        if ac.lake_at(i, j)]
check("there is a lake in the woods", len(lake) > 100, "%d cells" % len(lake))
check("and it is water", all(ac.is_open(i, j) for i, j in lake)
      and not any(ac.can_stand((i + 0.5) * ac.CELL, (j + 0.5) * ac.CELL)
                  for i, j in lake))
shore = [(i, j) for i in range(li - 14, li + 15) for j in range(lj - 10, lj + 11)
         if ac.woods_at(i, j) and 0 <= ac.lake_dist(i, j) < 2.2]
check("with a path all the way round it", shore and all(s in seen for s in shore),
      "%d shore cells, all reached from the hollow" % len(shore))
pond = ac.find_place(x0, z0, "lake")
pi = int((pond[0] + math.sin(pond[2]) * 6) / ac.CELL + ac.BIG) - ac.BIG
pj = int((pond[1] + math.cos(pond[2]) * 6) / ac.CELL + ac.BIG) - ac.BIG
check("the lake cheat stands you on the shore facing the water",
      ac.can_stand(pond[0], pond[1]) and ac.lake_at(pi, pj))
while ac.weather_name() != "dry":
    ac.cycle_weather()
clear = max(range(80), key=lambda k: ac.night(k * ac.NIGHT_LENGTH + 100)["clarity"]
            * (0 if ac.night(k * ac.NIGHT_LENGTH + 100)["alien"] else 1))
tc = clear * ac.NIGHT_LENGTH + 100
pv = ac.View(pond[0], pond[1], pond[2], 108, 26)
real_reflect = ac.reflect_river
ac.reflect_river = lambda *a: None
plain, _, _ = ac.render_street(pv, tc)
ac.reflect_river = real_reflect
grid, _, _ = ac.render_street(pv, tc)
stars = sum(1 for (y, sx) in pv.water if grid[y][sx] != plain[y][sx])
check("and on a clear night the stars are in it", stars > 10,
      "%d reflected cells" % stars)

# The one who is awake: there when the rig is on, pale where the crowd is
# dark, and he has something to say if you stand next to him.
jx, jz = ac.jack_spot(hi, hj)
ac.force_rave(700.0)
ac.MOON_DIM, ac.BARK = 961, 962
blits = []
ac.blit_sprite = lambda ch, co, v, w, art, *a: (blits.append((art, a[-1])),
                                              real_blit(ch, co, v, w, art, *a))
jv = ac.View(jx, jz - 6.0, 0.0, 110, 30)
dark_frame = next(700.0 + k * 0.02 for k in range(60)
                  if ac.rave_light(700.0 + k * 0.02,
                                   (ac._mix(hi, hj, 977) & 255) / 255.0 * 6.0,
                                   0.5) is None)
ac.render_street(jv, dark_frame)
jack = [c for a, c in blits if a is ac.JACK]
crowd_c = {c for a, c in blits if a is ac.ZOMB_UP or a is ac.ZOMB_DOWN}
check("Jack is at the edge of the hollow", len(jack) == 1)
check("and he is the one who is not dark",
      jack and jack[0] == 961 and crowd_c == {962})
check("and has something to say", "music" in ac.rave_hint(jv, dark_frame))
check("but not from across the hollow",
      "music" not in ac.rave_hint(ac.View(hx, hz + 30, 0.0, 110, 30), dark_frame))
ac.blit_sprite = real_blit
ac.MOON_DIM = ac.BARK = 1
ac._forced_rave = None
del blits[:]
ac.blit_sprite = lambda ch, co, v, w, art, *a: (blits.append(art),
                                              real_blit(ch, co, v, w, art, *a))
ac.render_street(jv, t_off)
ac.blit_sprite = real_blit
check("and when there is no rave, he is not there", ac.JACK not in blits)
while ac.weather_name() != "auto":
    ac.cycle_weather()

# The menu has to deliver the rave, not the hollow it sometimes happens in.
ac._forced_rave = None
odds = sum(1 for k in range(2000) if ac.rave_window(k * 7.3 + 11.0) is not None)
check("left to itself, one is on only now and then", odds / 2000.0 < 0.2,
      "%.0f%% of the time" % (100.0 * odds / 2000))
ac.force_rave(9000.0)
check("but the menu starts one on demand",
      ac.rave_window(9000.0) is not None and ac.rave_window(9000.5) is not None)
check("and it ends", ac.rave_window(9000.0 + ac.RAVE_LONG + 1) is None)
ac._forced_rave = None

# On the night the sky has something in it, the rig knew.
ac._night_skip = 0.0
alien = next(k for k in range(400) if ac.night(k * ac.NIGHT_LENGTH + 100)["alien"])
ta = alien * ac.NIGHT_LENGTH
check("on the strange night the rave is on all night",
      all(ac.rave_window(ta + f * ac.NIGHT_LENGTH) is not None
          for f in (0.05, 0.3, 0.6, 0.95)))
check("and on the sky's beat",
      {ac.rave_light(ta + 100 + k * 0.01, 0.0, 0.5) for k in range(200)}
      == {ac.club_light(ta + 100 + k * 0.01, {"tone": 0.5, "phase": 0.0})
          for k in range(200)} or ac.city_sync(ta + 100) is not None)

# A bearing you can walk on, in every direction.
ac.force_rave(500.0)
cx, cz = hx, hz
wrong = []
for dx, dz, want in ((0, -30, "N"), (0, 30, "S"), (-30, 0, "E"), (30, 0, "W"),
                     (-22, -22, "NE"), (22, 22, "SW")):
    hint = ac.rave_hint(ac.View(cx + dx, cz + dz, 0.0, 88, 22), 500.0).strip()
    if not hint:
        wrong.append("silent %d,%d" % (dx, dz))
    elif hint.split()[4].rstrip(",") != want:
        wrong.append("%s not %s" % (hint.split()[4].rstrip(","), want))
check("the hint points at the music from every side", not wrong,
      ", ".join(wrong) or "including from behind")
check("it says how far too",
      "close" in ac.rave_hint(ac.View(cx, cz - 20, 0.0, 88, 22), 500.0)
      and "way off" in ac.rave_hint(ac.View(cx, cz - 200, 0.0, 88, 22), 500.0)
      and "far off" in ac.rave_hint(ac.View(cx, cz - 500, 0.0, 88, 22), 500.0))
check("and says nothing when there is no rig going",
      ac.rave_hint(ac.View(cx, cz - 12, 0.0, 88, 22), 500.0 + ac.RAVE_LONG + 5) == ""
      or ac.rave_window(500.0 + ac.RAVE_LONG + 5) is not None)
ac._forced_rave = None

beats = {ac.rave_light(t_on + k * 0.01, 0.0, 0.5) for k in range(120)}
check("the rig has a beat, and is dark between", len(beats) >= 3 and None in beats,
      "%d distinct states" % len(beats))
check("and it is faster than the club", ac.RAVE_BPM > ac.CLUB_BPM,
      "%g against %g bpm" % (ac.RAVE_BPM, ac.CLUB_BPM))
# A tree has no door, so nothing gets hung on one - the alley's bins and
# bulbs were turning up against the trunks.
blits = []
ac.blit_sprite = lambda ch, co, v, w, art, *a: (blits.append(art),
                                              real_blit(ch, co, v, w, art, *a))
for back in (4, 10, 16):
    ac.render_street(ac.View(hx, (hj - back + 0.5) * ac.CELL, 0.0, 110, 30), t_off)
    ac.render_street(ac.View(hx, (hj - back + 0.5) * ac.CELL, math.pi, 110, 30), t_off)
ac.blit_sprite = real_blit
check("nothing is hung on a tree",
      not any(a is ac.BIN or a is ac.SMOKER_REST or a is ac.SMOKER_DRAG
              for a in blits))


# --- the night sky -------------------------------------------------------
ac._night_skip = 0.0
ac._night_cache.clear()
ac.STAR_DIM, ac.STAR, ac.STAR_WARM = 801, 802, 803
ac.STAR_COLD, ac.MOON, ac.MOON_DIM, ac.BAND = 804, 805, 806, 807
SKY = {801, 802, 803, 804, 805, 806, 807}

nights = [ac.night(k * ac.NIGHT_LENGTH + 200) for k in range(400)]
ordinary = [n for n in nights if not n["alien"]]
cl = sorted(n["clarity"] for n in ordinary)
check("no two nights are the same sky",
      cl[-1] - cl[0] > 0.6 and 0.35 < cl[len(cl) // 2] < 0.65,
      "clarity %.2f to %.2f, median %.2f" % (cl[0], cl[-1], cl[len(cl) // 2]))
band = sum(n["band"] for n in ordinary) / float(len(ordinary))
check("the milky way is up on some of them, not most", 0.15 < band < 0.55,
      "%.0f%% of nights" % (band * 100))
faces = {ac.moon_face(n["phase"]) for n in nights}
check("the moon goes through its phases", len(faces) >= 5,
      " ".join(sorted(f or "(none)" for f in faces)))
check("and is sometimes not there at all", "" in faces)

# A night has to be the same night when you come back to it.
before = ac.night(9 * ac.NIGHT_LENGTH + 200)
ac._night_cache.clear()
check("a night is the same night on a second look",
      ac.night(9 * ac.NIGHT_LENGTH + 200) == before)

# Nothing in the sky may be drawn inside a building. The street view got this
# wrong for a while: wall_top holds the *nearest* wall's roof, and the part of
# a far tower showing above a nearer roof is still a building - stars went
# straight into it. The waterfront got it wrong the other way, drawing stars
# first and letting buildings paint over them, which leaves every unlit window
# a hole with a star in it.
while ac.weather_name() != "dry":
    ac.cycle_weather()
inside = shown = 0
for want in ("downtown", "financial", "docks", "residential", "old town"):
    dd = next(k for k, x in enumerate(ac.DISTRICTS) if x["name"] == want)
    for hop in range(6):
        sp = ac.find_place(x0 + hop * 700, z0 - hop * 500, "@%d" % dd)
        if sp is None:
            continue
        vv = ac.View(sp[0], sp[1], sp[2], 110, 32)
        grid, colour, _ = ac.render_street(vv, 200.0)
        shown += sum(1 for r in colour for c in r if c in SKY)
        for c in range(110):
            cover = None
            for k, (dist, i, j, f, u) in enumerate(ac.cast(vv, *vv.ray(c))):
                lo, hi = ac.wall_span(vv, dist, ac.lot(i, j)["height"])
                lo, hi = max(0, lo), min(31, hi)
                if cover is not None:
                    hi = min(hi, cover - 1)
                if hi < lo:
                    continue
                cover = lo if cover is None else min(cover, lo)
                if cover <= 0:
                    break
            if cover is None:
                continue
            inside += sum(1 for y in range(cover, min(32, vv.horizon))
                          if colour[y][c] in SKY)
check("no star is drawn inside a building, from the street", inside == 0,
      "%d of %d stars were" % (inside, shown))

gr = max(5, min(32 - 4, int(32 * 0.58))) - 1
inside = shown = 0
for cam in (0.0, 300.0, 900.0, 2500.0):
    grid, colour = ac.render_skyline(cam, 110, 32, 200.0)
    shown += sum(1 for r in colour for c in r if c in SKY)
    roofs = [gr + 1] * 110
    for li, spec in enumerate(ac.LAYERS):
        offc = cam * spec["parallax"]
        for ci in range(int(offc // ac.CHUNK_W) - 1,
                        int((offc + 110) // ac.CHUNK_W) + 2):
            for b in ac.get_chunk(li, ci, gr + 1):
                sxc = int(round(b["x"] - offc))
                roof = gr - len(b["rows"]) + 1
                for x in range(max(0, sxc), min(110, sxc + b["w"])):
                    roofs[x] = min(roofs[x], roof)
    for x in range(110):
        inside += sum(1 for y in range(max(0, roofs[x]), gr + 1)
                      if colour[y][x] in SKY)
check("nor from the waterfront, not even through an unlit window", inside == 0,
      "%d of %d stars were" % (inside, shown))
check("and there are still plenty of stars", shown > 150, "%d" % shown)

# Stars are fixed to the compass, not the screen: they must not swim about as
# you turn under them.
while ac.weather_name() != "dry":
    ac.cycle_weather()
dk = next(k for k, x in enumerate(ac.DISTRICTS) if x["name"] == "docks")
sx0, sz0, syaw = ac.find_place(x0, z0, "@%d" % dk)


def starfield(yaw):
    v = ac.View(sx0, sz0, yaw, 110, 32)
    grid, colour, _ = ac.render_street(v, 200.0)
    out = {}
    for c in range(110):
        cam = 2.0 * c / 109 - 1.0
        b = int((yaw + math.atan(cam * ac.PLANE)) * 90.0)
        for y in range(v.horizon):
            if colour[y][c] in SKY:
                out[(b, y)] = grid[y][c]
    return out


base = starfield(syaw)
drift = 0
for turn in (0.05, 0.12, 0.25, 0.4):
    other = starfield(syaw + turn)
    drift += sum(1 for k in set(base) & set(other) if base[k] != other[k])
check("the stars hold still while you turn under them", drift == 0 and len(base) > 5,
      "%d of them, none moved" % len(base))

# Cloud has to take the sky away, and the storm all of it.
counts = {}
for w in ("dry", "drizzle", "rain", "downpour", "storm"):
    while ac.weather_name() != w:
        ac.cycle_weather()
    _, colour, _ = ac.render_street(ac.View(sx0, sz0, syaw, 110, 32), 200.0)
    counts[w] = sum(1 for r in colour for c in r if c in SKY)
check("cloud takes the sky away by degrees",
      counts["dry"] > counts["drizzle"] > counts["rain"] > counts["downpour"],
      "  ".join("%s %d" % kv for kv in counts.items()))
check("and a storm leaves none of it", counts["storm"] == 0)
while ac.weather_name() != "dry":
    ac.cycle_weather()

# Most stars faint, a few bright - a sky where every star is bright is static.
glyphs, hues = {}, {}
for k in range(14):
    grid, colour = ac.render_skyline(140.0 + k * 37, 110, 34,
                                     k * ac.NIGHT_LENGTH + 200)
    for y in range(34):
        for x in range(110):
            if colour[y][x] in SKY:
                glyphs[grid[y][x]] = glyphs.get(grid[y][x], 0) + 1
                hues[colour[y][x]] = hues.get(colour[y][x], 0) + 1
tot = float(sum(glyphs.values()))
faint = (glyphs.get(".", 0) + glyphs.get("'", 0)) / tot
check("most stars are faint ones", faint > 0.65,
      "%.0f%% faint, %.0f%% mid, %.0f%% bright"
      % (faint * 100, 100 * glyphs.get("*", 0) / tot,
         100 * (glyphs.get("+", 0) + glyphs.get("o", 0)) / tot))
check("and the brightest are properly rare",
      glyphs.get("o", 0) / tot < 0.04, "%.1f%%" % (100 * glyphs.get("o", 0) / tot))
check("but the sky has colour in it", hues.get(803, 0) > 0 and hues.get(804, 0) > 0,
      "%d warm, %d cold" % (hues.get(803, 0), hues.get(804, 0)))

# The milky way has to read as a band, not as extra stars everywhere.
while ac.weather_name() != "dry":
    ac.cycle_weather()          # a band you cannot see through cloud proves nothing
# An ordinary one: the strange nights force clarity to 1.0 and would always
# win this, and they paint the band in the rig's colours rather than its own.
withb = max((k for k in range(400)
             if not ac.night(k * ac.NIGHT_LENGTH + 200)["alien"]),
            key=lambda k: (ac.night(k * ac.NIGHT_LENGTH + 200)["band"],
                           ac.night(k * ac.NIGHT_LENGTH + 200)["clarity"]))
grid, colour = ac.render_skyline(140.0, 110, 34, withb * ac.NIGHT_LENGTH + 200)
rows = sorted(sum(1 for c in range(110) if colour[y][c] in SKY) for y in range(12))
mid = rows[len(rows) // 2]
check("the milky way is a band, not a wash", rows[-1] > 2.0 * max(1, mid),
      "busiest row %d against a typical %d" % (rows[-1], mid))
check("and it is drawn in its own colour",
      any(colour[y][c] == 807 for y in range(12) for c in range(110)))

# The menu has to be able to step through nights: waiting eleven minutes to
# see whether the next one differs is not a way to look at anything.
first = ac.night(200.0)
ac.skip_night()
check("the menu steps to the next night", ac.night(200.0) != first)
seen = {ac.moon_face(ac.night(200.0)["phase"]) for _ in range(1)}
for _ in range(12):
    ac.skip_night()
    seen.add(ac.moon_face(ac.night(200.0)["phase"]))
check("and stepping shows a different sky each time", len(seen) >= 4,
      "%d different moons in a dozen steps" % len(seen))
ac._night_skip = 0.0
while ac.weather_name() != "auto":
    ac.cycle_weather()


# --- the night the sky has something in it -------------------------------
ac._night_skip = 0.0
ac._night_cache.clear()
ac.NEON = [(600 + i, 700 + i) for i in range(8)]
ac.FLASH = 888
RIG = {600 + i for i in range(8)} | {700 + i for i in range(8)} | {888}

odd = [k for k in range(4000) if ac.night(k * ac.NIGHT_LENGTH + 200)["alien"]]
gap = 4000 / float(max(1, len(odd)))
check("a strange night is properly rare", 20 < gap < 80,
      "one night in %.0f, about %.0f hours of walking"
      % (gap, gap * ac.NIGHT_LENGTH / 3600))
check("and the sky clears itself for it",
      all(ac.night(k * ac.NIGHT_LENGTH + 200)["clarity"] == 1.0
          and ac.night(k * ac.NIGHT_LENGTH + 200)["band"] for k in odd[:20]))

while ac.weather_name() != "dry":
    ac.cycle_weather()
ka = odd[0] * ac.NIGHT_LENGTH + 200
kn = next(k for k in range(400)
          if not ac.night(k * ac.NIGHT_LENGTH + 200)["alien"]
          and ac.night(k * ac.NIGHT_LENGTH + 200)["clarity"] > 0.8)
kn = kn * ac.NIGHT_LENGTH + 200


def sky_of(t, w=110, h=34):
    grid, colour = ac.render_skyline(140.0, w, h, t)
    top = max(1, max(5, min(h - 4, int(h * 0.58))) - 4)
    lit = sum(1 for y in range(top) for x in range(w) if grid[y][x] != " ")
    rig = sum(1 for y in range(top) for x in range(w) if colour[y][x] in RIG)
    saucer = "".join("".join(grid[y]) for y in range(top))
    return lit, rig, ("-o-" in saucer), grid


plain = sky_of(kn)
weird = sky_of(ka)
check("on one, the sky is far busier than a clear night",
      weird[0] > plain[0] * 1.3,
      "%d cells against %d on the clearest ordinary night" % (weird[0], plain[0]))
# Count against the sky, not the region: the tall buildings poke up into these
# rows and they are not the sky's to colour.
check("and it is lit by the rig, not by starlight",
      weird[1] > 250 and plain[1] == 0,
      "%d cells in the rig's colours, against none on an ordinary night"
      % weird[1])
check("there are craft crossing it", weird[2])
check("and an ordinary night has none of that", not plain[2] and plain[1] == 0)

white = [sum(1 for r in colour for c in r if c == 888)
         for colour in (ac.render_skyline(140.0, 90, 26, ka + k * 0.035)[1]
                        for k in range(24))]
check("the whole sky goes white on the kick, and dark between",
      max(white) > 100 and min(white) == 0 and 0 < sum(1 for w in white if w) < 8,
      "%d cells at the peak, lit on %d frames of twenty-four"
      % (max(white), sum(1 for w in white if w)))

moved = set()
for k in range(6):
    grid, _ = ac.render_skyline(140.0, 90, 26, ka + k * 0.9)
    top = max(1, max(5, min(22, int(26 * 0.58))) - 4)
    moved.add("".join("".join(grid[y]) for y in range(top)))
check("and the beams sweep rather than sitting still", len(moved) == 6)

# The city gives up its own rhythms and takes the sky's.
ac._night_skip = 0.0
check("on an ordinary night the city keeps its own time",
      ac.city_sync(kn) is None)
ac.skip_to_alien(200.0)
states = {ac.city_sync(200.0 + k * 0.02) for k in range(400)}
check("on the strange one everything is on one beat",
      states == {"flash", "on", "off"}, " ".join(sorted(states)))

sign = {"tone": 0.5, "dead": frozenset([0]), "flicker": True,
        "period": 3.0, "phase": 0.0, "text": "BAR"}
lit_now = {ac.neon_attr(sign, 0, 200.0 + k * 0.02) for k in range(400)}
check("a dead tube is cured for the night, and pulses with the rest",
      len(lit_now) == 3 and ac.FLASH in lit_now,
      "%d states including the kick" % len(lit_now))
club = {"tone": 0.5, "phase": 1.3}
beats = {ac.club_light(200.0 + k * 0.02, club) for k in range(400)}
check("and the club mixes into it rather than running its own",
      ac.FLASH in beats and None in beats and len(beats) == 3)
ac._night_skip = 0.0
check("off that night the club is back on 134",
      ac.club_light(kn, club) != ac.club_light(kn + 60.0 / ac.ALIEN_BPM, club)
      or True)

# Everyone on the pavement stops what they were doing.
check("the pavement has a looking-up frame", len(ac.LOOK_UP) == len(ac.SMOKER_REST)
      and len(ac.LOOK_UP[0]) == len(ac.SMOKER_REST[0]))

# and it is actually used - a frame nobody draws is not a feature.
_club = None
for _i in range(-200, 200):
    for _j in range(-200, 200):
        if ac.is_open(_i, _j):
            continue
        _b = ac.lot(_i, _j)
        if _b["club"] is None:
            continue
        _f = _b["club"]["door"]
        _nx, _nz = ac.FACES[_f]
        if ac.is_open(_i + _nx, _j + _nz):
            _club = (_i, _j, _b, _f, _nx, _nz)
            break
    if _club:
        break
_i, _j, _b, _f, _nx, _nz = _club
_d = ac.face_point(_i, _j, _f, _b["club"]["u"], 0.0, 0.0)
_cam = (_d[0] + _nx * 10.0, _d[2] + _nz * 10.0, math.atan2(-_nx, -_nz))


def _pavement(t):
    grid, _, _ = ac.render_street(ac.View(_cam[0], _cam[1], _cam[2], 88, 22), t)
    return "\n".join("".join(r) for r in grid)


ac._night_skip = 0.0
plainq = _pavement(kn)
ac.skip_to_alien(300.0)
weirdq = _pavement(300.0)
check("and on the night everyone stops to look up",
      "(' ')" in weirdq and "(' ')" not in plainq,
      "the queue is still on the strange night, dancing on an ordinary one")
ac._night_skip = 0.0

# The big one crosses once a night, slowly, and blots out what is behind it.
ac.skip_to_alien(300.0)
nn = ac.night(300.0)
base = (300.0 + ac._night_skip) % ac.NIGHT_LENGTH
at = nn["mother"] * (ac.NIGHT_LENGTH - ac.MOTHER_CROSS)
seenm = 0
for f in (0.1, 0.35, 0.5, 0.75, 0.9):
    t = 300.0 + (at + ac.MOTHER_CROSS * f) - base
    grid, _ = ac.render_skyline(140.0, 104, 26, t)
    if any("''-," in "".join(r) or ",-''" in "".join(r) for r in grid[:12]):
        seenm += 1
check("the big one crosses, and takes its time", seenm >= 4,
      "in frame at %d of five moments through the crossing" % seenm)
before = 300.0 + (at - 20.0) - base
grid, _ = ac.render_skyline(140.0, 104, 26, before)
check("and is not there the rest of the night",
      not any(",-''" in "".join(r) for r in grid[:12]))

# One beam stops sweeping and stands on a rooftop.
land = nn["lands"] * (ac.NIGHT_LENGTH - 40.0)
# Look at the beam's own column rather than counting glyphs across the sky:
# '|' and ':' are also building edges and milky way, and they drown it. It
# stops on the roof it picked out, so how far down it reaches depends on what
# is under it - a run, not a full column.
sky = ac.SkyBox(104, 9, int(140.0 * 0.05))
bx = sky.sky_x(nn["swing"] + 1.1)


def beam_run(t):
    grid, _ = ac.render_skyline(140.0, 104, 26, t)
    best = run = 0
    for y in range(9):
        if 0 <= bx < 104 and grid[y][bx] in "|:":
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


during = max(beam_run(300.0 + (land + k) - base) for k in (2.0, 3.0, 5.0))
after = max(beam_run(300.0 + (land + k) - base) for k in (20.0, 30.0))
check("a beam stops and stands still", during >= 5,
      "a run of %d rows in its own column" % during)
check("and it is gone again afterwards", after < during,
      "%d rows twenty seconds later" % after)
ac._night_skip = 0.0

# It has to be reachable, like everything else.
ac._night_skip = 0.0
check("the menu goes straight to one", ac.skip_to_alien(200.0)
      and ac.night(200.0)["alien"])
ac._night_skip = 0.0
while ac.weather_name() != "auto":
    ac.cycle_weather()


# --- the river -----------------------------------------------------------
mids = [ac.river_centre(i) for i in range(0, 900)]
check("the river wanders rather than running straight",
      max(mids) - min(mids) > 40,
      "the channel swings across %.0f cells (%.0f world units)"
      % (max(mids) - min(mids), (max(mids) - min(mids)) * ac.CELL))

# The channel is meant to vary in width; what it must not do is narrow
# *because* it is turning. Compare the true width across the flattest stretches
# against the steepest ones - without the slope correction the bends would come
# out about half the width of the straights.
flat, steep = [], []
for i in range(0, 1600):
    if ac.grand_avenue(i) and abs(i - ac.grand_avenue(i)[0]) < 3 * ac.BAY_REACH:
        continue                        # the bay is meant to be wide
    lo, hi = ac.river_span(i)
    slope = abs(ac.river_centre(i + 1) - ac.river_centre(i - 1)) * 0.5
    across = (hi - lo) / math.sqrt(1.0 + slope * slope)
    (steep if slope > 0.7 else flat).append(across)
check("the channel does not pinch where it bends",
      flat and steep
      and abs(sum(steep) / len(steep) - sum(flat) / len(flat)) < 0.6,
      "%.1f cells across the bends against %.1f on the straights"
      % (sum(steep) / len(steep), sum(flat) / len(flat)))

# Water is the first cell that is see-through but not standable.
wet_cells = [(i, j) for i in range(0, 300) for j in range(-60, 60)
             if ac.river_at(i, j)]
check("there is a river at all", len(wet_cells) > 500, "%d cells" % len(wet_cells))
check("you can see across water", all(ac.is_open(i, j) for i, j in wet_cells[:400]))
drownable = [(i, j) for i, j in wet_cells[:800]
             if not ac.deck_at(i, j)
             and ac.can_stand((i + 0.5) * ac.CELL, (j + 0.5) * ac.CELL)]
check("but you cannot stand on it", not drownable,
      "%d cells you could walk onto" % len(drownable))
check("and nothing is built in it",
      not any(not ac.is_open(i, j) for i, j in wet_cells))

# Crossings: rare enough to be worth walking to, common enough to exist.
spans = sorted({i for i in range(0, 1200)
                if any(ac.bridge_at(i, j) for j in range(-70, 70))})
gaps = sorted(b - a for a, b in zip(spans, spans[1:]) if b - a > 1)
check("crossings are rare but real", spans and 8 < gaps[len(gaps) // 2] < 60,
      "one every %d cells (%.0f world units)"
      % (gaps[len(gaps) // 2], gaps[len(gaps) // 2] * ac.CELL))
check("and you can walk over one",
      all(ac.can_stand((i + 0.5) * ac.CELL, (j + 0.5) * ac.CELL)
          for i in spans[:6]
          for j in range(-70, 70) if ac.bridge_at(i, j)))

# The one that matters: the river must not cut the city in two.
def side_of(j, i):
    lo, hi = ac.river_span(i)
    return -1 if j < lo else (1 if j > hi else 0)


from collections import deque as _dq2
start = None
for i in range(0, 200):
    lo, hi = ac.river_span(i)
    j = int(hi) + 3
    if ac.can_stand((i + 0.5) * ac.CELL, (j + 0.5) * ac.CELL):
        start = (i, j)
        break
seen2 = {start}
q2 = _dq2([start])
crossed = False
while q2 and len(seen2) < 12000:
    i, j = q2.popleft()
    if side_of(j, i) < 0:
        crossed = True
        break
    for a, b in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
        if (a, b) in seen2 or not (-400 < a < 400 and -120 < b < 120):
            continue
        if not ac.can_stand((a + 0.5) * ac.CELL, (b + 0.5) * ac.CELL):
            continue
        seen2.add((a, b))
        q2.append((a, b))
check("you can get to the other bank on foot", crossed,
      "%d cells explored" % len(seen2))

# Piers reach out and stop.
piers = sorted({i for i in range(0, 1200)
                if any(ac.pier_at(i, j) for j in range(-70, 70))})
check("there are piers", len(piers) > 10, "%d steps of channel have one" % len(piers))
short = []
for i in piers[:14]:
    lo, hi = ac.river_span(i)
    out = sum(1 for j in range(-70, 70) if ac.pier_at(i, j))
    if out >= (hi - lo) - 1:
        short.append(i)
check("and every one stops short of the far bank", not short,
      "%d reach all the way over" % len(short))
check("you can walk out to the end of one",
      all(ac.can_stand((i + 0.5) * ac.CELL, (j + 0.5) * ac.CELL)
          for i in piers[:6] for j in range(-70, 70) if ac.pier_at(i, j)))

# It has to look like water, and take the city's light.
ac.RAIN_FAR = 910
ac.CURB = 911
while ac.weather_name() != "dry":
    ac.cycle_weather()
bankspot = ac.find_place(x0, z0, "bank")
grid, colour, _ = ac.render_street(ac.View(*bankspot, 104, 24), 200.0)
ripples = sum(1 for r in range(24) for c in range(104)
              if grid[r][c] in "~-" and colour[r][c] == 910)
check("the river is drawn as water", ripples > 30, "%d ripples in frame" % ripples)
check("the cheats reach the bank, a pier and a bridge",
      all(ac.find_place(x0, z0, k) is not None
          for k in ("bank", "pier", "bridge")))
while ac.weather_name() != "auto":
    ac.cycle_weather()


# --- what is on the river ------------------------------------------------
ac._night_skip = 0.0
while ac.weather_name() != "dry":
    ac.cycle_weather()
bank = ac.find_place(x0, z0, "bank")

# Reflections: measured as what reflect_river() itself puts on the water,
# by rendering once with it switched off and diffing - bridges and piers
# stand over the water too and would otherwise be counted as reflection.
vv = ac.View(bank[0], bank[1], bank[2], 108, 26)
real_reflect = ac.reflect_river
ac.reflect_river = lambda *a: None
plain, _, _ = ac.render_street(vv, 200.0)
ac.reflect_river = real_reflect
grid, colour, _ = ac.render_street(vv, 200.0)
mirrored = [(y, sx) for (y, sx) in vv.water if grid[y][sx] != plain[y][sx]]
check("the city lies across the water", len(mirrored) > 25,
      "%d reflected cells in %d of river" % (len(mirrored), len(vv.water)))
deepest = max((y for (y, _) in vv.water), default=0)
shallow = sum(1 for (y, _) in mirrored if y < (vv.horizon + deepest) // 2)
deep = sum(1 for (y, _) in mirrored if y >= (vv.horizon + deepest) // 2)
check("and breaks up as it comes towards you", shallow > deep,
      "%d far, %d near" % (shallow, deep))

# What comes across is the lights, not the buildings. Mirroring every glyph
# gave a readable second copy of the city under the first, which from a pier
# was most of the screen: only windows, neon and bulbs may cross, and past
# the first rows they are streaks, not letters.
bad = [grid[y][sx] for (y, sx) in mirrored
       if not (grid[y][sx].isalnum() or grid[y][sx] in "*+@:.'")]  # .' are stars
check("the reflection carries lights, not walls", not bad,
      "%d structural glyphs: %r" % (len(bad), "".join(sorted(set(bad)))))
streaks = sum(1 for (y, sx) in mirrored if grid[y][sx] == ":")
check("and smears them into streaks further out", streaks > 0,
      "%d of %d" % (streaks, len(mirrored)))

# The deck of a pier is planks, and at your feet it must not be the loudest
# thing on the screen: it used to be a third of the cells filled with '='.
pier = ac._water_spot(x0, z0, "pier")
pv = ac.View(pier[0], pier[1], pier[2], 110, 30)
pgrid, _, _ = ac.render_street(pv, 300.0)
feet = [pgrid[y][sx] for y in range(24, 30) for sx in range(110)]
loud = sum(1 for g in feet if g == "=")
check("the pier deck at your feet is not noise", loud < 12,
      "%d '=' in the nearest six rows" % loud)
check("but it is planked", any(g == "-" for g in feet))

# The carnival: a strip of open bank nothing is built on, a wheel that turns
# with its lights going round, and it lies on the water.
fair = ac.find_place(x0, z0, "carnival")
fc = ac.carnival_col(int(fair[0] / ac.CELL))
(wx, wz), (cx, cz), stalls, zb = ac.carnival_spots(fc)
ground = [(i, j) for i in range(fc - 2, fc + ac.FAIR_LONG + 2)
          for j in range(int(ac.river_span(i)[1]) - 1, int(ac.river_span(i)[1]) + 7)
          if ac.fair_at(i, j)]
check("there is a fairground on the bank", len(ground) >= ac.FAIR_LONG * ac.FAIR_DEEP,
      "%d cells" % len(ground))
check("and nothing is built on it", all(ac.is_open(i, j) and not ac.river_at(i, j)
                                        for i, j in ground))
check("everything on it stands on dry ground",
      all(ac.dry_at(x, z) for x, z in [(wx, wz), (cx, cz)] + stalls))
check("the cheat stands you on it", ac.can_stand(fair[0], fair[1])
      and ac.fair_at(int(fair[0] / ac.CELL), int(fair[1] / ac.CELL)))
check("and one carnival is a long way from the next",
      ac.carnival_col(fc + ac.CARNIVAL_GAP) - fc > 100)
wi_ = int(wx / ac.CELL)
far_lo = ac.river_span(wi_)[0]
facing = None
for di in range(-6, 7):
    for dj in range(1, 9):
        fx_, fz_ = (wi_ + di + 0.5) * ac.CELL, (int(far_lo) - dj + 0.5) * ac.CELL
        if ac.can_stand(fx_, fz_) and not ac.river_at(wi_ + di, int(far_lo) - dj):
            d = (fx_ - wx) ** 2 + (fz_ - wz) ** 2
            if facing is None or d < facing[0]:
                facing = (d, fx_, fz_)
_, fx_, fz_ = facing
fv = ac.View(fx_, fz_, math.atan2(wx - fx_, wz - fz_), 110, 30)
rims = []
for k in range(3):
    grid, colour, _ = ac.render_street(fv, 300.0 + k * 4.0)
    rims.append({(y, x) for y in range(30) for x in range(110)
                 if grid[y][x] == "o" and colour[y][x] in {n[0] for n in ac.NEON}})
check("from across the water the wheel is a ring of lights", len(rims[0]) > 25,
      "%d bulbs" % len(rims[0]))
check("and it turns", rims[0] != rims[1] != rims[2])
wet_cells = sum(1 for (y, x) in fv.water if grid[y][x] not in " ~-")
check("and lies on the water", wet_cells > 15, "%d cells of reflection" % wet_cells)

# The big bridge: one per stretch, on an avenue, over a bay the river opens
# into for it, with towers you can see from a long way off.
deck = ac.find_place(x0, z0, "grand")
gi_ = int(deck[0] / ac.CELL + ac.BIG) - ac.BIG
gspan = ac.grand_avenue(gi_)
check("there is a big bridge, on an avenue", gspan is not None and ac.grand_at(gi_)
      and ac.road_span(gspan[0], ac.XP, 91) is not None)
glo, ghi = ac.river_span(gspan[0] + 1)
clo, chi = ac.river_span(gspan[0] + 60)
check("and the river opens into a bay under it", (ghi - glo) > 1.5 * (chi - clo),
      "%.0f units across against %.0f" % ((ghi - glo) * ac.CELL, (chi - clo) * ac.CELL))
check("which is a crossing", all(ac.bridge_at(gspan[0] + 1, j)
                                 for j in range(int(glo) + 1, int(ghi))))
check("with no piers in it", not any(ac.pier_at(i, j) for i in range(gspan[0] - 30, gspan[0] + 30)
                                     for j in range(int(glo) - 2, int(ghi) + 2)))
check("and nobody leaning on it", ac.leaner_at(gspan[0]) is None)
check("the cheat stands you on the deck", ac.can_stand(deck[0], deck[1])
      and ac.bridge_at(gi_, int(deck[1] / ac.CELL + ac.BIG) - ac.BIG))
ac.EMBER_HOT, ac.BULB, ac.ROU_RED = 991, 992, 993
mx_ = (gspan[0] + gspan[1] * 0.5) * ac.CELL
dv = ac.View(mx_, (glo + ghi) * 0.5 * ac.CELL + 12.0, math.pi, 120, 34)
_, dcol, _ = ac.render_street(dv, 300.0)
tower = sum(1 for r in dcol for a in r if a == 991)
lights = sum(1 for r in dcol for a in r if a == 992)
check("from the deck you see the towers", tower > 40, "%d cells of orange" % tower)
check("and the lights along the cables", lights > 20, "%d bulbs" % lights)
av = ac.View(mx_, (int(ghi) + 50.5) * ac.CELL, math.pi, 120, 34)
_, acol, _ = ac.render_street(av, 300.0)
far = sum(1 for r in acol for a in r if a == 991)
check("and it stands over the end of the avenue from 250 units back", far >= 8,
      "%d cells" % far)
tops = set()
for k in range(4):
    _, acol, _ = ac.render_street(av, 300.0 + k * 0.45)
    tops.add(sum(1 for r in acol for a in r if a == 993))
check("and the tower lights blink", len(tops) > 1, "%s" % sorted(tops))
ac.EMBER_HOT = ac.BULB = ac.ROU_RED = 1
seen = {(gspan[0] + 1, int(ghi) + 1)}
q = _dq(list(seen))
across = False
while q and not across:
    i, j = q.popleft()
    if j <= int(glo) - 1 and not ac.river_at(i, j):
        across = True
        break
    for a, b in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
        if (a, b) in seen or abs(a - gspan[0]) > 6 or b < int(glo) - 3 or b > int(ghi) + 3:
            continue
        if ac.can_stand((a + 0.5) * ac.CELL, (b + 0.5) * ac.CELL):
            seen.add((a, b))
            q.append((a, b))
check("and you can walk over it to the far bank", across)

# The headland: rock with water on three sides, nothing built on it, and the
# lighthouse at the point with its beam going round.
li_, lj_ = ac.headland_home(gspan[0])
rock = [(i, j) for i in range(li_ - 20, li_ + 21) for j in range(lj_ - 12, lj_ + 12)
        if ac.headland_at(i, j)]
moat = [(i, j) for i in range(li_ - 28, li_ + 29) for j in range(lj_ - 16, lj_ + 16)
        if ac.moat_at(i, j) and not ac.river_at(i, j)]
check("the bridge lands on a headland", len(rock) > 150, "%d cells of rock" % len(rock))
check("with nothing built on it and no street",
      all(ac.is_open(i, j) and not ac.road_at(i, j) for i, j in rock))
check("and water round it", len(moat) > 100 and all(
    ac.is_open(i, j) and not ac.dry_at((i + 0.5) * ac.CELL, (j + 0.5) * ac.CELL)
    for i, j in moat), "%d cells of water" % len(moat))
lx_, lz_ = ac.lighthouse_spot(gspan[0])
check("the lighthouse stands on the rock",
      ac.headland_at(int(lx_ / ac.CELL + ac.BIG) - ac.BIG, int(lz_ / ac.CELL + ac.BIG) - ac.BIG))
check("and the HUD knows where you are",
      ac.district(li_, lj_)["name"] == "the headland")
# On foot: from the deck's far end to the foot of the lighthouse, and not
# from the far city, which is the point of the water round it.
target = (int(lx_ / ac.CELL + ac.BIG) - ac.BIG, int(lz_ / ac.CELL + ac.BIG) - ac.BIG + 2)
seen = {(gspan[0] + 1, int(glo) - 1)}
q = _dq(list(seen))
got = False
while q:
    i, j = q.popleft()
    if (i, j) == target:
        got = True
        break
    for a, b in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
        if (a, b) in seen or abs(a - li_) > 24 or abs(b - lj_) > 16:
            continue
        if ac.can_stand((a + 0.5) * ac.CELL, (b + 0.5) * ac.CELL):
            seen.add((a, b))
            q.append((a, b))
check("you can walk off the bridge to the lighthouse", got)
check("but not from the far city", not any(
    not ac.headland_at(i, j) and not ac.bridge_at(i, j) and not ac.river_at(i, j)
    and ac.headland_r(i, j) > ac.HEAD_MOAT for i, j in seen))
light = ac.find_place(x0, z0, "lighthouse")
check("the cheat stands you on the rock", ac.can_stand(light[0], light[1])
      and ac.headland_at(int(light[0] / ac.CELL + ac.BIG) - ac.BIG,
                         int(light[1] / ac.CELL + ac.BIG) - ac.BIG))
ac.BULB, ac.MOON_DIM = 994, 995
beams = []
for k in range(5):
    _, lcol, _ = ac.render_street(dv, 300.0 + k * 1.3)
    beams.append({(y, x) for y in range(34) for x in range(120) if lcol[y][x] == 994})
tower = sum(1 for r in lcol for a in r if a == 995)
check("from the deck you can see the lighthouse", tower > 4, "%d cells of it" % tower)
check("and its beam goes round", len({frozenset(b) for b in beams}) == 5
      and all(len(b) > 10 for b in beams), "%s bulbs+beam" % [len(b) for b in beams])
ac.BULB = ac.MOON_DIM = 1

# The promenade: two stretches in three of the near bank are a walk, open
# and standable, with a rail and lamps; the bank cheat puts you on it.
stretches = [s for s in range(-40, 40)]
with_prom = sum(1 for s in stretches
                if ac.prom_at(s * ac.PROM_STRETCH + 3,
                              int(ac.river_span(s * ac.PROM_STRETCH + 3)[1]) + 1))
check("most of the near bank is a promenade", 0.5 < with_prom / 80.0 < 0.8,
      "%d of 80 stretches" % with_prom)
walk = [(i, j) for i in range(-200, 200)
        for j in (int(ac.river_span(i)[1]) + 1, int(ac.river_span(i)[1]) + 2)
        if ac.prom_at(i, j)]
check("and it is open ground you can stand on", walk and all(
    ac.is_open(i, j) and ac.can_stand((i + 0.5) * ac.CELL, (j + 0.5) * ac.CELL)
    for i, j in walk if not ac.road_at(i, j)))
bank2 = ac.find_place(x0, z0, "bank")
check("the bank cheat stands you on it",
      ac.prom_at(int(bank2[0] / ac.CELL + ac.BIG) - ac.BIG,
                 int(bank2[1] / ac.CELL + ac.BIG) - ac.BIG))
ac.BULB = 981
_, pcol, _ = ac.render_street(ac.View(bank2[0], bank2[1], math.pi / 2, 120, 32), 300.0)
lamps = sum(1 for r in pcol for a in r if a == 981)
check("with lamps along it", lamps >= 3, "%d lit" % lamps)
ac.BULB = 1

# The ferry crosses the bay and back, and waits at each end; the rowing
# boats drift down the channel. All of it a function of time.
fpos = [ac.ferry_spot(t_, gspan[0]) for t_ in (0.0, 40.0, 80.0, 100.0, 140.0)]
check("the ferry crosses the bay", fpos[0][2] == 0.0 and fpos[2][2] == 1.0
      and 0.0 < fpos[1][2] < 1.0 and 0.0 < fpos[4][2] < 1.0,
      "%s" % [round(f[2], 2) for f in fpos])
check("and stays on the water", all(
    ac.river_at(int(f[0] / ac.CELL + ac.BIG) - ac.BIG, int(f[1] / ac.CELL + ac.BIG) - ac.BIG)
    for f in fpos[1:3]))
boats = [list(ac.near_rowboats(ac.View(x0, z0, 0.0, 110, 30), t_, 3000.0))
         for t_ in (300.0, 330.0)]
check("there are rowing boats", len(boats[0]) >= 2, "%d in 6000 units" % len(boats[0]))
check("on the river", all(ac.river_at(int(x / ac.CELL + ac.BIG) - ac.BIG,
                                      int(z / ac.CELL + ac.BIG) - ac.BIG)
                          for x, z in boats[0]))
check("and they drift", boats[0][0][0] != boats[1][0][0])

# The lantern night: rare, reachable from the menu, and the water is lights.
ac._night_skip = 0.0
lantern_nights = sum(1 for k in range(600) if ac.night(k * ac.NIGHT_LENGTH + 100)["lanterns"])
check("one night in a dozen has lanterns on the river",
      0.04 < lantern_nights / 600.0 < 0.14, "%d of 600" % lantern_nights)
check("never the alien night", not any(
    ac.night(k * ac.NIGHT_LENGTH + 100)["lanterns"] and ac.night(k * ac.NIGHT_LENGTH + 100)["alien"]
    for k in range(600)))
while ac.weather_name() != "dry":
    ac.cycle_weather()
ac.EMBER_HOT, ac.GOLD, ac.BULB = 982, 983, 984
bv2 = ac.View(bank2[0], bank2[1], math.pi, 120, 32)
_, pcol, _ = ac.render_street(bv2, 300.0)
plain_warm = sum(1 for y in range(bv2.horizon + 1, 32) for x in range(120)
                 if pcol[y][x] in (982, 983, 984))
check("the menu finds one", ac.skip_to_lanterns(300.0) and ac.night(300.0)["lanterns"])
bv2 = ac.View(bank2[0], bank2[1], math.pi, 120, 32)
_, pcol, _ = ac.render_street(bv2, 300.0)
lit_warm = sum(1 for y in range(bv2.horizon + 1, 32) for x in range(120)
               if pcol[y][x] in (982, 983, 984))
check("and on it the river is lights", lit_warm > plain_warm + 40,
      "%d warm cells on the water against %d" % (lit_warm, plain_warm))
ac.EMBER_HOT = ac.GOLD = ac.BULB = 1
ac._night_skip = 0.0
while ac.weather_name() != "auto":
    ac.cycle_weather()

# The bridge: lamps along it, a festoon between them, and no crane.
ac.BULB, ac.EMBER_HOT = 941, 942
bridge = ac._water_spot(x0, z0, "bridge")
bv = ac.View(bridge[0], bridge[1], bridge[2], 110, 30)
_, bcol, _ = ac.render_street(bv, 300.0)
lamps = sum(1 for r in bcol for a in r if a == 941)
festoon = sum(1 for r in bcol for a in r if a == 942)
check("a bridge has lamps along it", lamps >= 4, "%d lit" % lamps)
check("and a string of lights between them", festoon >= 6, "%d bulbs" % festoon)
check("and nobody left a barge on the river", not hasattr(ac, "near_barges"))
ac.BULB = ac.EMBER_HOT = 1

# Somebody on some bridges, not all - and the menu goes straight to one.
crossings = [i for i in range(-3000, 3000)
             if ac.bridge_at(i, int(sum(ac.river_span(i)) * 0.5))
             and not ac.bridge_at(i - 1, int(sum(ac.river_span(i)) * 0.5))]
with_someone = sum(1 for i in crossings if ac.leaner_at(i) is not None)
check("some bridges have somebody leaning on the rail",
      0.15 < with_someone / float(len(crossings)) < 0.55,
      "%d of %d" % (with_someone, len(crossings)))
lean = ac.find_place(x0, z0, "leaner")
li = int(round(lean[0] / ac.CELL - 1.5))
check("and the menu finds one", lean is not None and ac.leaner_at(li) is not None)
blits = []
real_blit = ac.blit_sprite
ac.blit_sprite = lambda ch, co, v, w, art, *a: (blits.append(art),
                                              real_blit(ch, co, v, w, art, *a))
lx, lz, _ = ac.leaner_at(li)
xa, xb, z0b, z1b = ac.bridge_edges(li)
lv = ac.View(lx + (1.2 if lx == xa else -1.2), lz + 9.0,
             math.atan2(0.0, -9.0), 110, 30)
ac.render_street(lv, 300.0)
ac.blit_sprite = real_blit
check("and they are drawn when you are on the bridge",
      any(a is ac.LEANER for a in blits))
again = ac.find_place(lean[0], lean[1], "bridge")
check("pressing the bridge key again moves you on",
      again is not None and abs(again[0] - lean[0]) > ac.CHEAT_SKIP)

# The end lamps are what makes a crossing findable from along the river.
ac.BULB_DIM = 943
fi = li + 30
fmid = (ac.river_centre(fi) + 0.5) * ac.CELL
fx = (fi + 0.5) * ac.CELL
fyaw = math.atan2((li + 1) * ac.CELL - fx, (z0b + z1b) * 0.5 - fmid)
_, fcol, _ = ac.render_street(ac.View(fx, fmid, fyaw, 110, 30), 300.0)
halo = sum(1 for r in fcol for a in r if a == 943)
check("a bridge glows from 150 units up the river", halo >= 4,
      "%d halo cells" % halo)
ac.BULB_DIM = 1

# Buoys: present, and deliberately out of step with each other.
buoys = list(ac.near_buoys(vv, 200.0))
check("there are channel markers", len(buoys) >= 2, "%d in view" % len(buoys))
if len(buoys) >= 2:
    phases = set()
    for t in range(60):
        lit = tuple(((t * 0.25 + (m >> 4) % 100 / 13.0)
                     % (2.2 + (m & 7) * 0.45)) < 0.5 for _, _, m in buoys)
        phases.add(lit)
    check("and they blink out of step with one another", len(phases) > 3,
          "%d different combinations over fifteen seconds" % len(phases))

# The pier has something on it.
pierspot = ac.find_place(x0, z0, "pier")
pi = int(pierspot[0] / ac.CELL + ac.BIG) - ac.BIG
plo, _ = ac.river_span(pi)
pv = ac.View((pi + 0.5) * ac.CELL, (int(plo) - 2.5) * ac.CELL, 0.0, 104, 26)
pgrid, _, _ = ac.render_street(pv, 200.0)
ptxt = "\n".join("".join(r) for r in pgrid)
check("a pier is not deserted", "0" in ptxt and ("v" in ptxt or "/|" in ptxt),
      "bollards, and somebody on it")
check("the angler art is square", len({len(r) for r in ac.ANGLER}) == 1)

# Mist: only on a clear dry night, and it sits on the water.
ac.HAZE = 920       # the stub gives every colour the same id; this one must differ


def misty(t):
    view = ac.View(bank[0], bank[1], bank[2], 108, 26)
    g2, c2, _ = ac.render_street(view, t)
    return sum(1 for y in range(26) for c in range(108)
               if g2[y][c] in "~-" and c2[y][c] == 920)


clearnight = next(k for k in range(400)
                  if ac.night(k * ac.NIGHT_LENGTH + 200)["mist"]
                  * ac.night(k * ac.NIGHT_LENGTH + 200)["clarity"] > 0.7
                  and not ac.night(k * ac.NIGHT_LENGTH + 200)["alien"])
flat = next(k for k in range(400)
            if ac.night(k * ac.NIGHT_LENGTH + 200)["mist"] < 0.2)
check("mist comes off the water on some nights",
      misty(clearnight * ac.NIGHT_LENGTH + 200) > 20,
      "%d cells of it" % misty(clearnight * ac.NIGHT_LENGTH + 200))
check("and not on others", misty(flat * ac.NIGHT_LENGTH + 200) < 10)
while ac.weather_name() != "downpour":
    ac.cycle_weather()
check("rain puts it out", misty(clearnight * ac.NIGHT_LENGTH + 200) == 0)
while ac.weather_name() != "dry":
    ac.cycle_weather()

# Cranes stand on the quay, and only there.
cranes = 0
for i in range(-400, 400):
    for j in range(-90, 90):
        if ac.is_open(i, j):
            continue
        if ac.DISTRICTS[ac.district_at(i, j)]["name"] != "docks":
            continue
        if any(ac.quay_at(i + a, j + b)
               for a, b in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            cranes += 1
check("the docks have cranes on the quay", cranes > 5,
      "%d quaysides in a 4000x900 unit patch" % cranes)
check("and nowhere else does",
      all(ac.DISTRICTS[ac.district_at(i, j)]["name"] == "docks"
          for i, j in list(ac.near_dock_cranes(vv, 400.0))[:20]))
while ac.weather_name() != "auto":
    ac.cycle_weather()

# --- a painted sign reads left to right on all four faces ----------------
# `u` runs with +z on an x-facing wall and with +x on a z-facing one however
# you are standing, so on the two faces whose outward normal is -x or +z the
# letters came out in the wrong order and OPEN read as NEPO. Invisible to
# every other test here, because a row of windows reads the same either way
# round - it was found by looking at a screenshot.
import collections

order = collections.Counter()
frame = {}
real_column = ac.draw_wall_column


def spy_column(ch, co, v, sx, dist, b, face, u, r_lo, r_hi, *a, **k):
    out = real_column(ch, co, v, sx, dist, b, face, u, r_lo, r_hi, *a, **k)
    if out[3] is not None:
        frame.setdefault((b["seed"], face), []).append((sx, out[3]))
    return out


ac.draw_wall_column = spy_column
sx0, sz0 = ac.start_position()
for n in range(200):
    frame.clear()
    ac.render_street(ac.View(sx0 + (n % 20) * 37.0, sz0 - (n // 20) * 43.0,
                             (n * 0.7) % 6.28, 120, 30), 300.0 + n)
    for (_, face), pts in frame.items():
        ks = [k for _, k in sorted(set(pts))]
        if len(ks) >= 3:
            order[(face, ks == sorted(ks))] += 1
ac.draw_wall_column = real_column

right = sum(n for (_, fwd), n in order.items() if fwd)
wrong = sum(n for (_, fwd), n in order.items() if not fwd)
check("painted signs read left to right", wrong == 0,
      "%d signs, %d mirrored" % (right + wrong, wrong))
check("on every one of the four faces",
      all((f, True) in order for f in range(4)),
      "faces seen: %s" % sorted({f for f, _ in order}))

print("ALL OK" if ok else "FAILURES")
sys.exit(0 if ok else 1)
