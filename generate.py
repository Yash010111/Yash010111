import json
import random
import sys
import urllib.request

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "Yash010111"
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else "animated-contrib.svg"

API_URL = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"

LEVEL_COLORS = ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']

def fetch_real_data():
    try:
        req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return data["contributions"]
    except Exception as e:
        print(f"WARN: live fetch failed ({e}); falling back to sample data", file=sys.stderr)
        return None

def build_grid(contributions):
    """Turn a flat list of {date, count, level} into a 53-col x 7-row grid
    aligned the same way GitHub lays out weeks (columns) x weekdays (rows)."""
    import datetime
    by_date = {c["date"]: c for c in contributions}
    dates = sorted(by_date.keys())
    if not dates:
        return None
    end = datetime.date.fromisoformat(dates[-1])
    start = end - datetime.timedelta(days=370)
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)  # align to Sunday

    grid = {}
    d = start
    col = 0
    while d <= end:
        row = (d.weekday() + 1) % 7  # 0=Sun ... 6=Sat
        rec = by_date.get(d.isoformat())
        level = rec["level"] if rec else 0
        grid[(col, row)] = LEVEL_COLORS[min(level, 4)]
        if row == 6:
            col += 1
        d += datetime.timedelta(days=1)
    return grid, col + 1

def sample_grid(cols=53, rows=7, seed=7):
    random.seed(seed)
    grid = {}
    for c in range(cols):
        for r in range(rows):
            weight = random.random()
            if weight < 0.35:
                lvl = 0
            elif weight < 0.6:
                lvl = 1
            elif weight < 0.8:
                lvl = 2
            elif weight < 0.93:
                lvl = 3
            else:
                lvl = 4
            grid[(c, r)] = LEVEL_COLORS[lvl]
    return grid, cols

letters = {
    'Y': ["10001","10001","01010","00100","00100","00100","00100"],
    'A': ["01110","10001","10001","11111","10001","10001","10001"],
    'S': ["01111","10000","10000","01110","00001","00001","11110"],
    'H': ["10001","10001","10001","11111","10001","10001","10001"],
}

def build_svg(grid, cols, word="YASH"):
    rows = 7
    cell, gap = 10, 3
    step = cell + gap
    margin_x = 20
    margin_top = 50
    zone_gap = 22

    main_h = rows * step - gap
    form_h = rows * step - gap
    width = margin_x * 2 + cols * step - gap
    height = margin_top + main_h + zone_gap + form_h + 20

    letter_w, spacing = 5, 1
    total_letter_cols = len(word) * letter_w + (len(word) - 1) * spacing
    col_offset = (cols - total_letter_cols) // 2

    mask = {}
    cur_col = col_offset
    for ch in word:
        pattern = letters[ch]
        for r in range(7):
            for i, bit in enumerate(pattern[r]):
                if bit == '1':
                    mask[(cur_col + i, r)] = True
        cur_col += letter_w + spacing

    total_dur = 10.0
    fall_base = 1.5
    fall_stagger_unit = 0.035
    fall_dur = 0.5
    hold_end = 5.5
    return_stagger_unit = 0.02
    return_dur = 0.5

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%">')
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" rx="10" fill="#0d1117"/>')
    parts.append(f'<text x="{margin_x}" y="28" fill="#c9d1d9" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="16" font-weight="600">JARVIS // CONTRIBUTION MATRIX</text>')
    parts.append(f'<text x="{margin_x}" y="44" fill="#8b949e" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="11">live data · {USERNAME}</text>')

    for c in range(cols):
        for r in range(rows):
            x = margin_x + c * step
            y = margin_top + r * step
            home_color = grid.get((c, r), LEVEL_COLORS[0])

            if (c, r) in mask:
                stagger_f = (c - col_offset) * fall_stagger_unit
                fall_start = fall_base + stagger_f
                arrive = fall_start + fall_dur
                stagger_r = (c - col_offset) * return_stagger_unit
                ret_start = hold_end + stagger_r
                ret_end = ret_start + return_dur

                target_y = margin_top + main_h + zone_gap + r * step
                bright = '#39d353'

                keytimes = f"0;{fall_start/total_dur:.4f};{arrive/total_dur:.4f};{ret_start/total_dur:.4f};{ret_end/total_dur:.4f};1"
                y_vals = f"{y};{y};{target_y};{target_y};{y};{y}"
                fill_vals = f"{home_color};{home_color};{bright};{bright};{home_color};{home_color}"

                parts.append(
                    f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{home_color}">'
                    f'<animate attributeName="y" values="{y_vals}" keyTimes="{keytimes}" dur="{total_dur}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="fill" values="{fill_vals}" keyTimes="{keytimes}" dur="{total_dur}s" repeatCount="indefinite"/>'
                    f'</rect>'
                )
            else:
                parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{home_color}"/>')

    parts.append('</svg>')
    return "\n".join(parts)

def main():
    contributions = fetch_real_data()
    if contributions:
        grid, cols = build_grid(contributions)
        print(f"Using LIVE data for {USERNAME}: {cols} weeks")
    else:
        grid, cols = sample_grid()
        print("Using SAMPLE placeholder data")

    svg = build_svg(grid, cols)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH}")

if __name__ == "__main__":
    main()
