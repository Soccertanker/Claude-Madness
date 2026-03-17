#!/usr/bin/env python3
"""
2026 NCAA March Madness Bracket Simulator

Methodology:
  - Win probability based on seeds: p(team) = opponent_seed / (seed1 + seed2)
    e.g. 1 vs 8: 1-seed wins with prob 8/9, 8-seed wins with prob 1/9
  - Teams with confirmed season-ending star player injuries take a 20% penalty
    to their win probability (renormalized afterward)
"""

import random
import sys
from datetime import datetime

# ----------------------------------------------------------------------------
# Confirmed season-ending / almost-certainly-out star player injuries
# ----------------------------------------------------------------------------
INJURED_TEAMS = {
    "Texas Tech":      "JT Toppin - torn ACL (Feb 17); Wooden Award contender, 21.8 ppg / 10.8 reb",
    "BYU":             "Richie Saunders - torn ACL (mid-Feb); key starter alongside Dybantsa",
    "Clemson":         "Carter Welling - torn ACL (ACC Tournament); 2nd-leading scorer, top rebounder",
    "North Carolina":  "Caleb Wilson - season-ending thumb fracture; projected top-5 NBA pick",
    "Michigan":        "L.J. Cason - torn ACL",
    "Villanova":       "Matt Hodge - torn ACL",
}

INJURY_PENALTY = 0.20  # 20% reduction to win probability

# Region colors (matches bracket.html)
REGION_COLORS = {
    "East":    "#4488ff",
    "West":    "#ff6644",
    "South":   "#44cc88",
    "Midwest": "#cc44ff",
}

# Conference info for HTML output
TEAM_CONF = {
    # East
    "Duke": "ACC", "UConn": "Big East", "Michigan State": "Big Ten",
    "Kansas": "Big 12", "St. John's": "Big East", "Louisville": "ACC",
    "UCLA": "Big Ten", "Ohio State": "Big Ten", "TCU": "Big 12",
    "UCF": "AAC", "South Florida": "AAC", "Northern Iowa": "MVC",
    "Cal Baptist": "WAC", "North Dakota State": "Summit", "Furman": "SoCon",
    "Siena": "MAAC",
    # West
    "Arizona": "Big 12", "Purdue": "Big Ten", "Gonzaga": "WCC",
    "Arkansas": "SEC", "Wisconsin": "Big Ten", "BYU": "Big 12",
    "Miami (FL)": "ACC", "Villanova": "Big East", "Utah State": "MWC",
    "Missouri": "SEC", "High Point": "Big South", "Hawaii": "Big West",
    "Kennesaw State": "ASUN", "Queens": "ASUN", "LIU": "America East",
    # South
    "Florida": "SEC", "Houston": "Big 12", "Illinois": "Big Ten",
    "Nebraska": "Big Ten", "Vanderbilt": "SEC", "North Carolina": "ACC",
    "St. Mary's": "WCC", "Clemson": "ACC", "Iowa": "Big Ten",
    "Texas A&M": "SEC", "VCU": "Atlantic 10", "McNeese": "Southland",
    "Troy": "Sun Belt", "Penn": "Ivy", "Idaho": "Big Sky",
    # Midwest
    "Michigan": "Big Ten", "Iowa State": "Big 12", "Virginia": "ACC",
    "Alabama": "SEC", "Texas Tech": "Big 12", "Tennessee": "SEC",
    "Kentucky": "SEC", "Georgia": "SEC", "St. Louis": "Atlantic 10",
    "Santa Clara": "WCC", "Akron": "MAC", "Hofstra": "CAA",
    "Wright State": "Horizon", "Tennessee State": "ASUN",
    # First Four play-in names
    "UMBC": "AE", "Howard": "MEAC", "Prairie View A&M": "SWAC",
    "Lehigh": "Patriot", "Texas": "Big 12", "NC State": "ACC",
    "Miami (OH)": "MAC", "SMU": "AAC",
}


# ----------------------------------------------------------------------------
# Core simulation logic
# ----------------------------------------------------------------------------
def win_prob(seed_self, seed_opp, team_self, team_opp):
    """Return win probability for team_self, accounting for injury penalties."""
    total = seed_self + seed_opp
    p_self = seed_opp / total
    p_opp  = seed_self / total

    if team_self in INJURED_TEAMS:
        p_self *= (1 - INJURY_PENALTY)
    if team_opp in INJURED_TEAMS:
        p_opp *= (1 - INJURY_PENALTY)

    return p_self / (p_self + p_opp)  # renormalize


def simulate_game(team1, seed1, team2, seed2, quiet=False):
    p1 = win_prob(seed1, seed2, team1, team2)
    inj1 = " [INJ]" if team1 in INJURED_TEAMS else ""
    inj2 = " [INJ]" if team2 in INJURED_TEAMS else ""

    if not quiet:
        print(f"    ({seed1}) {team1}{inj1}  vs  ({seed2}) {team2}{inj2}")
        print(f"         odds: {p1*100:.1f}% / {(1-p1)*100:.1f}%", end="")

    winner = (team1, seed1) if random.random() < p1 else (team2, seed2)
    loser  = (team2, seed2) if winner[0] == team1 else (team1, seed1)

    if not quiet:
        print(f"  →  ({winner[1]}) {winner[0]}")

    return winner[0], winner[1], loser[0], loser[1]


# ----------------------------------------------------------------------------
# Region simulator
# ----------------------------------------------------------------------------
def simulate_region(region_name, teams):
    """
    teams: list of (seed, team_name) for seeds 1–16.
    Returns (champion_name, champion_seed, region_results).

    region_results = {
        'r1':  [(winner, wseed, loser, lseed), ...],  # 8 games
        'r2':  [...],                                   # 4 games
        's16': [...],                                   # 2 games
        'e8':  [...]                                    # 1 game
    }
    """
    seed_map = {s: t for s, t in teams}

    # Standard NCAA bracket slot order within a region
    # Top half: 1v16, 8v9, 5v12, 4v13
    # Bottom half: 6v11, 3v14, 7v10, 2v15
    first_round = [(1,16), (8,9), (5,12), (4,13), (6,11), (3,14), (7,10), (2,15)]
    round_names = ["First Round", "Second Round", "Sweet 16", "Elite Eight"]
    round_keys  = ["r1", "r2", "s16", "e8"]

    current = [(seed_map[s1], s1, seed_map[s2], s2) for s1, s2 in first_round]

    print(f"\n{'═'*55}")
    print(f"  {region_name.upper()} REGION")
    print(f"{'═'*55}")

    region_results = {}
    teams_in_play = None  # will be list of (team, seed) winners

    for rnd_idx, (round_name, rkey) in enumerate(zip(round_names, round_keys)):
        print(f"\n  {round_name}:")
        if rnd_idx == 0:
            matchups = current
        else:
            matchups = [(teams_in_play[i][0], teams_in_play[i][1],
                         teams_in_play[i+1][0], teams_in_play[i+1][1])
                        for i in range(0, len(teams_in_play), 2)]

        round_results = []
        winners = []
        for t1, s1, t2, s2 in matchups:
            wt, ws, lt, ls = simulate_game(t1, s1, t2, s2)
            winners.append((wt, ws))
            round_results.append((wt, ws, lt, ls))

        region_results[rkey] = round_results
        teams_in_play = winners

    champ_team, champ_seed = teams_in_play[0]
    print(f"\n  *** {region_name} Champion: ({champ_seed}) {champ_team} ***")
    return champ_team, champ_seed, region_results


# ----------------------------------------------------------------------------
# HTML results writer
# ----------------------------------------------------------------------------
def _team_slot_html(team, seed, region_color, won, conf=None):
    """Return an HTML string for a filled-in team slot (winner or loser styling)."""
    is_inj = team in INJURED_TEAMS
    inj_note = INJURED_TEAMS.get(team, "")

    if won:
        border_style = f"border-left: 3px solid {region_color};" if not is_inj else \
                       f"border-left: 3px solid #ff4444;"
        bg_style = f"background: {region_color}22;"
        opacity_style = "opacity: 1;"
        name_style = f"color: #ffffff; font-weight: 600;"
    else:
        border_style = "border-left: 3px solid #333;"
        bg_style = "background: #0d0d1e;"
        opacity_style = "opacity: 0.35;"
        name_style = "text-decoration: line-through; color: #888;"

    title_attr = f' title="{team} [INJ]: {inj_note}"' if is_inj else ''

    inj_badge = ''
    if is_inj:
        inj_badge = '<span class="inj-badge">INJ</span>'

    conf_tag = ''
    if conf:
        conf_tag = f'<span class="conf-tag">{conf}</span>'

    seed_color = region_color if won else "#555"

    return (
        f'<div class="team-slot" style="{border_style} {bg_style} {opacity_style}"{title_attr}>'
        f'<span class="seed-badge" style="color:{seed_color}">{seed}</span>'
        f'<span class="team-name" style="{name_style}">{team}</span>'
        f'{conf_tag}'
        f'{inj_badge}'
        f'</div>'
    )


def _render_region_html(region_name, region_color, region_results):
    """Render a full region bracket with winners filled in."""
    MATCHUP_ORDER = [(1,16),(8,9),(5,12),(4,13),(6,11),(3,14),(7,10),(2,15)]

    # Build a quick lookup of all teams that appeared in R1 to get seeds
    r1 = region_results['r1']
    all_r1_teams = {}  # name -> seed
    for wt, ws, lt, ls in r1:
        all_r1_teams[wt] = ws
        all_r1_teams[lt] = ls

    def get_conf(t):
        return TEAM_CONF.get(t, "")

    round_keys  = ['r1', 'r2', 's16', 'e8']
    round_labels = ['First Round', 'Second Round', 'Sweet 16', 'Elite Eight']
    round_widths = [220, 130, 110, 100]

    html = f'''
    <div class="region-panel" style="border-color:{region_color}44;">
      <div class="region-header" style="border-bottom-color:{region_color}44; background:linear-gradient(90deg,{region_color}18 0%,transparent 100%);">
        <div class="region-dot" style="background:{region_color};box-shadow:0 0 8px {region_color};"></div>
        <div class="region-title" style="color:{region_color};">{region_name} Region</div>
      </div>
      <div class="round-labels">
    '''
    for label, w in zip(round_labels, round_widths):
        html += f'<div class="round-label-cell" style="width:{w}px;">{label}</div>'
    html += '</div>\n<div class="bracket-body">\n'

    # ── Round 1 column ──────────────────────────────────────────────────────
    html += f'<div class="round-col" style="width:{round_widths[0]}px;gap:10px;">\n'
    for wt, ws, lt, ls in r1:
        wconf = get_conf(wt)
        lconf = get_conf(lt)
        html += f'<div class="matchup" style="--line:{region_color}55;">\n'
        # figure out who was top vs bottom by original seed order
        # use MATCHUP_ORDER to determine which was s1
        html += _team_slot_html(wt, ws, region_color, True,  wconf) + '\n'
        html += _team_slot_html(lt, ls, region_color, False, lconf) + '\n'
        html += '</div>\n'
    html += '</div>\n'

    # ── Rounds 2, S16, E8 ────────────────────────────────────────────────────
    for rnd_idx in range(1, 4):
        rkey   = round_keys[rnd_idx]
        rwidth = round_widths[rnd_idx]
        games  = region_results[rkey]

        # connector strip
        html += f'<div class="round-col" style="width:20px;gap:10px;justify-content:space-around;">\n'
        for _ in games:
            html += f'<div class="connector" style="--line:{region_color}55;"></div>\n'
        html += '</div>\n'

        html += f'<div class="round-col" style="width:{rwidth}px;gap:10px;">\n'

        if rnd_idx == 3:
            # Elite Eight — single winner slot only (no matchup bracket)
            wt, ws, lt, ls = games[0]
            wconf = get_conf(wt)
            html += _team_slot_html(wt, ws, region_color, True, wconf) + '\n'
        else:
            for wt, ws, lt, ls in games:
                wconf = get_conf(wt)
                lconf = get_conf(lt)
                html += f'<div class="blank-matchup" style="--line:{region_color}55;">\n'
                html += _team_slot_html(wt, ws, region_color, True,  wconf) + '\n'
                html += _team_slot_html(lt, ls, region_color, False, lconf) + '\n'
                html += '</div>\n'

        html += '</div>\n'

    html += '</div>\n</div>\n'
    return html


def write_html_results(all_results, filename=None):
    """
    Generate a beautiful HTML file showing all bracket results.

    all_results keys:
      'first_four': list of (wt, ws, lt, ls)
      'east', 'west', 'south', 'midwest': region_results dicts
      'final_four': [(wt, ws, lt, ls), (wt, ws, lt, ls)]
      'championship': (wt, ws, lt, ls)
      'champion': (team, seed)
      'rng_seed': int or None
    """
    if filename is None:
        rng_seed = all_results.get('rng_seed')
        suffix = str(rng_seed) if rng_seed is not None else datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'bracket_results_{suffix}.html'
    champion, champ_seed = all_results['champion']
    champ_region = all_results.get('champion_region', '')
    champ_color  = REGION_COLORS.get(champ_region, '#ffd700')

    # ── Injury table rows ─────────────────────────────────────────────────────
    injury_rows_html = ''
    injury_notes = [
        ("JT Toppin",      "Texas Tech",     "(5) Midwest", "Torn ACL – Feb 17",            "Wooden Award contender, 21.8 ppg / 10.8 reb"),
        ("Caleb Wilson",   "North Carolina", "(6) South",   "Season-ending thumb fracture",  "Projected top-5 NBA pick"),
        ("Carter Welling", "Clemson",        "(8) South",   "Torn ACL – ACC Tournament",     "2nd-leading scorer, top rebounder"),
        ("Richie Saunders","BYU",            "(6) West",    "Torn ACL – mid-February",       "Key starter alongside AJ Dybantsa"),
        ("L.J. Cason",     "Michigan",       "(1) Midwest", "Torn ACL",                      "Key rotation player for #1 seed"),
        ("Matt Hodge",     "Villanova",      "(8) West",    "Torn ACL",                      "Starter for Big East squad"),
    ]
    for player, team, seed_r, injury, impact in injury_notes:
        injury_rows_html += f'''
        <tr>
          <td class="player-name">{player}</td>
          <td class="team-cell">{team}</td>
          <td class="seed-region-cell">{seed_r}</td>
          <td class="injury-text">{injury}</td>
          <td class="impact-text">{impact}</td>
        </tr>'''

    # ── First Four section ────────────────────────────────────────────────────
    ff_games_info = [
        {"seed": 16, "dest": "vs (1) Michigan — Midwest"},
        {"seed": 16, "dest": "vs (1) Florida — South"},
        {"seed": 11, "dest": "vs (6) BYU — West"},
        {"seed": 11, "dest": "vs (6) Tennessee — Midwest"},
    ]
    ff_html = '<div class="first-four-grid">\n'
    for i, (wt, ws, lt, ls) in enumerate(all_results['first_four']):
        info = ff_games_info[i]
        ff_html += f'''
        <div class="ff-card">
          <div class="ff-card-label">({info["seed"]}) Play-In</div>
          <div class="ff-team">
            <span class="ff-seed" style="color:#ffd700;">{ws}</span>
            <span style="color:#fff;font-weight:600;">{wt}</span>
            <span class="inj-badge" style="margin-left:auto;display:{"inline" if wt in INJURED_TEAMS else "none"}">INJ</span>
          </div>
          <div class="ff-vs">DEFEATED</div>
          <div class="ff-team">
            <span class="ff-seed" style="color:#555;">{ls}</span>
            <span style="text-decoration:line-through;color:#555;">{lt}</span>
          </div>
          <div class="ff-arrow">→ {wt} advances {info["dest"]}</div>
        </div>'''
    ff_html += '\n</div>\n'

    # ── Region panels ─────────────────────────────────────────────────────────
    regions_html = '<div class="regions-grid">\n'
    for rname in ['East', 'West', 'South', 'Midwest']:
        rkey   = rname.lower()
        rcolor = REGION_COLORS[rname]
        regions_html += _render_region_html(rname, rcolor, all_results[rkey])
    regions_html += '</div>\n'

    # ── Final Four ────────────────────────────────────────────────────────────
    ff1_w, ff1_ws, ff1_l, ff1_ls = all_results['final_four'][0]
    ff2_w, ff2_ws, ff2_l, ff2_ls = all_results['final_four'][1]
    champ_w, champ_ws, champ_l, champ_ls = all_results['championship']

    def region_of(team):
        for rname in ['East', 'West', 'South', 'Midwest']:
            rr = all_results[rname.lower()]
            for wt, ws, lt, ls in rr['e8']:
                if wt == team:
                    return rname
        return ''

    def color_of(team):
        return REGION_COLORS.get(region_of(team), '#888')

    def finals_slot(team, seed, won):
        rc = color_of(team)
        if won:
            return (f'<div class="team-slot" style="border-left:3px solid {rc};background:{rc}22;height:44px;">'
                    f'<span class="seed-badge" style="color:{rc};">{seed}</span>'
                    f'<span class="team-name" style="color:#fff;font-weight:600;">{team}</span>'
                    f'</div>')
        else:
            return (f'<div class="team-slot" style="border-left:3px solid #333;background:#0d0d1e;opacity:0.35;height:44px;">'
                    f'<span class="seed-badge" style="color:#555;">{seed}</span>'
                    f'<span class="team-name" style="text-decoration:line-through;color:#888;">{team}</span>'
                    f'</div>')

    finals_html = f'''
    <div class="finals-section">
      <div class="finals-grid">
        <div class="finals-side">
          <div class="finals-label">Final Four · East vs South</div>
          {finals_slot(ff1_w, ff1_ws, True)}
          <div style="padding:4px 0; text-align:center; font-size:0.7rem; color:#555; letter-spacing:.15em;">defeated</div>
          {finals_slot(ff1_l, ff1_ls, False)}
        </div>
        <div class="finals-divider">vs</div>
        <div class="finals-side">
          <div class="finals-label">Final Four · West vs Midwest</div>
          {finals_slot(ff2_w, ff2_ws, True)}
          <div style="padding:4px 0; text-align:center; font-size:0.7rem; color:#555; letter-spacing:.15em;">defeated</div>
          {finals_slot(ff2_l, ff2_ls, False)}
        </div>
      </div>
      <div class="championship-box" style="border-color:{champ_color}88;background:{champ_color}08;">
        <div class="champ-label" style="color:{champ_color};">NATIONAL CHAMPIONSHIP</div>
        <div style="display:flex;gap:20px;justify-content:center;align-items:center;margin-top:10px;">
          {finals_slot(champ_w, champ_ws, True)}
          <span style="font-family:'Bebas Neue',sans-serif;font-size:1.1rem;color:#555;">def.</span>
          {finals_slot(champ_l, champ_ls, False)}
        </div>
      </div>
    </div>'''

    # ── Full HTML ─────────────────────────────────────────────────────────────
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026 NCAA March Madness — Results</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700&family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:       #0a0a1a;
    --surface:  #12122a;
    --surface2: #1a1a35;
    --border:   #2a2a4a;
    --gold:     #ffd700;
    --gold-dim: #b8960a;
    --text:     #e8e8f5;
    --text-dim: #7878a8;
    --east:     #4488ff;
    --west:     #ff6644;
    --south:    #44cc88;
    --midwest:  #cc44ff;
    --injury:   #ff4444;
    --team-h:   34px;
    --gap:      6px;
    --line:     #3a3a6a;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
    overflow-x: auto;
  }}

  /* ── Champion banner ── */
  .champion-banner {{
    text-align: center;
    padding: 56px 20px 44px;
    background: linear-gradient(180deg, #0d0d2b 0%, transparent 100%);
    position: relative;
    overflow: hidden;
  }}
  .champion-banner::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse 80% 60% at 50% 0%, {champ_color}14 0%, transparent 70%);
    pointer-events: none;
  }}
  .champion-trophy {{
    font-size: 3.5rem;
    margin-bottom: 8px;
    filter: drop-shadow(0 0 20px {champ_color});
  }}
  .champion-label {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    letter-spacing: 0.4em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 10px;
  }}
  .champion-name {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(3.5rem, 9vw, 8rem);
    letter-spacing: 0.06em;
    background: linear-gradient(135deg, #ffe066, {champ_color}, #ffaa00);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 40px {champ_color}66);
    line-height: 1;
  }}
  .champion-seed {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: {champ_color};
    letter-spacing: 0.15em;
    margin-top: 6px;
  }}
  .glow-bar {{
    width: 160px;
    height: 3px;
    background: linear-gradient(90deg, transparent, {champ_color}, transparent);
    margin: 20px auto 0;
    border-radius: 2px;
  }}
  .site-title {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(1.6rem, 4vw, 3rem);
    letter-spacing: 0.1em;
    background: linear-gradient(135deg, #ffe066, #ffd700, #ffaa00);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 20px rgba(255,215,0,0.3));
    margin-bottom: 32px;
  }}

  /* ── Section labels ── */
  .section-label {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.6rem;
    letter-spacing: 0.15em;
    color: var(--gold);
    text-align: center;
    margin: 40px 0 18px;
    text-shadow: 0 0 20px rgba(255,215,0,0.4);
  }}

  /* ── First Four ── */
  .first-four-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    max-width: 960px;
    margin: 0 auto 16px;
    padding: 0 20px;
  }}
  @media (max-width: 800px) {{ .first-four-grid {{ grid-template-columns: repeat(2,1fr); }} }}
  .ff-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
    transition: transform 0.2s, box-shadow 0.2s;
  }}
  .ff-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.5); }}
  .ff-card-label {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.2em; color: var(--text-dim);
    text-transform: uppercase; margin-bottom: 8px;
  }}
  .ff-team {{ display:flex; align-items:center; gap:8px; padding:5px 0; font-size:0.85rem; font-weight:500; }}
  .ff-seed {{ font-family:'Rajdhani',sans-serif; font-weight:700; font-size:0.8rem; min-width:20px; }}
  .ff-vs {{
    text-align:center; font-size:0.7rem; font-weight:700;
    color:var(--text-dim); letter-spacing:0.15em; padding:2px 0;
  }}
  .ff-arrow {{ font-size:0.7rem; color:var(--text-dim); margin-top:8px; font-style:italic; }}

  /* ── Regions grid ── */
  .regions-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 32px;
    padding: 0 20px 40px;
    max-width: 1800px;
    margin: 0 auto;
  }}
  @media (max-width: 1200px) {{ .regions-grid {{ grid-template-columns: 1fr; }} }}

  /* ── Region panel ── */
  .region-panel {{
    background: var(--surface);
    border-radius: 14px;
    border: 1px solid var(--border);
    overflow: hidden;
  }}
  .region-header {{
    padding: 14px 20px;
    display: flex; align-items: center; gap: 12px;
    border-bottom: 1px solid var(--border);
  }}
  .region-dot {{ width:12px; height:12px; border-radius:50%; flex-shrink:0; }}
  .region-title {{ font-family:'Bebas Neue',sans-serif; font-size:1.4rem; letter-spacing:0.12em; }}
  .round-labels {{
    display: flex; gap: 0; padding: 0 14px;
    background: var(--surface2); border-bottom: 1px solid var(--border);
  }}
  .round-label-cell {{
    font-family:'Rajdhani',sans-serif; font-size:0.65rem; font-weight:600;
    letter-spacing:0.18em; color:var(--text-dim); text-transform:uppercase;
    text-align:center; padding:6px 0;
  }}
  .bracket-body {{
    display: flex; flex-direction: row;
    padding: 14px; gap: 0; align-items: stretch; min-height: 520px;
  }}
  .round-col {{ display:flex; flex-direction:column; justify-content:space-around; flex-shrink:0; }}

  /* ── Team slots ── */
  .team-slot {{
    height: var(--team-h);
    display: flex; align-items: center; gap: 6px;
    padding: 0 8px;
    border: 1px solid var(--border); border-radius: 6px;
    font-size: 0.78rem; font-weight: 500;
    white-space: nowrap; overflow: hidden;
    transition: box-shadow 0.15s;
    position: relative; cursor: default;
  }}
  .team-slot:hover {{ z-index: 2; box-shadow: 0 2px 16px rgba(0,0,0,0.5); }}
  .seed-badge {{ font-family:'Rajdhani',sans-serif; font-weight:700; font-size:0.75rem; min-width:18px; text-align:center; flex-shrink:0; }}
  .team-name {{ flex:1; overflow:hidden; text-overflow:ellipsis; }}
  .conf-tag {{
    font-size:0.62rem; font-weight:600; color:var(--text-dim);
    background:rgba(255,255,255,0.06); border-radius:3px;
    padding:1px 4px; flex-shrink:0; letter-spacing:0.05em;
  }}
  .inj-badge {{
    font-size:0.6rem; font-weight:700; color:#fff; background:var(--injury);
    border-radius:3px; padding:1px 4px; flex-shrink:0; letter-spacing:0.05em;
    animation: inj-pulse 2s ease-in-out infinite;
  }}
  @keyframes inj-pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.6; }} }}

  /* ── Matchup wrappers ── */
  .matchup {{
    display: flex; flex-direction: column; gap: var(--gap);
    position: relative; padding-right: 22px;
  }}
  .matchup .team-slot:first-child::after {{
    content: ''; position: absolute; right: 0; top: 50%;
    width: 22px; border-top: 2px solid var(--line); border-right: 2px solid var(--line);
    height: calc(50% + var(--gap)/2 + var(--team-h)/2 + 2px);
  }}
  .matchup .team-slot:last-child::after {{
    content: ''; position: absolute; right: 0; bottom: 50%;
    width: 22px; border-bottom: 2px solid var(--line); border-right: 2px solid var(--line);
    height: calc(50% + var(--gap)/2 + var(--team-h)/2 + 2px);
  }}
  .blank-matchup {{
    display: flex; flex-direction: column; gap: var(--gap);
    padding-right: 22px; position: relative;
  }}
  .blank-matchup .team-slot:first-child::after {{
    content: ''; position: absolute; right: 0; top: 50%;
    width: 22px; border-top: 2px solid var(--line); border-right: 2px solid var(--line);
    height: calc(50% + var(--gap)/2 + var(--team-h)/2 + 2px);
  }}
  .blank-matchup .team-slot:last-child::after {{
    content: ''; position: absolute; right: 0; bottom: 50%;
    width: 22px; border-bottom: 2px solid var(--line); border-right: 2px solid var(--line);
    height: calc(50% + var(--gap)/2 + var(--team-h)/2 + 2px);
  }}
  .connector {{
    width: 20px; flex-shrink: 0; position: relative; align-self: stretch;
  }}
  .connector::before {{
    content: ''; position: absolute; left: 0; top: 50%;
    width: 100%; height: 2px;
    background: var(--line); transform: translateY(-50%);
  }}

  /* ── Finals section ── */
  .finals-section {{ max-width: 700px; margin: 0 auto 48px; padding: 0 20px; }}
  .finals-grid {{ display: grid; grid-template-columns: 1fr 60px 1fr; gap: 0; align-items: center; }}
  .finals-side {{ display: flex; flex-direction: column; gap: 8px; }}
  .finals-label {{
    font-family: 'Rajdhani', sans-serif; font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.2em; color: var(--text-dim); text-transform: uppercase;
    text-align: center; margin-bottom: 4px;
  }}
  .finals-divider {{
    text-align: center; font-family: 'Bebas Neue', sans-serif;
    font-size: 1.2rem; color: var(--gold); letter-spacing: 0.1em;
  }}
  .championship-box {{
    margin-top: 24px; border-radius: 12px; padding: 24px; text-align: center;
    border: 2px solid;
  }}
  .champ-label {{
    font-family: 'Bebas Neue', sans-serif; font-size: 1.3rem;
    letter-spacing: 0.2em; margin-bottom: 14px;
  }}

  /* ── Injury table ── */
  .injury-section {{ max-width: 1100px; margin: 0 auto 60px; padding: 0 20px; }}
  .injury-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  .injury-table th {{
    font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 0.7rem;
    letter-spacing: 0.18em; text-transform: uppercase; color: var(--text-dim);
    padding: 10px 14px; background: var(--surface2); border-bottom: 2px solid var(--border); text-align: left;
  }}
  .injury-table td {{ padding: 11px 14px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  .injury-table tr:hover td {{ background: rgba(255,255,255,0.025); }}
  .injury-table .player-name {{ font-weight: 600; color: var(--text); }}
  .injury-table .team-cell {{ color: var(--text-dim); }}
  .injury-table .injury-text {{ color: var(--injury); font-weight: 500; }}
  .injury-table .impact-text {{ color: var(--text-dim); font-style: italic; font-size: 0.8rem; }}
  .seed-region-cell {{ white-space: nowrap; }}

  .divider {{ border:none; border-top:1px solid var(--border); margin:0 20px 40px; }}
</style>
</head>
<body>

<!-- ══════════════════ CHAMPION BANNER ══════════════════════════════════════ -->
<div class="champion-banner">
  <div class="site-title">2026 NCAA March Madness — Results</div>
  <div class="champion-trophy">🏆</div>
  <div class="champion-label">2026 National Champion</div>
  <div class="champion-name">{champion}</div>
  <div class="champion-seed">#{champ_seed} Seed</div>
  <div class="glow-bar"></div>
</div>

<!-- ══════════════════ FIRST FOUR ══════════════════════════════════════════ -->
<div class="section-label">First Four Results</div>
{ff_html}

<hr class="divider">

<!-- ══════════════════ REGIONS ════════════════════════════════════════════ -->
<div class="section-label">Regional Brackets</div>
{regions_html}

<hr class="divider">

<!-- ══════════════════ FINALS ═════════════════════════════════════════════ -->
<div class="section-label">Final Four &amp; Championship</div>
{finals_html}

<hr class="divider">

<!-- ══════════════════ INJURY TABLE ══════════════════════════════════════ -->
<div class="section-label">Injury Report</div>
<div class="injury-section">
  <table class="injury-table">
    <thead>
      <tr>
        <th>Player</th><th>Team</th><th>Seed / Region</th><th>Injury</th><th>Impact</th>
      </tr>
    </thead>
    <tbody>
      {injury_rows_html}
    </tbody>
  </table>
</div>

</body>
</html>'''

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)


# ----------------------------------------------------------------------------
# Full tournament
# ----------------------------------------------------------------------------
def simulate_tournament(seed=None):
    if seed is not None:
        random.seed(seed)

    print("=" * 55)
    print("  2026 NCAA MARCH MADNESS BRACKET SIMULATOR")
    print("=" * 55)
    print("\nMethodology: p(win) = opponent_seed / (sum of seeds)")
    print(f"Injury penalty: {int(INJURY_PENALTY*100)}% reduction for teams")
    print("  with confirmed season-ending star player injuries\n")
    print("Injured teams:")
    for team, note in INJURED_TEAMS.items():
        print(f"  [INJ] {team}: {note}")

    # ── First Four ──────────────────────────────────────────────────────────
    print(f"\n{'═'*55}")
    print("  FIRST FOUR  (Dayton, OH — March 17–18)")
    print(f"{'═'*55}")
    print("\n  (16) Play-in:")
    ff16_mid, ff16_mid_s, *_ = simulate_game("UMBC",             16, "Howard",          16)
    print("  → advances to face (1) Michigan — Midwest\n")
    ff16_sth, ff16_sth_s, *_ = simulate_game("Prairie View A&M", 16, "Lehigh",          16)
    print("  → advances to face (1) Florida — South\n")
    print("  (11) Play-in:")
    ff11_wst, ff11_wst_s, *_ = simulate_game("Texas",            11, "NC State",        11)
    print("  → advances to face (6) BYU — West\n")
    ff11_mid, ff11_mid_s, *_ = simulate_game("Miami (OH)",       11, "SMU",             11)
    print("  → advances to face (6) Tennessee — Midwest")

    # collect first four results
    first_four_results = []
    for game_args in [
        ("UMBC", 16, "Howard", 16),
        ("Prairie View A&M", 16, "Lehigh", 16),
        ("Texas", 11, "NC State", 11),
        ("Miami (OH)", 11, "SMU", 11),
    ]:
        # Re-derive from what we already know (can't replay RNG), so reconstruct:
        pass

    # Since we already simulated, reconstruct winner/loser tuples:
    first_four_results = [
        (ff16_mid, 16, "Howard" if ff16_mid == "UMBC" else "UMBC", 16),
        (ff16_sth, 16, "Lehigh" if ff16_sth == "Prairie View A&M" else "Prairie View A&M", 16),
        (ff11_wst, 11, "NC State" if ff11_wst == "Texas" else "Texas", 11),
        (ff11_mid, 11, "SMU" if ff11_mid == "Miami (OH)" else "Miami (OH)", 11),
    ]

    # ── Bracket ─────────────────────────────────────────────────────────────
    east_teams = [
        (1,  "Duke"),              (2,  "UConn"),
        (3,  "Michigan State"),    (4,  "Kansas"),
        (5,  "St. John's"),        (6,  "Louisville"),
        (7,  "UCLA"),              (8,  "Ohio State"),
        (9,  "TCU"),               (10, "UCF"),
        (11, "South Florida"),     (12, "Northern Iowa"),
        (13, "Cal Baptist"),       (14, "North Dakota State"),
        (15, "Furman"),            (16, "Siena"),
    ]

    west_teams = [
        (1,  "Arizona"),           (2,  "Purdue"),
        (3,  "Gonzaga"),           (4,  "Arkansas"),
        (5,  "Wisconsin"),         (6,  "BYU"),
        (7,  "Miami (FL)"),        (8,  "Villanova"),
        (9,  "Utah State"),        (10, "Missouri"),
        (11, ff11_wst),            (12, "High Point"),
        (13, "Hawaii"),            (14, "Kennesaw State"),
        (15, "Queens"),            (16, "LIU"),
    ]

    south_teams = [
        (1,  "Florida"),           (2,  "Houston"),
        (3,  "Illinois"),          (4,  "Nebraska"),
        (5,  "Vanderbilt"),        (6,  "North Carolina"),
        (7,  "St. Mary's"),        (8,  "Clemson"),
        (9,  "Iowa"),              (10, "Texas A&M"),
        (11, "VCU"),               (12, "McNeese"),
        (13, "Troy"),              (14, "Penn"),
        (15, "Idaho"),             (16, ff16_sth),
    ]

    midwest_teams = [
        (1,  "Michigan"),          (2,  "Iowa State"),
        (3,  "Virginia"),          (4,  "Alabama"),
        (5,  "Texas Tech"),        (6,  "Tennessee"),
        (7,  "Kentucky"),          (8,  "Georgia"),
        (9,  "St. Louis"),         (10, "Santa Clara"),
        (11, ff11_mid),            (12, "Akron"),
        (13, "Hofstra"),           (14, "Wright State"),
        (15, "Tennessee State"),   (16, ff16_mid),
    ]

    east_champ,    east_seed,    east_results    = simulate_region("East",    east_teams)
    west_champ,    west_seed,    west_results    = simulate_region("West",    west_teams)
    south_champ,   south_seed,   south_results   = simulate_region("South",   south_teams)
    midwest_champ, midwest_seed, midwest_results = simulate_region("Midwest", midwest_teams)

    # ── Final Four ──────────────────────────────────────────────────────────
    print(f"\n{'═'*55}")
    print("  FINAL FOUR")
    print(f"{'═'*55}\n")
    print("  East vs. South:")
    f1w, f1ws, f1l, f1ls = simulate_game(east_champ, east_seed, south_champ, south_seed)
    print("\n  West vs. Midwest:")
    f2w, f2ws, f2l, f2ls = simulate_game(west_champ, west_seed, midwest_champ, midwest_seed)

    # ── Championship ────────────────────────────────────────────────────────
    print(f"\n{'═'*55}")
    print("  NATIONAL CHAMPIONSHIP")
    print(f"{'═'*55}\n")
    champion, champ_seed, champ_loser, champ_loser_seed = simulate_game(f1w, f1ws, f2w, f2ws)

    print(f"\n{'═'*55}")
    print(f"  2026 NCAA CHAMPION: ({champ_seed}) {champion}")
    print(f"{'═'*55}\n")

    # figure out which region the champion came from
    champion_region = ''
    for rname, rchamp in [('East', east_champ), ('West', west_champ),
                          ('South', south_champ), ('Midwest', midwest_champ)]:
        if rchamp == champion:
            champion_region = rname
            break

    # ── Collect all results ─────────────────────────────────────────────────
    all_results = {
        'first_four':       first_four_results,
        'east':             east_results,
        'west':             west_results,
        'south':            south_results,
        'midwest':          midwest_results,
        'final_four':       [(f1w, f1ws, f1l, f1ls), (f2w, f2ws, f2l, f2ls)],
        'championship':     (champion, champ_seed, champ_loser, champ_loser_seed),
        'champion':         (champion, champ_seed),
        'champion_region':  champion_region,
        'rng_seed':         seed,
    }

    write_html_results(all_results)
    rng_suffix = str(seed) if seed is not None else datetime.now().strftime('%Y%m%d_%H%M%S')
    print(f"\nHTML results written to bracket_results_{rng_suffix}.html")

    return champion, champ_seed


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    # Usage: python bracket.py [seed]
    # If no seed given, one is derived from the current millisecond timestamp —
    # effectively random but reproducible if you note the seed printed below.
    if len(sys.argv) > 1:
        rng_seed = int(sys.argv[1])
    else:
        rng_seed = int(datetime.now().timestamp() * 1000)
    print(f"(Using RNG seed {rng_seed})\n")
    simulate_tournament(seed=rng_seed)
