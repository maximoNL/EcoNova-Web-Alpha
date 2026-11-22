"""EcoNova - Kipling Institute | SDG 4 (Quality Education) & SDG 13 (Climate Action).

Streamlit entry point and navigation router. Run with: streamlit run app.py
"""
from __future__ import annotations

import html
from datetime import date

import streamlit as st
import streamlit.components.v1 as components

from src.charts import (
    PARIS_PARTIES, PARIS_SIGNED_NOT_RATIFIED, PARIS_SOURCE_NOTE, PARIS_WITHDRAWN, PLOTLY_CONFIG,
    SURVEY_PLANNED_AREAS, UNFCCC_PARTIES, build_heat_figure, build_paris_figure,
    build_survey_placeholder_figure,
)
from src.data_loader import ContentLoadError, load_content_blocks, missing_required_ids
from src.email_service import submit_feedback
from src.games.eco_school_quest import get_eco_school_quest_html
from src.games.trash_platformer import get_trash_platformer_html
from src.models import ContentBlock, FeedbackSubmission
from src.projection import (
    BASE_OCEAN_RATE_ZJ, MAX_YEAR, MIN_YEAR, OCEAN_GAIN_2024_ZJ, OCEAN_GAIN_2025_ZJ, SCENARIOS, project,
)

st.set_page_config(page_title="EcoNova | Kipling Institute", page_icon="🌱", layout="wide",
                   initial_sidebar_state="collapsed")

esc = html.escape

# --------------------------------------------------------------------------- constants
NAV_HOME, NAV_IMPACT, NAV_ACTIONS, NAV_PLAY, NAV_ABOUT = (
    "01 / Home", "02 / Eco Impact", "03 / Green Actions", "04 / Eco-Play Zone", "05 / About Us",
)
NAV_ITEMS = [NAV_HOME, NAV_IMPACT, NAV_ACTIONS, NAV_PLAY, NAV_ABOUT]

# English card headings. Content comes from the database by ID, never by Seccion text.
CARD_HEADINGS = {
    2: "Our mission",
    3: "Environmental reality and our school survey",
    4: "Small habits, real climate action",
    5: "Learn by playing",
    6: "The EcoNova team",
    7: "Climate facts from Gapminder",
}

DAILY_TIPS = [
    "Use both sides of paper",
    "Carry reusable bags or containers",
    "Take only the food you will eat",
    "Walk or share rides to cut transport emissions",
    "Teach a peer a green habit",
]

CORE_HABITS = [
    ("bottle", "Reusable Water Bottle", "Cuts the emissions from producing single-use plastic."),
    ("bin", "Proper Waste Separation", "Reduces the methane that landfills release."),
    ("bulb", "Energy Saving", "Turn off unused lights and unplug chargers."),
]

# (title, icon, badge colour, action-guide steps)
CHALLENGES = [
    ("Bottle Buddy", "bottle", "#2B7A9B", ["Bring a reusable water bottle to school.", "Refill it instead of buying single-use bottles.", "Tell a friend why it matters."]),
    ("Bin Detective", "bin", "#40916c", ["Check how your school separates waste.", "Sort your own waste into the right bins for a whole day.", "Spot one item in the wrong bin and move it."]),
    ("Lights Out", "bulb", "#E9A23B", ["Turn off lights when you leave an empty room.", "Unplug chargers once devices are full.", "Remind one person to do the same."]),
    ("No-Waste Lunch", "lunch", "#d95d39", ["Pack your lunch in reusable containers.", "Take only the food you will eat.", "Bring leftovers home instead of throwing them away."]),
    ("Share the Page", "page", "#7b6bb5", ["Use both sides of the paper for notes.", "Share one handout with a classmate instead of printing two.", "Reuse scrap paper for drafts."]),
    ("Walk & Notice", "walk", "#1B4332", ["Walk or share a ride for one trip this week.", "On the way, notice three things about nature or pollution around you.", "Tell a peer what you noticed."]),
]

# Rewards: eco-points (XP), ranks and a certificate for finishing every challenge.
XP_PER_TIP = 10
XP_PER_CHALLENGE = 50
MAX_XP = XP_PER_TIP * len(DAILY_TIPS) + XP_PER_CHALLENGE * len(CHALLENGES)
RANKS = [(0, "Seed"), (50, "Sprout"), (120, "Sapling"), (200, "Young Tree"), (300, "Forest Guardian"), (MAX_XP, "Eco Hero")]

TEAMS = [
    ("UX/UI", "User research and interface design"),
    ("Developers", "Building the interactive web platform"),
    ("Marketing", "Climate communication"),
    ("Advertising", "Visual resources"),
]

DEMO_LEADERBOARD = [("Green Panda", 1850), ("Leafy Fox", 1620), ("Wave Rider", 1475), ("Solar Owl", 1310), ("Recycle Bear", 1190)]

ICON_PATHS = {
    "globe": "<circle cx='24' cy='24' r='18' fill='#D8F3DC' stroke='#1B4332' stroke-width='2.5'/><path d='M7 24h34M24 6c-8 9-8 27 0 36M24 6c8 9 8 27 0 36' fill='none' stroke='#2D6A4F' stroke-width='2'/>",
    "sprout": "<path d='M24 43V22' stroke='#1B4332' stroke-width='3' stroke-linecap='round'/><path d='M24 25C24 14 16 9 7 9c0 10 7 16 17 16z' fill='#2D6A4F'/><path d='M24 30c0-8 6-13 17-13 0 10-7 15-17 15z' fill='#74c69d'/>",
    "gamepad": "<rect x='4' y='14' width='40' height='22' rx='11' fill='#D8F3DC' stroke='#1B4332' stroke-width='2.5'/><path d='M15 20v10M10 25h10' stroke='#2D6A4F' stroke-width='3' stroke-linecap='round'/><circle cx='32' cy='22' r='2.6' fill='#2D6A4F'/><circle cx='37' cy='28' r='2.6' fill='#1B4332'/>",
    "bottle": "<rect x='19' y='4' width='10' height='6' rx='2' fill='#2D6A4F'/><path d='M20 10h8v6c5 3 7 6 7 11v13a3 3 0 0 1-3 3H16a3 3 0 0 1-3-3V27c0-5 2-8 7-11z' fill='#D8F3DC' stroke='#1B4332' stroke-width='2.5'/><rect x='13' y='28' width='22' height='8' fill='#74c69d'/>",
    "bin": "<rect x='8' y='9' width='32' height='6' rx='2' fill='#1B4332'/><path d='M11 15h26l-2 26a3 3 0 0 1-3 3H16a3 3 0 0 1-3-3z' fill='#D8F3DC' stroke='#1B4332' stroke-width='2.5'/><path d='M20 24l4-4 4 4M28 32l-4 4-4-4' fill='none' stroke='#2D6A4F' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'/>",
    "bulb": "<path d='M24 5a14 14 0 0 0-8 25c2 2 2 4 2 6h12c0-2 0-4 2-6A14 14 0 0 0 24 5z' fill='#D8F3DC' stroke='#1B4332' stroke-width='2.5'/><path d='M18 41h12M20 45h8' stroke='#1B4332' stroke-width='3' stroke-linecap='round'/><path d='M24 14l-4 8h8l-4 8' fill='none' stroke='#2D6A4F' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'/>",
    "lunch": "<rect x='7' y='16' width='34' height='24' rx='5' fill='#D8F3DC' stroke='#1B4332' stroke-width='2.5'/><path d='M17 16v-4a4 4 0 0 1 4-4h6a4 4 0 0 1 4 4v4' fill='none' stroke='#1B4332' stroke-width='2.5'/><path d='M7 27h34' stroke='#2D6A4F' stroke-width='2.5'/><circle cx='24' cy='27' r='3' fill='#2D6A4F'/>",
    "page": "<path d='M12 5h18l8 8v30H12z' fill='#D8F3DC' stroke='#1B4332' stroke-width='2.5' stroke-linejoin='round'/><path d='M30 5v8h8M18 22h14M18 29h14M18 36h9' fill='none' stroke='#2D6A4F' stroke-width='2.5' stroke-linecap='round'/>",
    "walk": "<ellipse cx='17' cy='32' rx='6' ry='9' fill='#2D6A4F'/><circle cx='13' cy='20' r='2.3' fill='#2D6A4F'/><circle cx='17' cy='18' r='2.3' fill='#2D6A4F'/><circle cx='21' cy='20' r='2.3' fill='#2D6A4F'/><ellipse cx='32' cy='21' rx='6' ry='9' fill='#74c69d'/><circle cx='28' cy='9' r='2.3' fill='#74c69d'/><circle cx='32' cy='7' r='2.3' fill='#74c69d'/><circle cx='36' cy='9' r='2.3' fill='#74c69d'/>",
    "lock": "<rect x='11' y='21' width='26' height='20' rx='4' fill='#94A3B8'/><path d='M16 21v-5a8 8 0 0 1 16 0v5' fill='none' stroke='#94A3B8' stroke-width='4'/>",
}


def icon_svg(name: str, size: int = 46) -> str:
    return f"<svg viewBox='0 0 48 48' width='{size}' height='{size}' aria-hidden='true'>{ICON_PATHS[name]}</svg>"


def badge_svg(icon: str, color: str, unlocked: bool) -> str:
    fill = color if unlocked else "#cbd5d1"
    glyph = ICON_PATHS[icon] if unlocked else ICON_PATHS["lock"]
    ribbon = f"<path d='M30 78 22 101l14-6 6 8 7-24z' fill='{fill}'/><path d='M66 78l8 23-14-6-6 8-7-24z' fill='{fill}' opacity='.8'/>"
    return (
        "<svg viewBox='0 0 96 106' width='84' height='93' aria-hidden='true'>" + ribbon
        + f"<circle cx='48' cy='46' r='40' fill='{fill}' stroke='#fff' stroke-width='4'/>"
        + "<circle cx='48' cy='46' r='32' fill='none' stroke='rgba(255,255,255,.55)' stroke-width='2' stroke-dasharray='3 4'/>"
        + f"<svg x='24' y='22' width='48' height='48' viewBox='0 0 48 48'>{glyph}</svg></svg>"
    )


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;800&family=Source+Sans+3:wght@400;600;700&display=swap');
/* Body font. Icon spans keep their own icon font (this fixes the "_arrow_right" text collisions). */
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button p { font-family: 'Source Sans 3', 'Segoe UI', Arial, sans-serif; }
span[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"] { font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important; }
h1, h2, h3, h4 { font-family: 'Bricolage Grotesque', 'Segoe UI', Arial, sans-serif !important; color: #1B4332; letter-spacing: -0.01em; }

/* page chrome: no sidebar, no default header */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"], header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.stApp { background: radial-gradient(1100px 480px at 92% -8%, #dff3e5 0, transparent 60%), radial-gradient(900px 420px at -8% 30%, #e8f6ee 0, transparent 58%), #F8FAF9; }
.stMainBlockContainer, [data-testid="stMainBlockContainer"] { padding-top: 0.8rem; max-width: 1220px; }

/* top navigation bar */
.st-key-topnav { position: sticky; top: 8px; z-index: 999; background: rgba(255,255,255,0.94); backdrop-filter: blur(10px); border: 1px solid #cfe5d6; border-radius: 22px; padding: 8px 18px; box-shadow: 0 8px 28px rgba(27,67,50,0.12); margin-bottom: 18px; }
.en-brand { display: flex; align-items: center; gap: 10px; font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: 1.45rem; color: #1B4332; white-space: nowrap; }
.en-brand small { display: block; font-family: 'Source Sans 3', sans-serif; font-weight: 600; font-size: 0.68rem; color: #52796f; letter-spacing: 0.04em; text-transform: uppercase; margin-top: -4px; }
.st-key-topnav [data-testid="stRadio"] > label { display: none; }
.st-key-topnav [role="radiogroup"] { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; background: #EEF5F0; padding: 5px; border-radius: 999px; }
.st-key-topnav [role="radiogroup"] label { margin: 0; padding: 8px 16px; border-radius: 999px; cursor: pointer; transition: background .15s ease, box-shadow .15s ease; }
.st-key-topnav [role="radiogroup"] label > div:first-child { display: none; }
.st-key-topnav [role="radiogroup"] label:hover { background: #D8F3DC; }
.st-key-topnav [role="radiogroup"] label:has(input:checked) { background: #2D6A4F; box-shadow: 0 3px 10px rgba(45,106,79,0.35); }
.st-key-topnav [role="radiogroup"] label p { font-weight: 600; font-size: 0.95rem; white-space: nowrap; margin: 0; }
.st-key-topnav [role="radiogroup"] label:has(input:checked) p { color: #fff !important; }
.en-chip { display: inline-flex; align-items: center; gap: 6px; background: #D8F3DC; color: #1B4332; border-radius: 999px; padding: 6px 12px; font-weight: 700; font-size: 0.85rem; white-space: nowrap; }

/* buttons */
.stButton > button, .stDownloadButton > button, [data-testid="stLinkButton"] a { border-radius: 999px; font-weight: 600; border: 1.5px solid #2D6A4F; transition: transform .12s ease, box-shadow .12s ease, background .12s ease; }
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stLinkButton"] a:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(45,106,79,0.25); border-color: #1B4332; }
[data-testid="stBaseButton-primary"] { background: #2D6A4F; color: #fff; }
[data-testid="stBaseButton-primary"]:hover { background: #1B4332; color: #fff; }

/* hero */
.en-hero { position: relative; overflow: hidden; display: flex; align-items: center; justify-content: space-between; gap: 24px; background: linear-gradient(120deg, #1B4332 0%, #2D6A4F 72%); color: #F8FAF9; border-radius: 26px; padding: 44px 48px; margin-bottom: 20px; }
.en-hero::before { content: ""; position: absolute; right: -60px; top: -80px; width: 320px; height: 320px; border-radius: 50%; background: radial-gradient(circle, rgba(116,198,157,0.45), transparent 65%); }
.en-hero::after { content: ""; position: absolute; left: 38%; bottom: -120px; width: 260px; height: 260px; border-radius: 50%; background: radial-gradient(circle, rgba(216,243,220,0.22), transparent 65%); }
.en-hero > * { position: relative; z-index: 1; }
.en-hero h1 { color: #F8FAF9 !important; font-size: clamp(2.6rem, 6vw, 4.4rem); margin: 0 0 8px 0; padding: 0; line-height: 1.0; }
.en-hero p { margin: 0 0 14px 0; font-size: 1.2rem; color: #D8F3DC; max-width: 36ch; }
.en-hero svg { animation: en-float 5s ease-in-out infinite; flex: none; }
@keyframes en-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-9px); } }
.en-sdg { display: inline-block; border-radius: 999px; padding: 4px 14px; font-weight: 700; font-size: 0.85rem; margin-right: 8px; color: #fff; }
.en-sdg.s4 { background: #C5192D; } .en-sdg.s13 { background: #3F7E44; }

/* page header */
.en-ph { display: flex; align-items: center; gap: 16px; margin: 6px 0 12px 0; }
.en-ph-num { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: 2.6rem; color: #b7e4c7; line-height: 1; }
.en-ph h1 { margin: 0; padding: 0; font-size: 2.1rem; }
.en-ph p { margin: 2px 0 0 0; color: #52796f; }

/* cards */
.en-card { background: #fff; border: 1px solid #cfe5d6; border-left: 6px solid #2D6A4F; border-radius: 16px; padding: 16px 22px; margin: 10px 0 6px 0; color: #1E293B; transition: box-shadow .15s ease, transform .15s ease; }
.en-card:hover { box-shadow: 0 10px 28px rgba(27,67,50,0.12); transform: translateY(-2px); }
.en-card h3 { margin: 0 0 6px 0; font-size: 1.25rem; }
.en-info { font-size: 1.05rem; line-height: 1.55; margin: 0 0 8px 0; max-width: 78ch; }
.en-source { font-size: 0.85rem; color: #475569; margin: 0; }
.en-tile { background: linear-gradient(160deg, #E4F7E8, #D8F3DC); border: 1px solid #bfe3c8; border-radius: 18px; padding: 16px 18px; min-height: 140px; color: #1E293B; transition: transform .15s ease, box-shadow .15s ease; }
.en-tile:hover { transform: translateY(-3px); box-shadow: 0 12px 26px rgba(27,67,50,0.14); }
.en-tile h4 { margin: 8px 0 4px 0; color: #1B4332; }
.en-tile p { margin: 0; font-size: 0.95rem; }
.en-badge { display: inline-block; background: #FFF3CD; color: #7a5200; border: 1px solid #f0c75e; border-radius: 999px; padding: 4px 14px; font-weight: 700; font-size: 0.9rem; margin-bottom: 8px; }
.en-badge.ok { background: #D8F3DC; color: #1B4332; border-color: #74c69d; }
.en-demo { background: #fff; border: 2px dashed #2D6A4F; border-radius: 16px; padding: 12px 16px; }
.en-demo table { width: 100%; border-collapse: collapse; }
.en-demo td { padding: 5px 2px; border-bottom: 1px solid #e2efe6; }
.en-demo td:last-child { text-align: right; font-weight: 700; color: #1B4332; }

/* rewards */
.en-rank { background: linear-gradient(120deg, #1B4332, #2D6A4F); color: #F8FAF9; border-radius: 20px; padding: 18px 24px; margin: 8px 0 12px 0; }
.en-rank b { font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.7rem; }
.en-rank span { color: #D8F3DC; }
.en-shelf { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; margin: 6px 0 14px 0; }
.en-medal { text-align: center; background: #fff; border: 1px solid #cfe5d6; border-radius: 16px; padding: 10px 6px 8px 6px; }
.en-medal.locked { opacity: 0.6; }
.en-medal div { font-weight: 700; font-size: 0.85rem; color: #1B4332; }
.en-medal small { color: #64748b; }
.en-xp { display: inline-block; background: #FFF3CD; color: #7a5200; border-radius: 999px; padding: 2px 10px; font-weight: 700; font-size: 0.8rem; }

/* metrics, expanders, tables */
[data-testid="stMetric"] { background: #fff; border: 1px solid #cfe5d6; border-radius: 14px; padding: 10px 14px; }
[data-testid="stExpander"] { border-radius: 14px; border-color: #cfe5d6; background: #fff; }
</style>
"""

# --------------------------------------------------------------------------- state & helpers
def init_state() -> None:
    st.session_state.setdefault("nav", NAV_HOME)
    st.session_state.setdefault("tips_done", set())
    st.session_state.setdefault("challenges_done", set())


def go_to(view: str) -> None:
    """Button callback: jump to a view (runs before the next render)."""
    st.session_state["nav"] = view


def go_to_explore_choice() -> None:
    st.session_state["nav"] = st.session_state["explore_choice"]


def total_xp() -> int:
    return len(st.session_state["tips_done"]) * XP_PER_TIP + len(st.session_state["challenges_done"]) * XP_PER_CHALLENGE


def rank_for(xp: int) -> tuple[str, tuple[int, str] | None]:
    """Return the current rank name and the next (threshold, name), or None at the top."""
    current = RANKS[0][1]
    for threshold, name in RANKS:
        if xp >= threshold:
            current = name
    upcoming = next(((t, n) for t, n in RANKS if t > xp), None)
    return current, upcoming


@st.cache_data(show_spinner=False)
def get_blocks() -> dict[int, ContentBlock]:
    return {block.id: block for block in load_content_blocks()}


def render_content_card(block: ContentBlock) -> None:
    """Show database text verbatim, its source, and a View Source button only for real URLs."""
    parts = [f'<div class="en-card"><h3>{esc(CARD_HEADINGS.get(block.id, ""))}</h3>']
    parts.append(f'<p class="en-info">{esc(block.information).replace(chr(10), "<br>")}</p>')
    if block.source:
        parts.append(f'<p class="en-source"><strong>Source:</strong> {esc(block.source)}</p>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
    if block.has_valid_link:
        st.link_button("View Source", block.link)


def icon_tile(icon: str, title: str, text: str) -> str:
    return f'<div class="en-tile">{icon_svg(icon)}<h4>{esc(title)}</h4><p>{esc(text)}</p></div>'


def page_header(number: str, title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="en-ph"><span class="en-ph-num">{esc(number)}</span><div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div></div>',
        unsafe_allow_html=True,
    )


def chip_html() -> str:
    name, _ = rank_for(total_xp())
    return f'<span class="en-chip">{icon_svg("sprout", 18)} {total_xp()} XP · {esc(name)}</span>'


def render_top_nav():
    """Sticky top bar: brand, pill navigation, eco-points chip and a Play now button."""
    with st.container(key="topnav"):
        c_brand, c_nav, c_chip, c_cta = st.columns([1.5, 5.4, 1.6, 1.2], vertical_alignment="center")
        c_brand.markdown(f'<div class="en-brand">{icon_svg("sprout", 34)}<div>EcoNova<small>Kipling Institute</small></div></div>', unsafe_allow_html=True)
        c_nav.radio("Navigate", NAV_ITEMS, key="nav", horizontal=True, label_visibility="collapsed")
        chip_slot = c_chip.empty()
        c_cta.button("Play now", key="cta_play", type="primary", on_click=go_to, args=(NAV_PLAY,))
    return chip_slot


# --------------------------------------------------------------------------- views
def view_home(blocks: dict[int, ContentBlock]) -> None:
    st.markdown(
        '<div class="en-hero"><div><h1>EcoNova</h1><p>A greener future starts with us — Kipling Institute · SDG 4 &amp; SDG 13</p>'
        '<span class="en-sdg s4">SDG 4 · Quality Education</span><span class="en-sdg s13">SDG 13 · Climate Action</span></div>'
        "<svg viewBox='0 0 120 120' width='132' height='132' aria-hidden='true'><circle cx='60' cy='60' r='54' fill='none' stroke='#74c69d' stroke-width='3' stroke-dasharray='4 6'/>"
        "<circle cx='60' cy='60' r='38' fill='#D8F3DC'/><path d='M60 98V56' stroke='#1B4332' stroke-width='5' stroke-linecap='round'/>"
        "<path d='M60 60C60 40 46 32 28 32c0 18 12 28 32 28z' fill='#2D6A4F'/><path d='M60 70c0-14 10-22 30-22 0 18-12 26-30 26z' fill='#40916c'/></svg></div>",
        unsafe_allow_html=True,
    )
    render_content_card(blocks[2])
    st.markdown("### Where would you like to start?")
    quick = [
        ("globe", "Understand the Impact", "See verified climate facts and explore interactive charts.", NAV_IMPACT),
        ("sprout", "Try a Green Action", "Build daily habits, complete six challenges and earn badges.", NAV_ACTIONS),
        ("gamepad", "Learn Through Play", "Play two games and test what you know.", NAV_PLAY),
    ]
    for col, (icon, title, text, target) in zip(st.columns(3), quick):
        with col:
            st.markdown(icon_tile(icon, title, text), unsafe_allow_html=True)
            st.button(title, key=f"quick_{target}", on_click=go_to, args=(target,))
    with st.expander("Explore Actions"):
        st.selectbox("Jump to a section", NAV_ITEMS[1:], key="explore_choice")
        st.button("Go to section", key="explore_go", on_click=go_to_explore_choice)


def view_impact(blocks: dict[int, ContentBlock]) -> None:
    page_header("02", "Eco Impact", "Verified climate facts and charts you can explore.")
    render_content_card(blocks[3])
    render_content_card(blocks[7])

    st.markdown("### Chart 1: Where excess global warming heat goes")
    st.markdown('<span class="en-badge ok">Verified split: Gapminder / UN SDG 13</span> <span class="en-badge">Projection: maths-based estimate</span>', unsafe_allow_html=True)
    c_year, c_scn = st.columns([3, 2])
    year = c_year.slider("Projection year", MIN_YEAR, MAX_YEAR, 2050, key="heat_year")
    scenario = c_scn.radio("Scenario", ["trend", "steady"], format_func=lambda k: SCENARIOS[k], key="heat_scenario")
    now = project(year, scenario)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Heat gained by {now.year}", f"{now.total_zj:,.0f} ZJ")
    m2.metric("Into the oceans (85%)", f"{now.ocean_zj:,.0f} ZJ")
    m3.metric("Air, land & ice (15%)", f"{now.other_zj:,.0f} ZJ")
    m4.metric("Same as world energy use for", f"{now.world_energy_years:,.0f} years")
    st.plotly_chart(build_heat_figure(year, scenario), config=PLOTLY_CONFIG, theme=None)
    st.caption(
        f"Likely range for {now.year}: {now.total_low_zj:,.0f} to {now.total_high_zj:,.0f} ZJ (the shaded band). "
        "The further ahead you look, the less certain the estimate. Drag on a chart to zoom, double-click to reset."
    )
    with st.expander("How is this predicted? (the maths and sources)"):
        st.markdown(
            "The yearly heat gain starts at a base rate and keeps speeding up, so the heat gained after *t* years is:"
        )
        st.latex(r"H(t) = R_0\,t + \tfrac{1}{2}\,a\,t^{2}")
        st.markdown(
            f"- **R₀ = {BASE_OCEAN_RATE_ZJ:.1f} ZJ per year** for the oceans: the average of 2024 ({OCEAN_GAIN_2024_ZJ:.0f} ZJ) and 2025 ({OCEAN_GAIN_2025_ZJ:.0f} ± 8 ZJ), "
            "so one unusual year does not decide the result.\n"
            "- **a = 0.32 ± 0.14 W/m² per decade**, the measured speed-up of ocean heating over 2005 to 2025. It is converted to ZJ with 1 W/m² over a year ≈ 16 ZJ, giving about 0.5 ZJ per year, every year.\n"
            "- **Steady rate** sets a = 0. **Current trend** uses the measured a. The shaded band uses the low and high ends of every input.\n"
            "- **Total heat = ocean heat ÷ 0.85**, because EcoNova's database says the oceans take roughly 85%. Recent studies say more than 90%, so treat the 15% share as approximate.\n"
            "- **World energy use** is about 0.62 ZJ per year (2023 level).\n\n"
            "This is a simple extrapolation, not a climate-model forecast. Cutting greenhouse-gas emissions would change the real result."
        )
        st.markdown(
            "Sources: [Pan, Cheng et al., Ocean Heat Content Sets Another Record in 2025 (NOAA repository)](https://repository.library.noaa.gov/view/noaa/73693) · "
            "[Eos: in 2025 the ocean stored more heat than ever recorded](https://eos.org/research-and-developments/in-2025-the-ocean-stored-more-heat-than-weve-ever-recorded) · "
            "[EurekAlert news release](https://www.eurekalert.org/news-releases/1111665)"
        )

    st.markdown("### Chart 2: Global climate cooperation (Paris Agreement)")
    st.markdown('<span class="en-badge ok">Verified global UN context</span>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    p1.metric("In the Paris Agreement", f"{PARIS_PARTIES} of {UNFCCC_PARTIES}")
    p2.metric("Signed, not ratified", PARIS_SIGNED_NOT_RATIFIED)
    p3.metric("Withdrew", PARIS_WITHDRAWN)
    st.plotly_chart(build_paris_figure(), config=PLOTLY_CONFIG, theme=None)
    st.caption(PARIS_SOURCE_NOTE + " Click a legend entry to hide or show a category. Hover a bar to see which countries it covers.")

    st.markdown("### Panel 3: Kipling Institute school survey dashboard")
    st.markdown('<span class="en-badge">Collection &amp; Validation Phase — Pending Review</span>', unsafe_allow_html=True)
    st.info("No survey results are shown yet. Results will appear here only after the data has been collected and validated.")
    for col, area in zip(st.columns(len(SURVEY_PLANNED_AREAS)), SURVEY_PLANNED_AREAS):
        col.metric(area, "Pending")
    st.plotly_chart(build_survey_placeholder_figure(), config=PLOTLY_CONFIG, theme=None)


def certificate_html(name: str) -> str:
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><title>EcoNova Eco Hero Certificate</title><style>"
        "body{margin:0;background:#F8FAF9;font-family:Georgia,'Times New Roman',serif;color:#1E293B}"
        ".c{max-width:900px;margin:30px auto;border:12px double #2D6A4F;background:#fff;padding:50px 60px;text-align:center}"
        "h1{font-size:44px;color:#1B4332;margin:0 0 6px}h2{font-size:34px;margin:18px 0;color:#2D6A4F;border-bottom:2px solid #b7e4c7;display:inline-block;padding:0 24px 6px}"
        "p{font-size:19px;line-height:1.5}.s{margin-top:34px;color:#52796f;font-size:15px}</style></head><body><div class='c'>"
        "<h1>Eco Hero Certificate</h1><p>EcoNova · Kipling Institute</p><p>This certificate is proudly awarded to</p>"
        f"<h2>{esc(name)}</h2><p>for completing all six Green Challenges and taking real action for<br>"
        "SDG 4 (Quality Education) and SDG 13 (Climate Action).</p>"
        f"<p class='s'>Awarded on {date.today():%d %B %Y}</p></div></body></html>"
    )


def render_rewards() -> None:
    """Rank card, badge shelf and certificate. Filled at the end of the run so it is never stale."""
    xp = total_xp()
    name, upcoming = rank_for(xp)
    done = st.session_state["challenges_done"]
    goal = f"Next rank: <b>{esc(upcoming[1])}</b> at {upcoming[0]} XP" if upcoming else "You reached the top rank!"
    st.markdown(
        f'<div class="en-rank"><span>Your rank</span><br><b>{esc(name)}</b> <span>· {xp} of {MAX_XP} XP</span><br><span>{goal}</span></div>',
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, xp / MAX_XP), text=f"{xp} / {MAX_XP} eco-points. Each tip is worth {XP_PER_TIP} XP, each challenge {XP_PER_CHALLENGE} XP.")
    medals = "".join(
        f'<div class="en-medal{"" if i in done else " locked"}">{badge_svg(icon, color, i in done)}<div>{esc(title)}</div>'
        f'<small>{"Unlocked" if i in done else "Locked"}</small></div>'
        for i, (title, icon, color, _steps) in enumerate(CHALLENGES)
    )
    st.markdown(f'<div class="en-shelf">{medals}</div>', unsafe_allow_html=True)
    if len(done) == len(CHALLENGES):
        st.success("All six badges unlocked! You are an Eco Hero. Add your name and download your certificate.")
        cert_name = st.text_input("Name on the certificate", key="cert_name", placeholder="Your name")
        st.download_button("Download your Eco Hero certificate", data=certificate_html(cert_name.strip() or "EcoNova Student").encode("utf-8"),
                           file_name="EcoNova_Eco_Hero_Certificate.html", mime="text/html")
    else:
        st.caption(f"Complete all {len(CHALLENGES)} challenges to unlock the Eco Hero certificate. {len(CHALLENGES) - len(done)} to go!")


def view_actions(blocks: dict[int, ContentBlock]) -> None:
    page_header("03", "Green Actions", "Build habits, finish challenges, earn badges.")
    render_content_card(blocks[4])
    rewards_slot = st.empty()
    xp_before_rank = rank_for(total_xp())[0]

    st.markdown("### Three core habits")
    for col, (icon, title, text) in zip(st.columns(3), CORE_HABITS):
        with col:
            st.markdown(icon_tile(icon, title, text), unsafe_allow_html=True)

    st.markdown("### Daily tips checklist")
    bar = st.empty()
    done_tips = st.session_state["tips_done"]
    for i, tip in enumerate(DAILY_TIPS):
        checked = st.checkbox(f"{tip}  (+{XP_PER_TIP} XP)", value=i in done_tips, key=f"tip_{i}")
        (done_tips.add if checked else done_tips.discard)(i)
    pct = round(len(done_tips) / len(DAILY_TIPS) * 100)
    bar.progress(pct / 100, text=f"{pct}% of today's tips completed")

    st.markdown("### Six green challenges")
    finished = st.session_state["challenges_done"]
    newly = []
    cols = st.columns(2)
    for i, (title, icon, color, steps) in enumerate(CHALLENGES):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px">{badge_svg(icon, color, i in finished)}'
                    f'<div><h4 style="margin:0">{esc(title)}</h4><span class="en-xp">+{XP_PER_CHALLENGE} XP and a badge</span></div></div>',
                    unsafe_allow_html=True,
                )
                with st.expander("Action guide"):
                    st.markdown("\n".join(f"{n}. {step}" for n, step in enumerate(steps, 1)))
                on = st.toggle("Mark Challenge Completed", value=i in finished, key=f"challenge_{i}")
                if on and i not in finished:
                    newly.append(title)
                (finished.add if on else finished.discard)(i)
    for title in newly:
        st.toast(f"Badge unlocked: {title}! +{XP_PER_CHALLENGE} XP", icon="🏅")
    if newly and len(finished) == len(CHALLENGES):
        st.balloons()
        st.toast("All six challenges done. You are an Eco Hero!", icon="🏆")
    new_rank = rank_for(total_xp())[0]
    if new_rank != xp_before_rank:
        st.toast(f"Rank up: {new_rank}!", icon="🌳")
    with rewards_slot.container():
        render_rewards()


def view_play(blocks: dict[int, ContentBlock]) -> None:
    page_header("04", "Eco-Play Zone", "Two games. Keyboard, mouse and touch all work.")
    render_content_card(blocks[5])
    game_a = "Game A: Eco-Runner (Trash Collect & Sort)"
    game_b = "Game B: Eco-School Quiz Quest"
    c_pick, c_big = st.columns([3, 1], vertical_alignment="center")
    choice = c_pick.radio("Choose a game", [game_a, game_b], horizontal=True, key="game_choice", label_visibility="collapsed")
    large = c_big.toggle("Large screen mode", key="play_large", help="Makes the game window taller. Inside the game, the Fullscreen button fills your whole screen.")
    page = get_trash_platformer_html() if choice == game_a else get_eco_school_quest_html()
    height = 820 if large else 620

    def leaderboard() -> None:
        rows = "".join(f"<tr><td>{i}. {esc(name)}</td><td>{score}</td></tr>" for i, (name, score) in enumerate(DEMO_LEADERBOARD, 1))
        st.markdown(f'<div class="en-demo"><h3 style="margin-top:0">Top Eco-Friends (Demo Example)</h3><table>{rows}</table></div>', unsafe_allow_html=True)
        st.caption("Visual example — placeholder names until live student scores are connected")

    if large:
        components.html(page, height=height)
        leaderboard()
    else:
        game_col, board_col = st.columns([3, 1])
        with game_col:
            components.html(page, height=height)
        with board_col:
            leaderboard()
    st.caption("Click inside the game once so it can read your keyboard. On phones and tablets, use the on-screen buttons. "
               "If Fullscreen is missing on your device, turn on Large screen mode.")


def view_about(blocks: dict[int, ContentBlock]) -> None:
    page_header("05", "About Us", "The students behind EcoNova.")
    render_content_card(blocks[6])
    st.markdown("### Student teams")
    for col, (team, role) in zip(st.columns(4), TEAMS):
        with col:
            st.markdown(f'<div class="en-tile"><h4>{esc(team)}</h4><p>{esc(role)}</p></div>', unsafe_allow_html=True)

    st.markdown("### Share your feedback")
    with st.form("feedback_form"):
        name = st.text_input("Student/Teacher name (optional)", placeholder="Anonymous")
        visited = st.radio("Have you visited EcoNova before?", ["Yes", "No"], index=1, horizontal=True)
        message = st.text_area(
            "What did you learn about SDG 4 & SDG 13, what climate habit will you adopt, and how can we improve EcoNova?",
            height=160,
        )
        rating = st.select_slider("Platform usefulness rating", options=[1, 2, 3, 4, 5], value=4, format_func=lambda n: "★" * n)
        submitted = st.form_submit_button("Send feedback")
    if submitted:
        if not message.strip():
            st.error("Please answer the question about what you learned, your climate habit, and how we can improve.")
            return
        result = submit_feedback(FeedbackSubmission(message=message, visited_before=visited, rating=rating, name=name or "Anonymous"))
        (st.success if result.emailed else st.warning)(result.message)


VIEWS = {NAV_HOME: view_home, NAV_IMPACT: view_impact, NAV_ACTIONS: view_actions, NAV_PLAY: view_play, NAV_ABOUT: view_about}


def main() -> None:
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    chip_slot = render_top_nav()

    try:
        blocks = get_blocks()
    except ContentLoadError as exc:
        st.error(f"The content database could not be loaded: {exc}")
        st.stop()
    missing = missing_required_ids(list(blocks.values()))
    if missing:
        st.error(f"The content database is missing required rows: {missing}")
        st.stop()

    VIEWS[st.session_state["nav"]](blocks)
    chip_slot.markdown(chip_html(), unsafe_allow_html=True)  # filled last so it never lags behind


main()
