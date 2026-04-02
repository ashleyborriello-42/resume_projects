import streamlit as st
from groq import Groq
import json
import os
import requests
from dotenv import load_dotenv
import folium
from streamlit_folium import st_folium
from fpdf import FPDF
import io

load_dotenv()

client = Groq(api_key=os.getenv("API_KEY"))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TrailPlan",
    page_icon="🏔️",
    layout="wide"
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');

.big-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 72px;
    line-height: 0.9;
    color: #e8ede4;
    margin-bottom: 4px;
}
.big-title span { color: #7ec850; }

.tagline {
    font-family: 'Lora', serif;
    font-style: italic;
    color: #6a856b;
    font-size: 15px;
    margin-bottom: 24px;
}

.map-instruction {
    background: #131f14;
    border-left: 3px solid #7ec850;
    padding: 12px 18px;
    font-size: 13px;
    color: #6a856b;
    margin-bottom: 16px;
    font-family: 'Lora', serif;
    font-style: italic;
}

.selected-park-banner {
    background: linear-gradient(135deg, #192b1a, #1f3820);
    border: 1px solid #2a3d2b;
    border-left: 4px solid #7ec850;
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.section-head {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 28px;
    letter-spacing: 0.05em;
    color: #e8ede4;
    border-bottom: 1px solid #2a3d2b;
    padding-bottom: 8px;
    margin: 32px 0 16px;
}

.overview-box {
    background: #131f14;
    border-left: 3px solid #7ec850;
    padding: 16px 20px;
    font-family: 'Lora', serif;
    font-size: 15px;
    line-height: 1.75;
    color: rgba(232,237,228,0.85);
    margin-bottom: 24px;
}

.day-header {
    background: #192b1a;
    border: 1px solid #2a3d2b;
    border-left: 3px solid #e8b84b;
    padding: 12px 18px;
    margin-bottom: 0;
}

.day-num {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 28px;
    color: #e8b84b;
    line-height: 1;
}

.day-theme {
    font-family: 'Lora', serif;
    font-style: italic;
    color: #6a856b;
    font-size: 14px;
}

.trail-card {
    background: #131f14;
    border: 1px solid #2a3d2b;
    border-top: none;
    padding: 20px;
    margin-bottom: 0;
}

.trail-name {
    font-size: 17px;
    font-weight: 600;
    color: #e8ede4;
    margin-bottom: 8px;
}

.badge-easy     { background: rgba(126,200,80,0.15); color: #7ec850; padding: 3px 10px; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; }
.badge-moderate { background: rgba(232,184,75,0.15); color: #e8b84b; padding: 3px 10px; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; }
.badge-hard     { background: rgba(232,113,75,0.15); color: #e8714b; padding: 3px 10px; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; }
.badge-strenuous{ background: rgba(232,75,75,0.15);  color: #e84b4b; padding: 3px 10px; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; }

.stat-row {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin: 8px 0;
    font-size: 13px;
    color: #6a856b;
}

.parking-note {
    background: rgba(232,184,75,0.08);
    border-left: 2px solid #e8b84b;
    padding: 6px 12px;
    font-size: 12px;
    color: #e8b84b;
    margin: 10px 0;
}

.day-notes {
    font-family: 'Lora', serif;
    font-style: italic;
    font-size: 13px;
    color: #6a856b;
    border-top: 1px dashed #2a3d2b;
    padding-top: 12px;
    margin-top: 12px;
}

.tip-card {
    background: #131f14;
    border: 1px solid #2a3d2b;
    padding: 16px;
    height: 100%;
}

.tip-title {
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #e8b84b;
    margin: 6px 0;
}

.tip-text {
    font-size: 12px;
    color: #6a856b;
    line-height: 1.6;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Park photos ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_park_photo_urls(park_name: str) -> list[str]:
    try:
        slug = park_name.replace(" ", "_") + "_National_Park"
        headers = {"User-Agent": "TrailPlanApp/1.0"}
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}",
            headers=headers, timeout=8
        )
        data = r.json()
        thumb = data.get("thumbnail", {}).get("source", "")
        original = data.get("originalimage", {}).get("source", "")
        commons_r = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrnamespace": 6,
                "gsrsearch": f"{park_name} National Park",
                "gsrlimit": 10,
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": 600,
                "format": "json"
            },
            headers=headers, timeout=8
        )
        commons_data = commons_r.json()
        pages = commons_data.get("query", {}).get("pages", {}).values()
        commons_urls = []
        for page in pages:
            info = page.get("imageinfo", [])
            if info:
                url = info[0].get("thumburl") or info[0].get("url", "")
                title = page.get("title", "").lower()
                if url and any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                    if not any(skip in title for skip in ["map", "logo", "seal", "flag", "icon"]):
                        commons_urls.append(url)
        results = []
        if original:
            results.append(original)
        elif thumb:
            results.append(thumb)
        results.extend(commons_urls)
        seen = set()
        unique = [u for u in results if not (u in seen or seen.add(u))]
        return unique[:3] if len(unique) >= 3 else unique
    except Exception:
        return []


# ── PDF Generator ─────────────────────────────────────────────────────────────
def generate_pdf(result, meta) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, result["park_name"], ln=True)

    # Trip meta
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"{meta['days']} days  |  {meta['month']}  |  {meta['experience']}  |  Max {meta['max_miles']} mi/day  |  {meta['group']}", ln=True)
    pdf.ln(4)

    # Divider
    pdf.set_draw_color(126, 200, 80)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Overview
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, "Overview", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, result["overview"])
    pdf.ln(6)

    # Days
    for day in result["days"]:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 30, 30)
        pdf.set_fill_color(240, 248, 235)
        pdf.cell(0, 8, f"Day {day['day']}  —  {day['theme']}", ln=True, fill=True)
        pdf.ln(2)

        for trail in day["trails"]:
            # Trail name + difficulty
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(140, 6, trail["name"], ln=False)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, f"[{trail['difficulty']}]", ln=True)

            # Stats
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 5,
                f"{trail['distance_miles']} mi  |  {trail['elevation_gain_ft']:,} ft gain  |  ~{trail['estimated_hours']}h",
                ln=True)

            # Description
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 5, trail["description"])

            # Parking
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(150, 120, 30)
            pdf.multi_cell(0, 5, f"Parking: {trail['parking']}")
            pdf.ln(3)

        # Day notes
        if day.get("day_notes"):
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 5, f"Note: {day['day_notes']}")

        pdf.ln(5)

    # Tips
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Essential Tips", ln=True)
    pdf.ln(2)

    for tip in result.get("tips", []):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 5, f"{tip['title']}", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5, tip["text"])
        pdf.ln(3)

    # Footer
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "Generated by TrailPlan — trailplan.streamlit.app", align="C")

    return bytes(pdf.output())


# ── Park data ─────────────────────────────────────────────────────────────────
PARKS = {
    "Acadia":                       {"lat": 44.35,  "lon": -68.21,  "state": "ME"},
    "American Samoa":               {"lat": -14.25, "lon": -170.68, "state": "AS"},
    "Arches":                       {"lat": 38.68,  "lon": -109.57, "state": "UT"},
    "Badlands":                     {"lat": 43.85,  "lon": -102.34, "state": "SD"},
    "Big Bend":                     {"lat": 29.25,  "lon": -103.25, "state": "TX"},
    "Biscayne":                     {"lat": 25.48,  "lon": -80.43,  "state": "FL"},
    "Black Canyon of the Gunnison": {"lat": 38.57,  "lon": -107.72, "state": "CO"},
    "Bryce Canyon":                 {"lat": 37.59,  "lon": -112.18, "state": "UT"},
    "Canyonlands":                  {"lat": 38.20,  "lon": -109.93, "state": "UT"},
    "Capitol Reef":                 {"lat": 38.20,  "lon": -111.17, "state": "UT"},
    "Carlsbad Caverns":             {"lat": 32.17,  "lon": -104.44, "state": "NM"},
    "Channel Islands":              {"lat": 34.01,  "lon": -119.42, "state": "CA"},
    "Congaree":                     {"lat": 33.78,  "lon": -80.78,  "state": "SC"},
    "Crater Lake":                  {"lat": 42.94,  "lon": -122.10, "state": "OR"},
    "Cuyahoga Valley":              {"lat": 41.24,  "lon": -81.55,  "state": "OH"},
    "Death Valley":                 {"lat": 36.51,  "lon": -117.08, "state": "CA"},
    "Denali":                       {"lat": 63.33,  "lon": -150.50, "state": "AK"},
    "Dry Tortugas":                 {"lat": 24.63,  "lon": -82.87,  "state": "FL"},
    "Everglades":                   {"lat": 25.39,  "lon": -80.93,  "state": "FL"},
    "Gates of the Arctic":          {"lat": 67.78,  "lon": -153.30, "state": "AK"},
    "Gateway Arch":                 {"lat": 38.62,  "lon": -90.19,  "state": "MO"},
    "Glacier":                      {"lat": 48.69,  "lon": -113.72, "state": "MT"},
    "Glacier Bay":                  {"lat": 58.50,  "lon": -137.00, "state": "AK"},
    "Grand Canyon":                 {"lat": 36.10,  "lon": -112.11, "state": "AZ"},
    "Grand Teton":                  {"lat": 43.73,  "lon": -110.80, "state": "WY"},
    "Great Basin":                  {"lat": 38.98,  "lon": -114.30, "state": "NV"},
    "Great Sand Dunes":             {"lat": 37.73,  "lon": -105.51, "state": "CO"},
    "Great Smoky Mountains":        {"lat": 35.61,  "lon": -83.53,  "state": "TN"},
    "Guadalupe Mountains":          {"lat": 31.92,  "lon": -104.87, "state": "TX"},
    "Haleakala":                    {"lat": 20.72,  "lon": -156.17, "state": "HI"},
    "Hawaii Volcanoes":             {"lat": 19.42,  "lon": -155.29, "state": "HI"},
    "Hot Springs":                  {"lat": 34.51,  "lon": -93.05,  "state": "AR"},
    "Indiana Dunes":                {"lat": 41.65,  "lon": -87.05,  "state": "IN"},
    "Isle Royale":                  {"lat": 48.00,  "lon": -88.83,  "state": "MI"},
    "Joshua Tree":                  {"lat": 33.88,  "lon": -115.90, "state": "CA"},
    "Katmai":                       {"lat": 58.50,  "lon": -154.00, "state": "AK"},
    "Kenai Fjords":                 {"lat": 59.92,  "lon": -149.65, "state": "AK"},
    "Kings Canyon":                 {"lat": 36.89,  "lon": -118.55, "state": "CA"},
    "Kobuk Valley":                 {"lat": 67.55,  "lon": -159.28, "state": "AK"},
    "Lake Clark":                   {"lat": 60.97,  "lon": -153.42, "state": "AK"},
    "Lassen Volcanic":              {"lat": 40.49,  "lon": -121.51, "state": "CA"},
    "Mammoth Cave":                 {"lat": 37.19,  "lon": -86.10,  "state": "KY"},
    "Mesa Verde":                   {"lat": 37.18,  "lon": -108.49, "state": "CO"},
    "Mount Rainier":                {"lat": 46.85,  "lon": -121.75, "state": "WA"},
    "New River Gorge":              {"lat": 37.87,  "lon": -81.08,  "state": "WV"},
    "North Cascades":               {"lat": 48.70,  "lon": -121.20, "state": "WA"},
    "Olympic":                      {"lat": 47.97,  "lon": -123.50, "state": "WA"},
    "Petrified Forest":             {"lat": 35.07,  "lon": -109.78, "state": "AZ"},
    "Pinnacles":                    {"lat": 36.49,  "lon": -121.20, "state": "CA"},
    "Redwood":                      {"lat": 41.30,  "lon": -124.00, "state": "CA"},
    "Rocky Mountain":               {"lat": 40.40,  "lon": -105.58, "state": "CO"},
    "Saguaro":                      {"lat": 32.25,  "lon": -110.50, "state": "AZ"},
    "Sequoia":                      {"lat": 36.43,  "lon": -118.68, "state": "CA"},
    "Shenandoah":                   {"lat": 38.49,  "lon": -78.35,  "state": "VA"},
    "Theodore Roosevelt":           {"lat": 46.97,  "lon": -103.45, "state": "ND"},
    "Virgin Islands":               {"lat": 18.33,  "lon": -64.73,  "state": "VI"},
    "Voyageurs":                    {"lat": 48.48,  "lon": -92.83,  "state": "MN"},
    "White Sands":                  {"lat": 32.78,  "lon": -106.17, "state": "NM"},
    "Wind Cave":                    {"lat": 43.57,  "lon": -103.48, "state": "SD"},
    "Wrangell-St. Elias":          {"lat": 61.00,  "lon": -142.00, "state": "AK"},
    "Yellowstone":                  {"lat": 44.43,  "lon": -110.59, "state": "WY"},
    "Yosemite":                     {"lat": 37.87,  "lon": -119.54, "state": "CA"},
    "Zion":                         {"lat": 37.30,  "lon": -113.05, "state": "UT"},
}

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

INTERESTS = [
    "Waterfalls", "Summit views", "Wildlife", "Photography spots",
    "Swimming holes", "Solitude / fewer crowds", "Iconic landmarks",
    "Geology / rock formations"
]

# ── Session state ─────────────────────────────────────────────────────────────
if "selected_park" not in st.session_state:
    st.session_state.selected_park = None
if "itinerary" not in st.session_state:
    st.session_state.itinerary = None
if "last_generated" not in st.session_state:
    st.session_state.last_generated = None

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="big-title">TRAIL<span>PLAN</span></div>
<div class="tagline">Click any park on the map to begin planning your trip.</div>
""", unsafe_allow_html=True)

st.divider()

# ── Layout ────────────────────────────────────────────────────────────────────
map_col, settings_col = st.columns([2, 1])

with map_col:
    selected = st.session_state.selected_park
    st.markdown('<div class="map-instruction">🗺️ Click a green dot to select a national park</div>', unsafe_allow_html=True)

    m = folium.Map(location=[39.5, -98.35], zoom_start=4, tiles="CartoDB dark_matter", prefer_canvas=True)

    for park_name, info in PARKS.items():
        is_selected = park_name == selected
        folium.CircleMarker(
            location=[info["lat"], info["lon"]],
            radius=10 if is_selected else 7,
            color="#7ec850" if is_selected else "#4a7a30",
            fill=True,
            fill_color="#7ec850" if is_selected else "#2a4a1a",
            fill_opacity=1.0 if is_selected else 0.7,
            weight=3 if is_selected else 1,
            tooltip=folium.Tooltip(
                f"<b style='font-family:sans-serif;color:#e8ede4'>{park_name}</b>",
                style="background:#131f14;border:1px solid #2a3d2b;color:#e8ede4;"
            ),
            popup=folium.Popup(park_name, max_width=200)
        ).add_to(m)

        if is_selected:
            folium.CircleMarker(
                location=[info["lat"], info["lon"]],
                radius=18, color="#7ec850", fill=False, weight=2, opacity=0.5,
            ).add_to(m)

    map_data = st_folium(m, width="100%", height=420, returned_objects=["last_object_clicked_popup"])

    if map_data and map_data.get("last_object_clicked_popup"):
        clicked = map_data["last_object_clicked_popup"]
        if clicked and clicked in PARKS:
            if clicked != st.session_state.selected_park:
                st.session_state.selected_park = clicked
                st.session_state.itinerary = None
                st.rerun()

    # Photos
    if st.session_state.selected_park:
        park = st.session_state.selected_park
        st.markdown(f"""
        <div style="font-size:10px;letter-spacing:0.16em;text-transform:uppercase;
                    color:#6a856b;margin:16px 0 10px">
            📸 {park} National Park
        </div>
        """, unsafe_allow_html=True)

        photos = get_park_photo_urls(park)
        if photos:
            cols = st.columns(len(photos))
            for i, url in enumerate(photos):
                with cols[i]:
                    st.markdown(f"""
                    <div style="height:240px;overflow:hidden;border:1px solid #2a3d2b">
                        <img src="{url}" style="width:100%;height:100%;object-fit:cover;display:block"/>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="color:#6a856b;font-size:12px;font-style:italic;padding:8px 0">
                Photos unavailable for this park.
            </div>
            """, unsafe_allow_html=True)

with settings_col:
    st.markdown("### ⚙️ Trip Settings")

    if st.session_state.selected_park:
        st.markdown(f"""
        <div class="selected-park-banner">
            <div>
                <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:#6a856b">Selected Park</div>
                <div style="font-family:'Bebas Neue',sans-serif;font-size:24px;color:#7ec850">{st.session_state.selected_park}</div>
                <div style="font-size:11px;color:#6a856b">{PARKS[st.session_state.selected_park]['state']}</div>
            </div>
            <div style="font-size:32px">🏔️</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👆 Click a park on the map first")

    days = st.number_input("Number of Days", min_value=1, max_value=14, value=3)
    month = st.selectbox("Visit Month", MONTHS, index=6)
    experience = st.selectbox(
        "Hiking Experience",
        ["Beginner", "Intermediate", "Advanced", "Expert"],
        index=1
    )
    max_miles = st.slider("Max Miles Per Day", min_value=2, max_value=20, value=8)
    group = st.selectbox(
        "Group Type",
        ["Solo", "Couple", "Small group (3-5)", "Family with kids", "Large group (6+)"]
    )
    interests = st.multiselect(
        "Interests",
        INTERESTS,
        default=["Waterfalls", "Photography spots", "Summit views"]
    )

    st.divider()
    build_btn = st.button(
        "→ Build My Itinerary",
        use_container_width=True,
        type="primary",
        disabled=not st.session_state.selected_park
    )


# ── Helper ────────────────────────────────────────────────────────────────────
def diff_badge(difficulty: str) -> str:
    cls = difficulty.lower().replace(" ", "-")
    return f'<span class="badge-{cls}">{difficulty}</span>'


# ── Build itinerary ───────────────────────────────────────────────────────────
def build_itinerary(park, days, experience, max_miles, month, group, interests):
    interests_str = ", ".join(interests) if interests else "general sightseeing"

    prompt = f"""You are an expert national park hiking guide with deep knowledge of all US national parks, their trails, parking areas, and logistics.

Build a detailed hiking itinerary for:
- Park: {park} National Park
- Duration: {days} days
- Hiking experience: {experience}
- Max miles per day: {max_miles} miles
- Visit month: {month}
- Group: {group}
- Interests: {interests_str}

Respond ONLY with valid JSON, no markdown, no backticks, no preamble. Use this exact structure:

{{
  "park_name": "{park} National Park",
  "overview": "3-4 sentence description of this park and what makes it special for this trip. Mention seasonal conditions for {month}.",
  "days": [
    {{
      "day": 1,
      "theme": "short evocative theme e.g. 'Valley Floor & Waterfalls'",
      "trails": [
        {{
          "name": "Trail Name",
          "difficulty": "Easy|Moderate|Hard|Strenuous",
          "distance_miles": 4.2,
          "elevation_gain_ft": 800,
          "estimated_hours": 3,
          "description": "2-3 sentences on what makes this trail special, what you'll see, best time of day",
          "parking": "Specific trailhead parking area name and any tips (arrive early, shuttle info, cost etc)",
          "youtube_search": "YouTube search query to find a trail video e.g. 'Yosemite Upper Yosemite Falls hike 4K'",
          "highlights": ["highlight 1", "highlight 2", "highlight 3"]
        }}
      ],
      "day_notes": "1-2 sentences on pacing, logistics, or tips for the day"
    }}
  ],
  "tips": [
    {{"icon": "🅿️", "title": "Parking", "text": "Park-specific parking advice"}},
    {{"icon": "🌤️", "title": "Weather in {month}", "text": "What to expect weather-wise"}},
    {{"icon": "🐻", "title": "Wildlife", "text": "Wildlife you might see and safety tips"}},
    {{"icon": "💧", "title": "Water & Food", "text": "Water sources, food storage, nearest towns"}},
    {{"icon": "📱", "title": "Cell Service", "text": "Connectivity and offline map tips"}},
    {{"icon": "🎟️", "title": "Permits & Passes", "text": "Entry fees, timed permits, reservations"}}
  ]
}}

Include 1-3 trails per day, keeping total daily mileage under {max_miles} miles.
Match difficulty to {experience} experience level.
Be specific about parking — name the actual trailhead lots at {park}.
Be accurate about real trails that exist at {park}."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
        temperature=0.7
    )

    raw = response.choices[0].message.content
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)


# ── Render itinerary ──────────────────────────────────────────────────────────
def render_itinerary(result, days, experience, max_miles, month, group):
    st.divider()

    st.markdown(f"""
    <div class="big-title" style="font-size:48px">{result['park_name']}</div>
    """, unsafe_allow_html=True)

    meta_cols = st.columns(5)
    meta_cols[0].metric("Days", f"{days} 📅")
    meta_cols[1].metric("Experience", experience)
    meta_cols[2].metric("Max Miles/Day", f"{max_miles} mi")
    meta_cols[3].metric("Month", month)
    meta_cols[4].metric("Group", group)

    st.markdown(f'<div class="overview-box">{result["overview"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-head">Day-by-Day Itinerary</div>', unsafe_allow_html=True)

    for day in result["days"]:
        st.markdown(f"""
        <div class="day-header">
            <div class="day-num">Day {day['day']}</div>
            <div class="day-theme">{day['theme']}</div>
        </div>
        """, unsafe_allow_html=True)

        for trail in day["trails"]:
            trail_name_encoded = trail['name'].replace(' ', '+')
            park_encoded = st.session_state.selected_park.replace(' ', '+')
            google_url = f"https://www.google.com/search?q={trail_name_encoded}+{park_encoded}+alltrails"
            highlights = " &nbsp;·&nbsp; ".join(trail.get("highlights", []))

            st.markdown(f"""
            <div class="trail-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start">
                    <div class="trail-name">{trail['name']}</div>
                    {diff_badge(trail['difficulty'])}
                </div>
                <div class="stat-row">
                    <span>📏 <strong style="color:#e8ede4">{trail['distance_miles']} mi</strong></span>
                    <span>⬆️ <strong style="color:#e8ede4">{trail['elevation_gain_ft']:,} ft gain</strong></span>
                    <span>⏱️ <strong style="color:#e8ede4">~{trail['estimated_hours']}h</strong></span>
                </div>
                {f'<div style="font-size:12px;color:#6a856b;margin-bottom:8px">✦ {highlights}</div>' if highlights else ''}
                <div style="font-size:13px;color:#6a856b;line-height:1.6;margin-bottom:10px">{trail['description']}</div>
                <div class="parking-note">🅿️ {trail['parking']}</div>
                <a href="{google_url}" target="_blank" style="font-size:12px;color:#7ec850;text-decoration:none;border:1px solid rgba(126,200,80,0.3);padding:4px 12px;display:inline-block;margin-top:4px">🌿 Find on AllTrails</a>
            </div>
            """, unsafe_allow_html=True)

        if day.get("day_notes"):
            st.markdown(f'<div class="day-notes">📝 {day["day_notes"]}</div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom:24px'></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-head">Essential Tips</div>', unsafe_allow_html=True)

    tips = result.get("tips", [])
    cols = st.columns(3)
    for i, tip in enumerate(tips):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="tip-card">
                <div style="font-size:22px">{tip['icon']}</div>
                <div class="tip-title">{tip['title']}</div>
                <div class="tip-text">{tip['text']}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)

    # ── PDF Export ────────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:32px'></div>", unsafe_allow_html=True)
    st.divider()

    meta = st.session_state.last_generated
    pdf_bytes = generate_pdf(result, meta)
    filename = f"{result['park_name'].replace(' ', '_')}_Itinerary.pdf"

    st.download_button(
        label="⬇️ Download Itinerary as PDF",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        use_container_width=True
    )

    if st.button("← Plan Another Trip", key="reset_btn"):
        st.session_state.selected_park = None
        st.session_state.itinerary = None
        st.rerun()


# ── Main logic ────────────────────────────────────────────────────────────────
if build_btn and st.session_state.selected_park:
    with st.spinner(f"Scouting trails in {st.session_state.selected_park}..."):
        try:
            result = build_itinerary(
                st.session_state.selected_park,
                days, experience, max_miles, month, group, interests
            )
            st.session_state.itinerary = result
            st.session_state.last_generated = {
                "days": days, "experience": experience,
                "max_miles": max_miles, "month": month, "group": group
            }
        except json.JSONDecodeError:
            st.error("Couldn't parse the response. Try again.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

if st.session_state.itinerary:
    meta = st.session_state.last_generated
    render_itinerary(
        st.session_state.itinerary,
        meta["days"], meta["experience"],
        meta["max_miles"], meta["month"], meta["group"]
    )
