"""Builds the SVGs used in the profile README (dark + light versions).

Run from the repo root:  python tools/build_assets.py
"""
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
MONO = "'SFMono-Regular', Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"

THEMES = {
    "dark": dict(
        bg1="#0b1220", bg2="#121a2b", panel="#161b22", panel2="#1c2330", border="#30363d",
        text="#e6edf3", muted="#8b949e", dot="#243044",
        teal="#2dd4bf", amber="#fbbf24", violet="#a78bfa", rose="#fb7185", green="#3fb950",
        arm="#d0d7de", arm2="#9aa5b1", armdark="#57606a", table="#30363d", glow="0.35",
    ),
    "light": dict(
        bg1="#f0fdfa", bg2="#f8fafc", panel="#f6f8fa", panel2="#ffffff", border="#d0d7de",
        text="#1f2328", muted="#59636e", dot="#d8e2ec",
        teal="#0d9488", amber="#d97706", violet="#7c3aed", rose="#e11d48", green="#1a7f37",
        arm="#475569", arm2="#64748b", armdark="#334155", table="#cbd5e1", glow="0.18",
    ),
}


def write(name, svg):
    (OUT / name).write_text(svg.strip() + "\n", encoding="utf-8")


def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- hero arm

SHOULDER = (600.0, 190.0)
L1, L2, TOOL = 100.0, 90.0, 22.0
BLOCK = 34.0
TABLE_Y = 260.0
SPOT_A, SPOT_B = 690.0, 775.0
A_PICK_Y = TABLE_Y - BLOCK              # top of block A resting on the table
A_STACK_Y = TABLE_Y - 2 * BLOCK         # top of block A sitting on block B


def ik(x, y):
    """Elbow-up IK for the wrist point, angles in degrees (SVG y-down)."""
    dx, dy = x - SHOULDER[0], y - SHOULDER[1]
    c2 = (dx * dx + dy * dy - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    c2 = max(-1.0, min(1.0, c2))
    best = None
    for s in (1, -1):
        q2 = s * math.acos(c2)
        q1 = math.atan2(dy, dx) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
        elbow_y = L1 * math.sin(q1)
        if best is None or elbow_y < best[2]:
            best = (q1, q2, elbow_y)
    return math.degrees(best[0]), math.degrees(best[1])


def ease(t):
    return t * t * (3 - 2 * t)


def arm_timeline():
    home = (720, 130)
    above_a, at_a = (SPOT_A, 168), (SPOT_A, A_PICK_Y)
    above_b, at_b = (SPOT_B, 164), (SPOT_B, A_STACK_Y)
    # (target, seconds, gripping-after-move)
    plan = [
        (home, 0.7, False), (above_a, 0.9, False), (at_a, 0.5, False), (at_a, 0.3, True),
        (above_a, 0.5, True), (above_b, 1.0, True), (at_b, 0.5, True), (at_b, 0.3, False),
        (above_b, 0.5, False), (home, 0.8, False), (home, 0.7, False),
        (above_b, 0.8, False), (at_b, 0.5, False), (at_b, 0.3, True), (above_b, 0.5, True),
        (above_a, 1.0, True), (at_a, 0.5, True), (at_a, 0.3, False), (above_a, 0.5, False),
        (home, 0.9, False),
    ]
    total = sum(p[1] for p in plan)
    frames = []
    pos, grip = home, False
    t0 = 0.0
    block = (SPOT_A, A_PICK_Y)
    steps_per_sec = 14
    for target, secs, grip_after in plan:
        n = max(2, int(secs * steps_per_sec))
        for i in range(n):
            u = ease(i / n)
            x = pos[0] + (target[0] - pos[0]) * u
            y = pos[1] + (target[1] - pos[1]) * u
            if grip:
                block = (x, y)
            frames.append(((t0 + secs * i / n) / total, x, y, block, grip))
        pos = target
        t0 += secs
        grip = grip_after
        if grip:
            block = pos
    x, y = pos
    frames.append((1.0, x, y, block, grip))
    return frames, total


def hero(theme):
    c = THEMES[theme]
    W, H = 840, 290
    frames, total = arm_timeline()
    kt = ";".join(fmt(f[0]) if f[0] < 1 else "1" for f in frames)
    a1s, a2s, a3s, blk, suck = [], [], [], [], []
    for _, x, y, b, g in frames:
        q1, q2 = ik(x, y - TOOL)
        a1s.append(fmt(q1))
        a2s.append(fmt(q2))
        a3s.append(fmt(-(q1 + q2)))
        blk.append(f"{fmt(b[0] - SPOT_A)} {fmt(b[1] - A_PICK_Y)}")
        suck.append("1" if g else "0")
    dur = f"{fmt(total)}s"

    def anim_rot(vals):
        return (f'<animateTransform attributeName="transform" type="rotate" dur="{dur}" '
                f'repeatCount="indefinite" calcMode="linear" keyTimes="{kt}" values="{";".join(vals)}"/>')

    # typing lines
    lines = [
        "Robotics & AI/ML Engineer",
        "Voice-controlled robot arms",
        "RL fine-tuned robot policies",
        "Local-first AI & RAG tools",
        "Java & Spring Boot backends",
    ]
    fs = 25
    cw = fs * 0.6
    per_char, hold, slot = 0.065, 1.6, 0.0
    slots = []
    for s in lines:
        type_t = len(s) * per_char
        del_t = len(s) * 0.025
        slots.append((s, type_t, hold, del_t))
    loop = sum(t + h + d + 0.3 for _, t, h, d in slots)
    tx, ty = 58, 236
    typed = []
    start = 0.0
    for idx, (s, type_t, h, del_t) in enumerate(slots):
        n = len(s)
        times, widths = [0.0], [0]
        for k in range(1, n + 1):
            times.append(start + k * per_char)
            widths.append(k)
        times.append(start + type_t + h)
        widths.append(n)
        for k in range(n - 1, -1, -1):
            times.append(start + type_t + h + (n - k) * 0.025)
            widths.append(k)
        times[0] = 0.0
        # before this line starts it is hidden (width 0); keep width 0 until end
        key = [0.0]
        val = [0]
        if start > 0:
            key.append(start / loop)
            val.append(0)
        for tm, wv in zip(times[1:], widths[1:]):
            key.append(min(tm / loop, 1.0))
            val.append(wv)
        if key[-1] < 1.0:
            key.append(1.0)
            val.append(0)
        # make keyTimes strictly non-decreasing and unique
        clean_k, clean_v = [], []
        for k_, v_ in zip(key, val):
            if clean_k and k_ <= clean_k[-1]:
                k_ = clean_k[-1] + 1e-5
            clean_k.append(min(k_, 1.0))
            clean_v.append(v_)
        clean_k[-1] = 1.0
        kts = ";".join(f"{k:.5f}" for k in clean_k)
        wvals = ";".join(fmt(v * cw + (2 if v else 0)) for v in clean_v)
        cvals = ";".join(fmt(tx + 26 + v * cw + 2) for v in clean_v)
        end = start + type_t + h + del_t
        vis = ";".join("1" if start <= clean_k[i] * loop < end - 1e-6 else "0" for i in range(len(clean_v)))
        typed.append(f'''
    <clipPath id="tc{idx}"><rect x="{tx + 26}" y="{ty - 26}" height="36" width="0">
      <animate attributeName="width" dur="{fmt(loop)}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kts}" values="{wvals}"/>
    </rect></clipPath>
    <text clip-path="url(#tc{idx})" x="{tx + 26}" y="{ty}" font-family="{MONO}" font-size="{fs}" fill="{c['text']}" textLength="{fmt(len(s) * cw)}" lengthAdjust="spacing">{esc(s)}</text>
    <rect x="{tx + 28}" y="{ty - 21}" width="3" height="26" rx="1" fill="{c['teal']}" opacity="0">
      <animate attributeName="x" dur="{fmt(loop)}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kts}" values="{cvals}"/>
      <animate attributeName="opacity" dur="{fmt(loop)}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kts}" values="{vis}"/>
    </rect>''')
        start += type_t + h + del_t + 0.3

    sx, sy = SHOULDER
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Amatya Katyayan - Robotics and AI/ML Engineer">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c['bg1']}"/><stop offset="1" stop-color="{c['bg2']}"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.78" cy="0.55" r="0.45">
      <stop offset="0" stop-color="{c['teal']}" stop-opacity="{c['glow']}"/><stop offset="1" stop-color="{c['teal']}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1.4" fill="{c['dot']}"/>
    </pattern>
    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c['text']}"/><stop offset="1" stop-color="{c['teal']}"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="22" fill="url(#bg)" stroke="{c['border']}"/>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="22" fill="url(#dots)" opacity="0.7"/>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="22" fill="url(#glow)"/>

  <g>
    <rect x="58" y="44" width="346" height="36" rx="18" fill="{c['panel2']}" stroke="{c['border']}"/>
    <circle cx="80" cy="62" r="5" fill="{c['green']}"/>
    <circle cx="80" cy="62" r="5" fill="none" stroke="{c['green']}" stroke-width="2">
      <animate attributeName="r" values="5;12" dur="1.8s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.8;0" dur="1.8s" repeatCount="indefinite"/>
    </circle>
    <text x="96" y="68" font-family="{SANS}" font-size="16" font-weight="600" fill="{c['text']}">Open to Robotics, AI/ML &amp; SWE roles</text>
  </g>
  <text x="58" y="122" font-family="{SANS}" font-size="22" fill="{c['muted']}">Hi there, I'm</text>
  <text x="55" y="180" font-family="{SANS}" font-size="56" font-weight="800" fill="url(#name)">Amatya Katyayan</text>
  <text x="{tx}" y="{ty}" font-family="{MONO}" font-size="{fs}" font-weight="700" fill="{c['teal']}">&gt;</text>
  {''.join(typed)}

  <!-- workspace -->
  <rect x="548" y="{TABLE_Y}" width="262" height="6" rx="3" fill="{c['table']}"/>
  <rect x="{SPOT_B - BLOCK / 2}" y="{TABLE_Y - BLOCK}" width="{BLOCK}" height="{BLOCK}" rx="6" fill="{c['amber']}"/>
  <rect x="{SPOT_B - BLOCK / 2 + 7}" y="{TABLE_Y - BLOCK + 7}" width="{BLOCK - 14}" height="5" rx="2.5" fill="#ffffff" opacity="0.35"/>
  <g>
    {f'<animateTransform attributeName="transform" type="translate" dur="{dur}" repeatCount="indefinite" calcMode="linear" keyTimes="{kt}" values="{";".join(blk)}"/>'}
    <rect x="{SPOT_A - BLOCK / 2}" y="{A_PICK_Y}" width="{BLOCK}" height="{BLOCK}" rx="6" fill="{c['teal']}"/>
    <rect x="{SPOT_A - BLOCK / 2 + 7}" y="{A_PICK_Y + 7}" width="{BLOCK - 14}" height="5" rx="2.5" fill="#ffffff" opacity="0.35"/>
  </g>

  <!-- arm -->
  <path d="M{sx - 34} {TABLE_Y} L{sx - 22} {sy + 30} L{sx + 22} {sy + 30} L{sx + 34} {TABLE_Y} Z" fill="{c['armdark']}"/>
  <rect x="{sx - 28}" y="{sy + 14}" width="56" height="18" rx="6" fill="{c['arm2']}"/>
  <g transform="translate({sx} {sy})">
    <g>
      {anim_rot(a1s)}
      <rect x="-12" y="-11" width="{L1 + 24}" height="22" rx="11" fill="{c['arm']}"/>
      <circle r="15" fill="{c['armdark']}"/><circle r="6" fill="{c['teal']}"/>
      <g transform="translate({L1} 0)">
        <g>
          {anim_rot(a2s)}
          <rect x="-10" y="-9" width="{L2 + 20}" height="18" rx="9" fill="{c['arm']}"/>
          <circle r="12" fill="{c['armdark']}"/><circle r="5" fill="{c['amber']}"/>
          <g transform="translate({L2} 0)">
            <g>
              {anim_rot(a3s)}
              <circle r="9" fill="{c['armdark']}"/>
              <rect x="-4" y="0" width="8" height="{TOOL - 6}" fill="{c['arm2']}"/>
              <path d="M-10 {TOOL - 6} L10 {TOOL - 6} L7 {TOOL} L-7 {TOOL} Z" fill="{c['armdark']}"/>
              <ellipse cx="0" cy="{TOOL}" rx="9" ry="3" fill="{c['teal']}" opacity="0">
                <animate attributeName="opacity" dur="{dur}" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{";".join(suck)}"/>
              </ellipse>
            </g>
          </g>
        </g>
      </g>
    </g>
  </g>
</svg>'''


# ---------------------------------------------------------------- terminal

def terminal(theme):
    c = THEMES[theme]
    W, H = 400, 300
    rows = [
        ("cmd", "whoami"),
        ("out", "Amatya Katyayan, Tempe AZ"),
        ("cmd", "cat focus.txt"),
        ("out", "robot learning | vision | GenAI"),
        ("cmd", "cat now.txt"),
        ("out", "M.S. Robotics & AI @ ASU (May 2027)"),
        ("out", "AI + RAG tools @ W. P. Carey, ASU"),
        ("cmd", "cat before.txt"),
        ("out", "Software Engineer @ Persistent"),
        ("out", "Java | Spring Boot | React | REST"),
    ]
    fs, lh, x0, y0 = 13.5, 21, 22, 70
    cw = fs * 0.6
    parts = []
    t = 0.4
    for i, (kind, s) in enumerate(rows):
        y = y0 + i * lh
        if kind == "cmd":
            n = len(s)
            dur_t = n * 0.06
            w_end = (n + 2) * cw + 2
            parts.append(f'''
  <text x="{x0}" y="{y}" font-family="{MONO}" font-size="{fs}" fill="{c['teal']}" opacity="0">$<set attributeName="opacity" to="1" begin="{fmt(t)}s" fill="freeze"/></text>
  <clipPath id="c{i}"><rect x="{x0 + 2 * cw}" y="{y - 14}" height="20" width="0"><animate attributeName="width" from="0" to="{fmt(w_end)}" begin="{fmt(t + 0.2)}s" dur="{fmt(dur_t)}s" fill="freeze" calcMode="discrete" values="{';'.join(fmt(k * cw) for k in range(n + 1))};{fmt(w_end)}"/></rect></clipPath>
  <text clip-path="url(#c{i})" x="{x0 + 2 * cw}" y="{y}" font-family="{MONO}" font-size="{fs}" fill="{c['text']}" textLength="{fmt(n * cw)}" lengthAdjust="spacing">{esc(s)}</text>''')
            t += 0.2 + dur_t + 0.25
        else:
            parts.append(f'''
  <text x="{x0}" y="{y}" font-family="{MONO}" font-size="{fs}" fill="{c['muted']}" opacity="0">{esc(s)}<animate attributeName="opacity" from="0" to="1" begin="{fmt(t)}s" dur="0.25s" fill="freeze"/></text>''')
            t += 0.18
    yc = y0 + len(rows) * lh
    parts.append(f'''
  <text x="{x0}" y="{yc}" font-family="{MONO}" font-size="{fs}" fill="{c['teal']}" opacity="0">$<set attributeName="opacity" to="1" begin="{fmt(t)}s" fill="freeze"/></text>
  <rect x="{x0 + 2 * cw}" y="{yc - 12}" width="8" height="15" fill="{c['teal']}" opacity="0">
    <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" begin="{fmt(t)}s" repeatCount="indefinite"/>
  </rect>''')
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="About me: robotics and AI grad student at ASU, former software engineer at Persistent Systems">
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="{c['panel']}" stroke="{c['border']}"/>
  <path d="M1 17 a16 16 0 0 1 16 -16 H{W - 17} a16 16 0 0 1 16 16 V38 H1 Z" fill="{c['panel2']}"/>
  <line x1="1" y1="38" x2="{W - 1}" y2="38" stroke="{c['border']}"/>
  <circle cx="22" cy="20" r="6" fill="#ff5f57"/><circle cx="42" cy="20" r="6" fill="#febc2e"/><circle cx="62" cy="20" r="6" fill="#28c840"/>
  <text x="{W / 2}" y="25" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{c['muted']}">amatya@asu: ~</text>
  {''.join(parts)}
</svg>'''


# ---------------------------------------------------------------- stats

def stats(theme):
    c = THEMES[theme]
    W, H = 400, 300
    tiles = [
        ("4.00", "GPA, M.S. Robotics", "Arizona State University", c["teal"]),
        ("3.5 yrs", "paid experience", "software, ML, teaching", c["amber"]),
        ("#1", "rank in B.E. cohort", "Computer Engineering", c["violet"]),
        ("IEEE", "first-author paper", "AI + IoT agriculture", c["rose"]),
    ]
    parts = []
    gw, gh, gap = 186, 136, 12
    for i, (big, l1, l2, col) in enumerate(tiles):
        x = 8 + (i % 2) * (gw + gap)
        y = 8 + (i // 2) * (gh + gap)
        b = 0.15 + i * 0.18
        parts.append(f'''
  <g opacity="0">
    <animate attributeName="opacity" from="0" to="1" begin="{fmt(b)}s" dur="0.5s" fill="freeze"/>
    <animateTransform attributeName="transform" type="translate" from="0 14" to="0 0" begin="{fmt(b)}s" dur="0.5s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/>
    <rect x="{x}" y="{y}" width="{gw}" height="{gh}" rx="14" fill="{c['panel']}" stroke="{c['border']}"/>
    <rect x="{x + 18}" y="{y + 20}" width="28" height="4" rx="2" fill="{col}">
      <animate attributeName="width" values="28;56;28" dur="3s" begin="{fmt(b + 0.6)}s" repeatCount="indefinite"/>
    </rect>
    <text x="{x + 18}" y="{y + 70}" font-family="{SANS}" font-size="34" font-weight="800" fill="{col}">{esc(big)}</text>
    <text x="{x + 18}" y="{y + 97}" font-family="{SANS}" font-size="14.5" font-weight="600" fill="{c['text']}">{esc(l1)}</text>
    <text x="{x + 18}" y="{y + 117}" font-family="{SANS}" font-size="12.5" fill="{c['muted']}">{esc(l2)}</text>
  </g>''')
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="4.00 GPA at ASU, 3.5 years of paid experience, ranked first in B.E. cohort, first-author IEEE paper">
  {''.join(parts)}
</svg>'''


# ---------------------------------------------------------------- project cards

def icon(kind, col, c):
    if kind == "arm":
        return f'''<g fill="none" stroke="{col}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4 30 h20"/><path d="M14 30 v-6"/>
      <g><animateTransform attributeName="transform" type="rotate" values="-8 14 24;10 14 24;-8 14 24" dur="3s" repeatCount="indefinite"/>
        <path d="M14 24 L22 10 L32 16"/><circle cx="22" cy="10" r="2.2" fill="{col}"/><path d="M32 16 v5"/></g></g>'''
    if kind == "wave":
        bars = []
        for i, h in enumerate([8, 16, 24, 14, 20, 10, 6]):
            x = 4 + i * 4.6
            bars.append(f'<rect x="{fmt(x)}" y="{18 - h / 2}" width="2.6" height="{h}" rx="1.3" fill="{col}">'
                        f'<animate attributeName="height" values="{h};{max(4, 26 - h)};{h}" dur="1.{i + 1}s" repeatCount="indefinite"/>'
                        f'<animate attributeName="y" values="{18 - h / 2};{18 - max(4, 26 - h) / 2};{18 - h / 2}" dur="1.{i + 1}s" repeatCount="indefinite"/></rect>')
        return "<g>" + "".join(bars) + "</g>"
    if kind == "radar":
        return f'''<g fill="none" stroke="{col}" stroke-width="2"><circle cx="18" cy="18" r="14" opacity="0.5"/><circle cx="18" cy="18" r="7" opacity="0.5"/>
      <g><animateTransform attributeName="transform" type="rotate" from="0 18 18" to="360 18 18" dur="3s" repeatCount="indefinite"/><path d="M18 18 L18 4" stroke-width="2.4" stroke-linecap="round"/></g>
      <circle cx="25" cy="12" r="2.4" fill="{col}" stroke="none"><animate attributeName="opacity" values="0;1;0" dur="3s" repeatCount="indefinite"/></circle></g>'''
    if kind == "spark":
        return f'''<g fill="{col}"><path d="M18 3 L21 14 L32 18 L21 22 L18 33 L15 22 L4 18 L15 14 Z">
      <animateTransform attributeName="transform" type="rotate" values="0 18 18;90 18 18" dur="4s" repeatCount="indefinite"/></path></g>'''
    if kind == "chart":
        return f'''<g fill="{col}">''' + "".join(
            f'<rect x="{4 + i * 7.5}" y="{32 - h}" width="5" height="{h}" rx="1.5"><animate attributeName="height" values="{h};{h * 0.5};{h}" dur="2.{i}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{32 - h};{32 - h * 0.5};{32 - h}" dur="2.{i}s" repeatCount="indefinite"/></rect>'
            for i, h in enumerate([12, 20, 15, 26])) + "</g>"
    if kind == "paper":
        return f'''<g fill="none" stroke="{col}" stroke-width="2.2" stroke-linejoin="round"><path d="M8 4 h14 l7 7 v21 h-21 Z"/><path d="M22 4 v7 h7"/>
      <path d="M12 18 h12 M12 23 h12 M12 28 h7" stroke-linecap="round"><animate attributeName="stroke-dasharray" values="0 40;40 0" dur="2.5s" repeatCount="indefinite"/></path></g>'''
    return ""


def card(theme, p):
    c = THEMES[theme]
    col = c[p["color"]]
    W, H = 400, 236
    tags = []
    tx = 22
    for t in p["tags"]:
        w = len(t) * 6.9 + 18
        tags.append(f'<rect x="{fmt(tx)}" y="190" width="{fmt(w)}" height="24" rx="12" fill="{c["panel2"]}" stroke="{c["border"]}"/>'
                    f'<text x="{fmt(tx + w / 2)}" y="206" text-anchor="middle" font-family="{SANS}" font-size="12" fill="{c["muted"]}">{esc(t)}</text>')
        tx += w + 7
    m = p["metric"]
    bar = ""
    if "from" in m:
        bar = f'''
  <rect x="22" y="150" width="356" height="8" rx="4" fill="{c['panel2']}" stroke="{c['border']}" stroke-width="0.8"/>
  <rect x="22" y="150" width="{fmt(356 * m['from'])}" height="8" rx="4" fill="{c['muted']}" opacity="0.55"/>
  <rect x="22" y="150" width="{fmt(356 * m['from'])}" height="8" rx="4" fill="{col}">
    <animate attributeName="width" values="{fmt(356 * m['from'])};{fmt(356 * m['to'])};{fmt(356 * m['to'])};{fmt(356 * m['from'])}" keyTimes="0;0.35;0.85;1" dur="4s" repeatCount="indefinite" calcMode="spline" keySplines="0.3 0 0.2 1;0 0 1 1;0.4 0 0.2 1"/>
  </rect>'''
    desc = "".join(f'<text x="22" y="{98 + i * 19}" font-family="{SANS}" font-size="13.5" fill="{c["muted"]}">{esc(d)}</text>'
                   for i, d in enumerate(p["desc"]))
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(p['title'])}: {esc(' '.join(p['desc']))}">
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="{c['panel']}" stroke="{c['border']}"/>
  <rect x="1" y="1" width="{W - 2}" height="4" rx="2" fill="{col}" opacity="0.9"/>
  <g transform="translate(20 18)">{icon(p['icon'], col, c)}</g>
  <text x="66" y="32" font-family="{SANS}" font-size="11.5" font-weight="700" letter-spacing="1.2" fill="{col}">{esc(p['kicker'].upper())}</text>
  <text x="66" y="54" font-family="{SANS}" font-size="19" font-weight="700" fill="{c['text']}">{esc(p['title'])}</text>
  <text x="{W - 22}" y="32" text-anchor="end" font-family="{SANS}" font-size="13" fill="{c['muted']}">{esc(p.get('cta', 'View repo'))} -&gt;</text>
  {desc}
  <text x="22" y="141" font-family="{SANS}" font-size="14" font-weight="700" fill="{col}">{esc(m['label'])}</text>
  {bar}
  {''.join(tags)}
</svg>'''


PROJECTS = [
    dict(slug="dppo", icon="arm", color="teal", kicker="Robot learning", title="Robust DPPO on Robomimic",
         desc=["Fine-tuned a diffusion policy with PPO, then", "stress-tested it under 10 perturbations."],
         metric=dict(label="Task success 40% -> 81% after DPPO", **{"from": 0.40, "to": 0.81}),
         tags=["Diffusion Policy", "PPO", "PyTorch", "Robomimic"]),
    dict(slug="voice-arm", icon="wave", color="violet", kicker="Robotics + LLMs", title="Voice-Controlled Robot Arm",
         desc=["Spoken commands -> Gemini -> OpenCV block", "detection -> pick, stack and place on a Dobot."],
         metric=dict(label="\"Place the farthest blue block on the red one\""),
         tags=["Python", "Gemini", "OpenCV", "Dobot"]),
    dict(slug="ekf", icon="radar", color="amber", kicker="State estimation", title="EKF Sensor Fusion",
         desc=["Fused wheel odometry, gyro, GPS and LiDAR", "with outlier gating for a ground robot."],
         metric=dict(label="Position error 30.24 m -> 0.30 m (100x less)", **{"from": 0.06, "to": 0.94}),
         tags=["Python", "NumPy", "EKF", "Monte Carlo"]),
    dict(slug="brandpilot", icon="spark", color="rose", kicker="GenAI in production", title="BrandPilot",
         desc=["Researches a company from the web (RAG) and", "drafts outreach with a LoRA-tuned Gemma 3."],
         metric=dict(label="Research per company: 45 min -> under 10", **{"from": 0.22, "to": 0.90}),
         tags=["LoRA", "RAG", "FastAPI", "Docker", "K8s"]),
    dict(slug="delivery", icon="chart", color="teal", kicker="Data science", title="Delivery Performance Analytics",
         desc=["ETL, SQL KPIs and a late-delivery model on", "96k real e-commerce orders."],
         metric=dict(label="Top-10% risk flags: 2.8x more likely late", **{"from": 0.3, "to": 0.84}),
         tags=["SQL", "scikit-learn", "Tableau", "Plotly"]),
    dict(slug="ieee", icon="paper", color="violet", kicker="Research", title="IEEE Paper, First Author",
         desc=["AI + IoT smart agriculture system for", "personalized advisories (ICAC3N 2021)."],
         metric=dict(label="Prototyping grant, Goa State Innovation Council"),
         tags=["IoT", "Machine Learning", "IEEE"], cta="Scholar"),
]


# ---------------------------------------------------------------- buttons

def button(theme, label, kind):
    c = THEMES[theme]
    W, H = 190, 50
    col = c["teal"]
    icons = {
        "globe": f'<circle cx="0" cy="0" r="9"/><path d="M-9 0 h18 M0 -9 c-5 5 -5 13 0 18 M0 -9 c5 5 5 13 0 18"/>',
        "brief": f'<rect x="-9" y="-5" width="18" height="13" rx="2"/><path d="M-4 -5 v-3 h8 v3 M-9 1 h18"/>',
        "cap": f'<path d="M-11 -2 L0 -8 L11 -2 L0 4 Z"/><path d="M-6 1 v5 c4 3 8 3 12 0 v-5"/>',
    }
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(label)}">
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="25" fill="{c['panel']}" stroke="{c['border']}"/>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="25" fill="none" stroke="{col}" stroke-width="1.5" stroke-dasharray="70 600" opacity="0.9">
    <animate attributeName="stroke-dashoffset" from="0" to="-670" dur="5s" repeatCount="indefinite"/>
  </rect>
  <g transform="translate(34 25)" fill="none" stroke="{col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{icons[kind]}</g>
  <text x="56" y="31" font-family="{SANS}" font-size="15" font-weight="600" fill="{c['text']}">{esc(label)}</text>
</svg>'''


BUTTONS = [("portfolio", "Portfolio", "globe"), ("linkedin", "LinkedIn", "brief"),
           ("scholar", "Google Scholar", "cap")]


def main():
    for theme in THEMES:
        write(f"hero-{theme}.svg", hero(theme))
        write(f"about-{theme}.svg", terminal(theme))
        write(f"stats-{theme}.svg", stats(theme))
        for p in PROJECTS:
            write(f"card-{p['slug']}-{theme}.svg", card(theme, p))
        for slug, label, kind in BUTTONS:
            write(f"btn-{slug}-{theme}.svg", button(theme, label, kind))
    print("wrote", len(list(OUT.glob("*.svg"))), "files to", OUT)


if __name__ == "__main__":
    main()
