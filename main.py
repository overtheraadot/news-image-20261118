#!/usr/bin/env python3
"""news-image-20261118: a newspaper front page summing up the world news of
Wednesday 18 November 2026. Pure Python 3.13 standard library only: the PNG
encoder is hand-rolled (struct + zlib) and every glyph is drawn from a
built-in 5x7 bitmap font. No network, no third-party imports, fully
deterministic: the same bytes on every run.

Run:  python3 main.py            (writes $MAKEFUN_OUTPUT_DIR/entry.png,
                                  or ./out/entry.png by default)
"""
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 230)
INK = (20, 20, 24)
NAVY = (20, 33, 61)
NAVY_DK = (13, 22, 42)
RED = (178, 34, 34)
GOLD = (233, 196, 106)
GOLD_BG = (238, 210, 140)
OCEAN = (198, 222, 240)
LAND = (127, 176, 105)
LAND_DK = (88, 138, 72)
GREY = (110, 110, 108)
LINE = (200, 192, 172)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows, each a 5-bit string. Uppercase only; input is upper-cased.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    ";": ("00000", "01100", "00000", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "<": ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    "^": ("00100", "01010", "10001", "00000", "00000", "00000", "00000"),
}
FALLBACK = FONT["?"]


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(px, x, y, text, scale, color):
    """Draw upper-cased text at (x, y); returns width drawn."""
    text = text.upper()
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FALLBACK)
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    fill_rect(px, cx + col * scale, y + row * scale,
                              scale, scale, color)
        cx += 6 * scale
    return cx - x - scale


def draw_text_centered(px, x0, x1, y, text, scale, color):
    w = text_width(text, scale)
    draw_text(px, x0 + (x1 - x0 - w) // 2, y, text, scale, color)


def wrap_text(text, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    words = text.upper().split(" ")
    lines, cur = [], ""
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
def new_canvas():
    px = bytearray(W * H * 3)
    r, g, b = PAPER
    for i in range(0, len(px), 3):
        px[i] = r
        px[i + 1] = g
        px[i + 2] = b
    return px


def set_pixel(px, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i], px[i + 1], px[i + 2] = color


def fill_rect(px, x, y, w, h, color):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    r, g, b = color
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            px[i] = r
            px[i + 1] = g
            px[i + 2] = b


def hline(px, x0, x1, y, color, thick=1):
    fill_rect(px, x0, y, x1 - x0, thick, color)


def vline(px, x, y0, y1, color, thick=1):
    fill_rect(px, x, y0, thick, y1 - y0, color)


def draw_line(px, x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_pixel(px, x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_circle(px, cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        fill_rect(px, cx - dx, cy + dy, 2 * dx + 1, 1, color)


def fill_polygon(px, points, color):
    """Scanline fill of a simple polygon given as [(x, y), ...]."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / (y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            x0 = int(round(xs[i]))
            x1 = int(round(xs[i + 1]))
            fill_rect(px, x0, y, x1 - x0 + 1, 1, color)


# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(px, path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- world map
# Stylised continents as (lon, lat) polygons, equirectangular projection.
MAP_X0, MAP_Y0, MAP_W, MAP_H = 16, 268, 992, 168
MAP_LAT_TOP, MAP_LAT_BOT = 75.0, -55.0


def project(lon, lat):
    x = MAP_X0 + (lon + 180.0) / 360.0 * MAP_W
    y = MAP_Y0 + (MAP_LAT_TOP - lat) / (MAP_LAT_TOP - MAP_LAT_BOT) * MAP_H
    return (int(round(x)), int(round(y)))


CONTINENTS = [
    # Asia (drawn first so Europe/Africa overlap cleanly on top)
    [(30, 36), (27, 41), (30, 46), (35, 48), (40, 48), (42, 52), (45, 55),
     (50, 58), (55, 60), (60, 65), (65, 68), (70, 72), (75, 73), (85, 75),
     (95, 76), (105, 77), (115, 73), (125, 72), (135, 72), (145, 72),
     (155, 70), (162, 66), (170, 66), (178, 65), (178, 62), (170, 60),
     (162, 58), (158, 53), (156, 51), (150, 59), (142, 52), (141, 45),
     (140, 40), (139, 36), (137, 34), (132, 33), (129, 31), (127, 35),
     (126, 38), (124, 40), (122, 39), (121, 32), (120, 28), (118, 25),
     (113, 22), (110, 20), (108, 18), (106, 10), (105, 9), (103, 7),
     (100, 6), (98, 10), (97, 16), (94, 17), (92, 21), (89, 22), (86, 20),
     (84, 18), (80, 15), (80, 10), (77, 8), (75, 12), (73, 18), (70, 20),
     (66, 25), (62, 25), (58, 26), (56, 27), (53, 28), (51, 29), (50, 30),
     (48, 30), (47, 30), (44, 29), (43, 33), (41, 36), (39, 36), (36, 36),
     (33, 36), (30, 36)],
    # Europe
    [(-9, 37), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-1, 50), (2, 51),
     (5, 53), (8, 55), (8, 57), (10, 59), (18, 56), (21, 55), (24, 58),
     (28, 60), (30, 62), (32, 70), (40, 68), (44, 66), (48, 60), (45, 55),
     (42, 50), (38, 47), (33, 45), (30, 46), (28, 44), (23, 40), (22, 38),
     (19, 42), (15, 44), (12, 44), (8, 44), (3, 43), (0, 39), (-2, 37),
     (-6, 36), (-9, 37)],
    # Africa
    [(-17, 15), (-16, 20), (-13, 27), (-10, 31), (-6, 34), (0, 36),
     (10, 37), (11, 34), (20, 32), (25, 32), (32, 31), (34, 28), (37, 22),
     (39, 18), (43, 12), (46, 11), (51, 11), (51, 2), (46, -2), (41, -4),
     (40, -10), (38, -15), (35, -20), (33, -26), (32, -29), (28, -33),
     (20, -35), (17, -32), (15, -27), (13, -18), (12, -12), (9, -1),
     (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 12), (-17, 15)],
    # North America
    [(-168, 66), (-150, 70), (-135, 69), (-125, 71), (-110, 68), (-95, 69),
     (-85, 66), (-80, 73), (-75, 72), (-65, 60), (-55, 52), (-60, 46),
     (-65, 44), (-70, 42), (-75, 35), (-76, 34), (-80, 26), (-81, 25),
     (-87, 21), (-90, 21), (-97, 16), (-94, 17), (-92, 15), (-97, 16),
     (-105, 20), (-110, 23), (-114, 29), (-117, 33), (-122, 37),
     (-124, 42), (-125, 49), (-130, 54), (-135, 58), (-145, 60),
     (-155, 58), (-162, 55), (-165, 60), (-168, 66)],
    # Greenland
    [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68), (-25, 70),
     (-30, 74), (-40, 76), (-55, 76), (-58, 70)],
    # South America
    [(-79, 9), (-77, 7), (-72, 12), (-64, 10), (-60, 8), (-52, 5),
     (-50, 0), (-44, -3), (-35, -8), (-38, -15), (-40, -22), (-48, -28),
     (-52, -33), (-58, -38), (-62, -41), (-65, -45), (-68, -52),
     (-70, -54), (-73, -50), (-73, -40), (-72, -30), (-70, -20),
     (-75, -15), (-80, -6), (-81, -1), (-80, 4), (-79, 9)],
    # Australia
    [(113, -22), (114, -28), (115, -33), (118, -35), (124, -33),
     (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (151, -24),
     (147, -19), (146, -19), (144, -15), (142, -11), (141, -13),
     (136, -12), (135, -15), (132, -12), (130, -13), (126, -14),
     (124, -16), (122, -17), (120, -20), (116, -21), (113, -22)],
    # United Kingdom
    [(-5, 50), (-3, 53), (-5, 56), (-2, 58), (0, 53), (-1, 51), (-5, 50)],
    # Japan
    [(130, 31), (132, 33), (134, 34), (136, 35), (138, 35), (140, 36),
     (141, 39), (141, 41), (143, 42), (144, 44), (142, 44), (140, 41),
     (139, 38), (137, 36), (134, 33), (131, 32), (130, 31)],
    # Indonesia / New Guinea chain
    [(95, 5), (98, 3), (100, 0), (104, -3), (108, -6), (112, -7),
     (116, -8), (120, -9), (124, -10), (128, -8), (130, -4), (132, -2),
     (134, 0), (131, 1), (127, 0), (122, -1), (118, 0), (114, -2),
     (110, -6), (105, -5), (100, -1), (96, 3), (95, 5)],
    # Philippines
    [(120, 18), (122, 16), (124, 14), (122, 11), (120, 10), (119, 13),
     (120, 18)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24), (45, -25),
     (43, -22), (43, -18), (44, -16)],
    # New Zealand
    [(167, -45), (170, -42), (173, -40), (175, -38), (177, -38),
     (175, -41), (172, -43), (169, -46), (167, -45)],
]

# (story number, lon, lat, label side) for the numbered map markers.
MARKERS = [
    (1, 112.0, 23.0, "R"), (2, 121.0, 12.0, "R"), (5, -75.7, 45.4, "L"),
    (6, 123.0, 26.0, "R"), (11, -0.1, 51.5, "L"), (12, 30.5, 50.4, "R"),
    (13, 50.5, 26.2, "R"), (14, 129.0, 41.0, "R"), (15, 34.5, 31.4, "R"),
    (18, 15.3, -4.3, "L"), (22, -84.0, 36.0, "L"), (32, 77.2, 28.6, "L"),
]

LEGEND = ("1 SHENZHEN  2 MANILA  5 OTTAWA  6 TAIPEI  11 LONDON  12 KYIV  "
          "13 BAHRAIN  14 PYONGYANG  15 GAZA  18 KINSHASA  22 WASHINGTON  "
          "32 NEW DELHI")

# ---------------------------------------------------------------- the news
# 34 stories, all events that happened or were first reported on Wednesday
# 18 November 2026, gathered from wire and press reports that day.
# (number, country tag, headline <= 26 chars, one-line summary)
STORIES = [
    # -- column 1: summits & diplomacy
    (1, "CHINA", "APEC OPENS IN SHENZHEN",
     "Leaders gather in Shenzhen as APEC opens; first Trump-Xi-Putin summit set for Thursday."),
    (2, "PHILIPPINES", "TRUMP LANDS IN MANILA",
     "Trump arrives for Quad talks, then heads to China for the APEC summit."),
    (3, "CHINA", "TRUMP-XI-PUTIN SUMMIT THU",
     "The first three-way summit of Trump, Xi and Putin will be held on 19 Nov in Shenzhen."),
    (4, "INDIA", "MODI PUSHES ASEAN TIES",
     "Modi urges deeper India-ASEAN cooperation for a peaceful Indo-Pacific."),
    (5, "CANADA", "CANADA-CHINA EXTEND DEALS",
     "Xi meets Carney as Canada and China extend trade cooperation ahead of APEC."),
    (6, "TAIWAN", "US CHALLENGES TAIWAN CURBS",
     "Washington urges ICAO to oppose Taiwan flight curbs; Beijing hits back."),
    (7, "THAILAND", "THAI-US TRADE DEAL SIGNED",
     "Bangkok and Washington sign a joint statement advancing a reciprocal trade deal."),
    (8, "JAPAN", "TOKYO PROPOSES ASIAN IEA",
     "Tokyo proposes an Asian energy agency and offers idle oil storage for a fee."),
    (9, "INDIA", "INDIA RE-ELECTED TO ITU",
     "India wins a seat on the ITU Council for the 2027-2030 term."),
    (10, "LATVIA", "KULBERGS GOVT WINS VOTE",
     "The Saeima approves the Kulbergs cabinet in a confidence vote."),
    (11, "BRITAIN", "BURNHAM FLOATS EU TIES",
     "PM Burnham sparks debate on closer EU ties; options due next month."),
    # -- column 2: war & security
    (12, "UKRAINE", "CRIMEA BRIDGE HIT AGAIN",
     "Ukraine strikes the bridge for a second day as Russia pounds Kyiv bridges."),
    (13, "BAHRAIN", "IRAN DRONES HIT US RADAR",
     "Iranian drones hit a US radar site; Kuwait says it intercepted drones."),
    (14, "N. KOREA", "PYONGYANG FIRES MISSILE",
     "Seoul says the North fired a ballistic missile toward the Sea of Japan."),
    (15, "GAZA", "CEASEFIRE 'NEAR COLLAPSE'",
     "The Board of Peace warns the Gaza ceasefire faces imminent collapse."),
    (16, "GAZA", "WFP: ONE MEAL EVERY 2 DAYS",
     "The WFP says displaced families in Gaza get one hot meal every two days."),
    (17, "UKRAINE", "372 CIVILIANS KILLED",
     "The UN says at least 372 civilians were killed in Ukraine in October."),
    (18, "D.R. CONGO", "EAST VIOLENCE GOES ON",
     "Rival peace efforts fail to halt the fighting in the east, reports say."),
    (19, "SUDAN", "SUDAN FACTORIES STRUGGLE",
     "Khartoum factories struggle to restart more than three years into the war."),
    (20, "ISRAEL", "KAHANA ELECTED SPEAKER",
     "The Knesset elects Matan Kahana, a Gadi Eisenkot ally, as its new speaker."),
    (21, "ISRAEL", "FLY DUBAI COCKPIT PROBE",
     "Netanyahu blames co-pilot radicalisation after a cockpit incident on a Dubai-Tel Aviv flight."),
    (22, "USA", "27 YEARS FOR TRUMP PLOT",
     "A Pakistani man gets 27 years in a US prison over a plot to kill Trump."),
    (23, "ECUADOR", "FISHERMEN SUE TRUMP ADMIN",
     "Ecuadorian fishermen sue the Trump administration over a drone strike."),
    # -- column 3: markets, tech & sport
    (24, "USA", "NVIDIA: $115.8BN, +103%",
     "Q3 revenue hits a record $115.8bn, up 103%; shares jump after hours."),
    (25, "USA", "NVIDIA PROBES HUANG LINK",
     "Nvidia hires a law firm to probe claims about Huang and a suspected Chinese spy."),
    (26, "USA", "DOW SINKS 849 POINTS",
     "The Dow falls 849 points as tech selling spreads ahead of Nvidia earnings."),
    (27, "GLOBAL", "FUNDS DUMP TECH, BUY GOLD",
     "A BofA survey finds the biggest tech-to-gold rotation since June 2006."),
    (28, "TECH", "GOOGLE FLAGS AI ATTACK",
     "Google warns of the first autonomous AI cyberattack and growing threats."),
    (29, "INDIA", "AMAZON BETS $7BN ON INDIA",
     "Amazon plans a $7bn renewable-energy investment in India by 2030."),
    (30, "GERMANY", "DEUTSCHE BANK SHARES SLIDE",
     "Shares fall about 6% after reports of a breach of customer data."),
    (31, "USA", "ANTHROPIC IPO SET FOR THU",
     "The AI firm's listing is expected on 19 Nov as AI shares rally."),
    (32, "INDIA", "CYCLONE AKVAN NEARS ANDHRA",
     "The storm strengthens in the Bay of Bengal; landfall expected on 20 Nov."),
    (33, "INDIA", "DHONI RETIRES FROM IPL",
     "The cricket great quits the IPL and becomes Chennai Super Kings mentor."),
    (34, "NORWAY", "HAALAND'S 96TH-MIN WINNER",
     "A 96th-minute penalty beats Denmark 3-2 and puts Norway in the quarters."),
]

COLUMNS = [
    ("1  SUMMITS & DIPLOMACY", STORIES[0:11]),
    ("2  WAR & SECURITY", STORIES[11:23]),
    ("3  MARKETS, TECH & SPORT", STORIES[23:34]),
]

# ---------------------------------------------------------------- layout
def draw_masthead(px):
    fill_rect(px, 0, 0, W, 88, NAVY)
    draw_text_centered(px, 0, W, 12, "THE WORLD IN ONE PAGE", 4, WHITE)
    draw_text_centered(px, 0, W, 58, "WEDNESDAY 18 NOVEMBER 2026", 2, GOLD)
    hline(px, 0, W, 88, GOLD, 3)


def draw_kicker(px):
    fill_rect(px, 0, 91, W, 25, GOLD_BG)
    draw_text_centered(px, 0, W, 97,
                       "34 STORIES FROM EVERY CONTINENT - ONE DAY", 2, NAVY)


def draw_hero(px):
    # Left hero: summits day. Right hero: war in Europe.
    for x0, x1 in ((16, 600), (616, 1008)):
        fill_rect(px, x0, 124, x1 - x0, 104, WHITE)
        for t in range(2):
            hline(px, x0, x1, 124 + t, NAVY)
            hline(px, x0, x1, 227 - t, NAVY)
            vline(px, x0 + t, 124, 228, NAVY)
            vline(px, x1 - 1 - t, 124, 228, NAVY)
    draw_text(px, 30, 134, "TOP STORY - SUMMITS DAY", 1, RED)
    draw_text(px, 30, 152, "APEC OPENS IN SHENZHEN", 3, NAVY)
    draw_text(px, 30, 176, "TRUMP LANDS IN MANILA", 3, NAVY)
    for i, line in enumerate(wrap_text(
            "Quad leaders meet in Manila. First-ever Trump-Xi-Putin summit "
            "set for Thursday in Shenzhen.", 90)):
        draw_text(px, 30, 204 + i * 9, line, 1, INK)
    draw_text(px, 630, 134, "WAR IN EUROPE", 1, RED)
    draw_text(px, 630, 152, "CRIMEA BRIDGE", 3, NAVY)
    draw_text(px, 630, 176, "HIT AGAIN", 3, NAVY)
    for i, line in enumerate(wrap_text(
            "Ukraine strikes the crossing for a second day as Russia pounds "
            "bridges in Kyiv.", 60)):
        draw_text(px, 630, 204 + i * 9, line, 1, INK)


def draw_map(px):
    draw_text_centered(px, 0, W, 240,
                       "WHERE IT HAPPENED - 12 PLACES THAT MADE THE NEWS",
                       2, NAVY)
    fill_rect(px, MAP_X0, MAP_Y0, MAP_W, MAP_H, OCEAN)
    # graticule
    for lon in range(-150, 181, 30):
        x, _ = project(lon, 0)
        vline(px, x, MAP_Y0, MAP_Y0 + MAP_H, (178, 208, 228))
    for lat in (60, 30, 0, -30):
        _, y = project(0, lat)
        hline(px, MAP_X0, MAP_X0 + MAP_W, y, (178, 208, 228))
    # continents
    for poly in CONTINENTS:
        fill_polygon(px, [project(lon, lat) for lon, lat in poly], LAND)
    # frame
    for t in range(2):
        hline(px, MAP_X0, MAP_X0 + MAP_W, MAP_Y0 + t, NAVY)
        hline(px, MAP_X0, MAP_X0 + MAP_W, MAP_Y0 + MAP_H - 1 - t, NAVY)
        vline(px, MAP_X0 + t, MAP_Y0, MAP_Y0 + MAP_H, NAVY)
        vline(px, MAP_X0 + MAP_W - 1 - t, MAP_Y0, MAP_Y0 + MAP_H, NAVY)
    # numbered markers
    for num, lon, lat, side in MARKERS:
        cx, cy = project(lon, lat)
        fill_circle(px, cx, cy, 9, RED)
        label = str(num)
        draw_text(px, cx - text_width(label, 1) // 2, cy - 3, label, 1, WHITE)
    draw_text_centered(px, 0, W, 442, LEGEND, 1, GREY)


def draw_columns(px):
    col_x = [16, 352, 688]
    col_w = 320
    y_head = 456
    for (title, stories), x0 in zip(COLUMNS, col_x):
        fill_rect(px, x0, y_head, col_w, 24, NAVY)
        draw_text_centered(px, x0, x0 + col_w, y_head + 5, title, 2, WHITE)
        y = y_head + 30
        for num, tag, headline, summary in stories:
            draw_text(px, x0 + 8, y, "%02d - %s" % (num, tag), 1, RED)
            draw_text(px, x0 + 8, y + 9, headline[:26], 2, INK)
            lines = wrap_text(summary, 52)[:2]
            for i, line in enumerate(lines):
                draw_text(px, x0 + 8, y + 24 + i * 8, line, 1, (70, 70, 66))
            y += 41
        if x0 != col_x[-1]:
            vline(px, x0 + col_w + 4, y_head, 994, LINE)
    # footer
    hline(px, 16, 1008, 996, NAVY, 2)
    draw_text_centered(
        px, 0, W, 1004,
        "ALL EVENTS OF WEDNESDAY 18 NOVEMBER 2026 - COMPILED FROM WIRE "
        "REPORTS - 34 STORIES", 1, NAVY)


def build_image():
    px = new_canvas()
    draw_masthead(px)
    draw_kicker(px)
    draw_hero(px)
    draw_map(px)
    draw_columns(px)
    return px


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    px = build_image()
    size = write_png(px, path)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))
    return 0


if __name__ == "__main__":
    sys.exit(main())
