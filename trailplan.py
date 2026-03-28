import streamlit as st
from groq import Groq
import json
import os
import requests
from dotenv import load_dotenv
import folium
from streamlit_folium import st_folium

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

# ── Fetch park photos ─────────────────────────────────────────────────────────
# Hardcoded Wikimedia Commons direct URLs — reliable, no API calls needed
PARK_PHOTOS_UNUSED = {
    "Acadia":                       [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Bass_Harbor_Head_Light_Station_2016.jpg/800px-Bass_Harbor_Head_Light_Station_2016.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Jordan_Pond%2C_Acadia_National_Park.jpg/800px-Jordan_Pond%2C_Acadia_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Acadia_National_Park_-_Thunder_Hole.jpg/800px-Acadia_National_Park_-_Thunder_Hole.jpg",
    ],
    "American Samoa":               [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/National_Park_of_American_Samoa.jpg/800px-National_Park_of_American_Samoa.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Ofu_Beach_American_Samoa.jpg/800px-Ofu_Beach_American_Samoa.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/American_Samoa_tropical_forest.jpg/800px-American_Samoa_tropical_forest.jpg",
    ],
    "Arches":                       [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Delicate_Arch_LaSals_crop.jpg/800px-Delicate_Arch_LaSals_crop.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Landscape_arch_2011.jpg/800px-Landscape_arch_2011.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Arches_National_Park_April_2015.jpg/800px-Arches_National_Park_April_2015.jpg",
    ],
    "Badlands":                     [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Badlands_National_Park_1.jpg/800px-Badlands_National_Park_1.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Badlands_National_Park_2.jpg/800px-Badlands_National_Park_2.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Badlands_National_Park_prairie.jpg/800px-Badlands_National_Park_prairie.jpg",
    ],
    "Big Bend":                     [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Santa_Elena_Canyon_Big_Bend.jpg/800px-Santa_Elena_Canyon_Big_Bend.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Big_Bend_National_Park_Chisos_Mountains.jpg/800px-Big_Bend_National_Park_Chisos_Mountains.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Big_Bend_NP_Rio_Grande.jpg/800px-Big_Bend_NP_Rio_Grande.jpg",
    ],
    "Biscayne":                     [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/Biscayne_NP_snorkeling.jpg/800px-Biscayne_NP_snorkeling.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Biscayne_National_Park_aerial.jpg/800px-Biscayne_National_Park_aerial.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Biscayne_NP_coral_reef.jpg/800px-Biscayne_NP_coral_reef.jpg",
    ],
    "Black Canyon of the Gunnison": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Gunnison_River_from_Chasm_View.jpg/800px-Gunnison_River_from_Chasm_View.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Black_Canyon_of_the_Gunnison_NP.jpg/800px-Black_Canyon_of_the_Gunnison_NP.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Black_Canyon_Gunnison_view.jpg/800px-Black_Canyon_Gunnison_view.jpg",
    ],
    "Bryce Canyon":                 [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Bryce_Canyon_hoodoos_Amphitheater.jpg/800px-Bryce_Canyon_hoodoos_Amphitheater.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Inspiration_Point_Bryce_Canyon_November_2018.jpg/800px-Inspiration_Point_Bryce_Canyon_November_2018.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Bryce_Canyon_Thor%27s_Hammer.jpg/800px-Bryce_Canyon_Thor%27s_Hammer.jpg",
    ],
    "Canyonlands":                  [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Canyonlands_National_Park%E2%80%A6Needles_area_%28byNPS%29.jpg/800px-Canyonlands_National_Park%E2%80%A6Needles_area_%28byNPS%29.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Canyonlands_National_Park_1.jpg/800px-Canyonlands_National_Park_1.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Mesa_Arch_Canyonlands.jpg/800px-Mesa_Arch_Canyonlands.jpg",
    ],
    "Capitol Reef":                 [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Capitol_Reef_National_Park.jpg/800px-Capitol_Reef_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Hickman_Bridge_Capitol_Reef.jpg/800px-Hickman_Bridge_Capitol_Reef.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Capitol_Reef_Waterpocket_Fold.jpg/800px-Capitol_Reef_Waterpocket_Fold.jpg",
    ],
    "Carlsbad Caverns":             [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Carlsbad_Caverns_%285%29.jpg/800px-Carlsbad_Caverns_%285%29.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Carlsbad_Caverns_Big_Room.jpg/800px-Carlsbad_Caverns_Big_Room.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Carlsbad_Caverns_National_Park_entrance.jpg/800px-Carlsbad_Caverns_National_Park_entrance.jpg",
    ],
    "Channel Islands":              [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Santa_Cruz_Island_Channel_Islands.jpg/800px-Santa_Cruz_Island_Channel_Islands.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Channel_Islands_National_Park.jpg/800px-Channel_Islands_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Anacapa_Island_Channel_Islands.jpg/800px-Anacapa_Island_Channel_Islands.jpg",
    ],
    "Congaree":                     [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Congaree_National_Park_SC.jpg/800px-Congaree_National_Park_SC.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Congaree_NP_boardwalk.jpg/800px-Congaree_NP_boardwalk.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Congaree_River_floodplain.jpg/800px-Congaree_River_floodplain.jpg",
    ],
    "Crater Lake":                  [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Crater_lake_oregon.jpg/800px-Crater_lake_oregon.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Crater_Lake_winter.jpg/800px-Crater_Lake_winter.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Crater_Lake_Wizard_Island.jpg/800px-Crater_Lake_Wizard_Island.jpg",
    ],
    "Cuyahoga Valley":              [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Cuyahoga_Valley_National_Park.jpg/800px-Cuyahoga_Valley_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Brandywine_Falls_Cuyahoga.jpg/800px-Brandywine_Falls_Cuyahoga.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Cuyahoga_Valley_NP_canal.jpg/800px-Cuyahoga_Valley_NP_canal.jpg",
    ],
    "Death Valley":                 [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Sand_Dunes_in_Death_Valley_National_Park.jpg/800px-Sand_Dunes_in_Death_Valley_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Badwater_Basin_Death_Valley.jpg/800px-Badwater_Basin_Death_Valley.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Death_Valley_Zabriskie_Point.jpg/800px-Death_Valley_Zabriskie_Point.jpg",
    ],
    "Denali":                       [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Denali_National_Park_and_Preserve.jpg/800px-Denali_National_Park_and_Preserve.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Mount_McKinley_and_Reflection_Pond.jpg/800px-Mount_McKinley_and_Reflection_Pond.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Denali_from_Stony_Hill.jpg/800px-Denali_from_Stony_Hill.jpg",
    ],
    "Dry Tortugas":                 [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Dry_Tortugas_National_Park.jpg/800px-Dry_Tortugas_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Fort_Jefferson_Dry_Tortugas.jpg/800px-Fort_Jefferson_Dry_Tortugas.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Dry_Tortugas_aerial.jpg/800px-Dry_Tortugas_aerial.jpg",
    ],
    "Everglades":                   [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Everglades_National_Park_by_Sentinel-2.jpg/800px-Everglades_National_Park_by_Sentinel-2.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Everglades_anhinga_trail.jpg/800px-Everglades_anhinga_trail.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Florida_Everglades_airboat.jpg/800px-Florida_Everglades_airboat.jpg",
    ],
    "Gates of the Arctic":          [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Gates_of_the_Arctic_National_Park.jpg/800px-Gates_of_the_Arctic_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Gates_Arctic_NP_Alaska.jpg/800px-Gates_Arctic_NP_Alaska.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Arctic_wilderness_Alaska.jpg/800px-Arctic_wilderness_Alaska.jpg",
    ],
    "Gateway Arch":                 [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/St_Louis_night_expblend_cropped.jpg/800px-St_Louis_night_expblend_cropped.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Gateway_Arch_2015-06-09.jpg/800px-Gateway_Arch_2015-06-09.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Gateway_Arch_from_below.jpg/800px-Gateway_Arch_from_below.jpg",
    ],
    "Glacier":                      [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/GlacierNP_from_RE_Marble_Canyon.jpg/800px-GlacierNP_from_RE_Marble_Canyon.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Glacier_National_Park_going_to_the_sun_road.jpg/800px-Glacier_National_Park_going_to_the_sun_road.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Lake_McDonald_Glacier_NP.jpg/800px-Lake_McDonald_Glacier_NP.jpg",
    ],
    "Glacier Bay":                  [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/Glacier_Bay_National_Park_and_Preserve.jpg/800px-Glacier_Bay_National_Park_and_Preserve.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Glacier_Bay_Alaska.jpg/800px-Glacier_Bay_Alaska.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Margerie_Glacier_Glacier_Bay.jpg/800px-Margerie_Glacier_Glacier_Bay.jpg",
    ],
    "Grand Canyon":                 [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Dawn_on_the_S_rim_of_the_Grand_Canyon_%288645178272%29.jpg/800px-Dawn_on_the_S_rim_of_the_Grand_Canyon_%288645178272%29.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Grand_Canyon_NP_-_Mather_Point.jpg/800px-Grand_Canyon_NP_-_Mather_Point.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Grand_Canyon_Colorado_River.jpg/800px-Grand_Canyon_Colorado_River.jpg",
    ],
    "Grand Teton":                  [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/GrandTetonNP-Panorama.jpg/800px-GrandTetonNP-Panorama.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Grand_Teton_from_Snake_River_Overlook_Ansel_Adams_style.jpg/800px-Grand_Teton_from_Snake_River_Overlook_Ansel_Adams_style.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Jenny_Lake_Grand_Teton.jpg/800px-Jenny_Lake_Grand_Teton.jpg",
    ],
    "Great Basin":                  [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Great_Basin_National_Park.jpg/800px-Great_Basin_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Wheeler_Peak_Great_Basin.jpg/800px-Wheeler_Peak_Great_Basin.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Lehman_Caves_Great_Basin.jpg/800px-Lehman_Caves_Great_Basin.jpg",
    ],
    "Great Sand Dunes":             [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Great_Sand_Dunes_National_Park_and_Preserve.jpg/800px-Great_Sand_Dunes_National_Park_and_Preserve.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Great_Sand_Dunes_Colorado.jpg/800px-Great_Sand_Dunes_Colorado.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Great_Sand_Dunes_Medano_Creek.jpg/800px-Great_Sand_Dunes_Medano_Creek.jpg",
    ],
    "Great Smoky Mountains":        [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Appalachian_Trail_in_Great_Smoky_Mountains.jpg/800px-Appalachian_Trail_in_Great_Smoky_Mountains.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Laurel_Falls_Smoky_Mountains.jpg/800px-Laurel_Falls_Smoky_Mountains.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Clingmans_Dome_Smoky_Mountains.jpg/800px-Clingmans_Dome_Smoky_Mountains.jpg",
    ],
    "Guadalupe Mountains":          [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Guadalupe_Mountains_National_Park.jpg/800px-Guadalupe_Mountains_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/El_Capitan_Guadalupe_Mountains.jpg/800px-El_Capitan_Guadalupe_Mountains.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Guadalupe_Peak_Texas.jpg/800px-Guadalupe_Peak_Texas.jpg",
    ],
    "Haleakala":                    [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Haleakala_National_Park_Crater.jpg/800px-Haleakala_National_Park_Crater.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Haleakala_sunrise.jpg/800px-Haleakala_sunrise.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Haleakala_Crater_Maui.jpg/800px-Haleakala_Crater_Maui.jpg",
    ],
    "Hawaii Volcanoes":             [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Halemaumau_Crater_Kilauea.jpg/800px-Halemaumau_Crater_Kilauea.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Kilauea_lava_flow_Hawaii.jpg/800px-Kilauea_lava_flow_Hawaii.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Hawaii_Volcanoes_NP_lava.jpg/800px-Hawaii_Volcanoes_NP_lava.jpg",
    ],
    "Hot Springs":                  [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Hot_Springs_National_Park_Bathhouse_Row.jpg/800px-Hot_Springs_National_Park_Bathhouse_Row.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Hot_Springs_Arkansas_National_Park.jpg/800px-Hot_Springs_Arkansas_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Hot_Springs_NP_thermal_water.jpg/800px-Hot_Springs_NP_thermal_water.jpg",
    ],
    "Indiana Dunes":                [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Indiana_Dunes_National_Park.jpg/800px-Indiana_Dunes_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Indiana_Dunes_Lake_Michigan.jpg/800px-Indiana_Dunes_Lake_Michigan.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Indiana_Dunes_NP_beach.jpg/800px-Indiana_Dunes_NP_beach.jpg",
    ],
    "Isle Royale":                  [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Isle_Royale_National_Park.jpg/800px-Isle_Royale_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Isle_Royale_Lake_Superior.jpg/800px-Isle_Royale_Lake_Superior.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Rock_Harbor_Isle_Royale.jpg/800px-Rock_Harbor_Isle_Royale.jpg",
    ],
    "Joshua Tree":                  [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Joshua_Tree_-_Rock_formation_edit.jpg/800px-Joshua_Tree_-_Rock_formation_edit.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Joshua_Tree_National_Park_-_Cholla_Cactus_Garden_-_Panorama.jpg/800px-Joshua_Tree_National_Park_-_Cholla_Cactus_Garden_-_Panorama.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Joshua_trees_at_Joshua_Tree_National_Park.jpg/800px-Joshua_trees_at_Joshua_Tree_National_Park.jpg",
    ],
    "Katmai":                       [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Katmai_National_Park_bears.jpg/800px-Katmai_National_Park_bears.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Brooks_Falls_Katmai.jpg/800px-Brooks_Falls_Katmai.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Katmai_Valley_of_Ten_Thousand_Smokes.jpg/800px-Katmai_Valley_of_Ten_Thousand_Smokes.jpg",
    ],
    "Kenai Fjords":                 [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Kenai_Fjords_National_Park.jpg/800px-Kenai_Fjords_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Exit_Glacier_Kenai_Fjords.jpg/800px-Exit_Glacier_Kenai_Fjords.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Kenai_Fjords_kayaking.jpg/800px-Kenai_Fjords_kayaking.jpg",
    ],
    "Kings Canyon":                 [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Kings_Canyon_National_Park.jpg/800px-Kings_Canyon_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/General_Grant_Tree_Kings_Canyon.jpg/800px-General_Grant_Tree_Kings_Canyon.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Kings_Canyon_river.jpg/800px-Kings_Canyon_river.jpg",
    ],
    "Kobuk Valley":                 [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Kobuk_Valley_National_Park.jpg/800px-Kobuk_Valley_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Kobuk_Sand_Dunes_Alaska.jpg/800px-Kobuk_Sand_Dunes_Alaska.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Kobuk_River_Alaska.jpg/800px-Kobuk_River_Alaska.jpg",
    ],
    "Lake Clark":                   [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Lake_Clark_National_Park.jpg/800px-Lake_Clark_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Lake_Clark_Alaska_wilderness.jpg/800px-Lake_Clark_Alaska_wilderness.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Lake_Clark_NP_mountains.jpg/800px-Lake_Clark_NP_mountains.jpg",
    ],
    "Lassen Volcanic":              [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Lassen_Peak_from_Lake_Helen.jpg/800px-Lassen_Peak_from_Lake_Helen.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Bumpass_Hell_Lassen.jpg/800px-Bumpass_Hell_Lassen.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Lassen_Volcanic_National_Park.jpg/800px-Lassen_Volcanic_National_Park.jpg",
    ],
    "Mammoth Cave":                 [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Mammoth_Cave_National_Park.jpg/800px-Mammoth_Cave_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Mammoth_Cave_interior.jpg/800px-Mammoth_Cave_interior.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Mammoth_Cave_Kentucky.jpg/800px-Mammoth_Cave_Kentucky.jpg",
    ],
    "Mesa Verde":                   [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Cliff_Palace_Mesa_Verde.jpg/800px-Cliff_Palace_Mesa_Verde.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Mesa_Verde_National_Park_Colorado.jpg/800px-Mesa_Verde_National_Park_Colorado.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Spruce_Tree_House_Mesa_Verde.jpg/800px-Spruce_Tree_House_Mesa_Verde.jpg",
    ],
    "Mount Rainier":                [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Mount_Rainier_from_Paradise_2.jpg/800px-Mount_Rainier_from_Paradise_2.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Mount_Rainier_NP_wildflowers.jpg/800px-Mount_Rainier_NP_wildflowers.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Reflection_Lakes_Mount_Rainier.jpg/800px-Reflection_Lakes_Mount_Rainier.jpg",
    ],
    "New River Gorge":              [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/New_River_Gorge_Bridge.jpg/800px-New_River_Gorge_Bridge.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/New_River_Gorge_National_Park.jpg/800px-New_River_Gorge_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/New_River_Gorge_WV.jpg/800px-New_River_Gorge_WV.jpg",
    ],
    "North Cascades":               [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/North_Cascades_National_Park.jpg/800px-North_Cascades_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Diablo_Lake_North_Cascades.jpg/800px-Diablo_Lake_North_Cascades.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/North_Cascades_mountains.jpg/800px-North_Cascades_mountains.jpg",
    ],
    "Olympic":                      [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Hoh_Rain_Forest_Olympic.jpg/800px-Hoh_Rain_Forest_Olympic.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Olympic_National_Park_coastline.jpg/800px-Olympic_National_Park_coastline.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Hurricane_Ridge_Olympic_NP.jpg/800px-Hurricane_Ridge_Olympic_NP.jpg",
    ],
    "Petrified Forest":             [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Petrified_Forest_National_Park_2.jpg/800px-Petrified_Forest_National_Park_2.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Petrified_wood_Arizona.jpg/800px-Petrified_wood_Arizona.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/Painted_Desert_Petrified_Forest.jpg/800px-Painted_Desert_Petrified_Forest.jpg",
    ],
    "Pinnacles":                    [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Pinnacles_National_Park_California.jpg/800px-Pinnacles_National_Park_California.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Pinnacles_NP_rock_formations.jpg/800px-Pinnacles_NP_rock_formations.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Pinnacles_National_Park_condor.jpg/800px-Pinnacles_National_Park_condor.jpg",
    ],
    "Redwood":                      [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Redwood_National_Park%2C_fog_in_the_forest.jpg/800px-Redwood_National_Park%2C_fog_in_the_forest.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Redwood_National_Park_ferns.jpg/800px-Redwood_National_Park_ferns.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Coast_Redwoods_Redwood_NP.jpg/800px-Coast_Redwoods_Redwood_NP.jpg",
    ],
    "Rocky Mountain":               [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Rocky_Mountain_National_Park_in_September_2011_-_Glacier_Gorge_from_Bear_Lake.jpg/800px-Rocky_Mountain_National_Park_in_September_2011_-_Glacier_Gorge_from_Bear_Lake.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Trail_Ridge_Road_Rocky_Mountain_NP.jpg/800px-Trail_Ridge_Road_Rocky_Mountain_NP.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Bear_Lake_Rocky_Mountain_NP.jpg/800px-Bear_Lake_Rocky_Mountain_NP.jpg",
    ],
    "Saguaro":                      [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Saguaro_National_Park.jpg/800px-Saguaro_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Saguaro_cactus_Arizona.jpg/800px-Saguaro_cactus_Arizona.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Saguaro_NP_sunset.jpg/800px-Saguaro_NP_sunset.jpg",
    ],
    "Sequoia":                      [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/General_Sherman_Tree.jpg/800px-General_Sherman_Tree.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Sequoia_National_Park_forest.jpg/800px-Sequoia_National_Park_forest.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Moro_Rock_Sequoia_NP.jpg/800px-Moro_Rock_Sequoia_NP.jpg",
    ],
    "Shenandoah":                   [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Shenandoah_National_Park_Skyline_Drive.jpg/800px-Shenandoah_National_Park_Skyline_Drive.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Shenandoah_NP_fall_foliage.jpg/800px-Shenandoah_NP_fall_foliage.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Dark_Hollow_Falls_Shenandoah.jpg/800px-Dark_Hollow_Falls_Shenandoah.jpg",
    ],
    "Theodore Roosevelt":           [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Theodore_Roosevelt_National_Park_badlands.jpg/800px-Theodore_Roosevelt_National_Park_badlands.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Theodore_Roosevelt_NP_bison.jpg/800px-Theodore_Roosevelt_NP_bison.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Little_Missouri_River_Theodore_Roosevelt_NP.jpg/800px-Little_Missouri_River_Theodore_Roosevelt_NP.jpg",
    ],
    "Virgin Islands":               [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Virgin_Islands_National_Park.jpg/800px-Virgin_Islands_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Trunk_Bay_Virgin_Islands.jpg/800px-Trunk_Bay_Virgin_Islands.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/Cinnamon_Bay_Virgin_Islands_NP.jpg/800px-Cinnamon_Bay_Virgin_Islands_NP.jpg",
    ],
    "Voyageurs":                    [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Voyageurs_National_Park.jpg/800px-Voyageurs_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Voyageurs_NP_lake.jpg/800px-Voyageurs_NP_lake.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Voyageurs_National_Park_Minnesota.jpg/800px-Voyageurs_National_Park_Minnesota.jpg",
    ],
    "White Sands":                  [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/White_Sands_National_Park.jpg/800px-White_Sands_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/White_Sands_NM_dunes.jpg/800px-White_Sands_NM_dunes.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/White_Sands_sunset.jpg/800px-White_Sands_sunset.jpg",
    ],
    "Wind Cave":                    [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Wind_Cave_National_Park.jpg/800px-Wind_Cave_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Wind_Cave_boxwork.jpg/800px-Wind_Cave_boxwork.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Wind_Cave_NP_prairie.jpg/800px-Wind_Cave_NP_prairie.jpg",
    ],
    "Wrangell-St. Elias":          [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Wrangell_St_Elias_National_Park.jpg/800px-Wrangell_St_Elias_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Wrangell_St_Elias_glacier.jpg/800px-Wrangell_St_Elias_glacier.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Wrangell_Mountains_Alaska.jpg/800px-Wrangell_Mountains_Alaska.jpg",
    ],
    "Yellowstone":                  [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Grand_Prismatic_Spring_2013.jpg/800px-Grand_Prismatic_Spring_2013.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Old_Faithful_Yellowstone.jpg/800px-Old_Faithful_Yellowstone.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Yellowstone_bison_jam.jpg/800px-Yellowstone_bison_jam.jpg",
    ],
    "Yosemite":                     [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Half_Dome_from_Glacier_Point%2C_Yosemite_NP_-_Diliff.jpg/800px-Half_Dome_from_Glacier_Point%2C_Yosemite_NP_-_Diliff.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Tunnel_View%2C_Yosemite_Valley%2C_Yosemite_NP_-_Diliff.jpg/800px-Tunnel_View%2C_Yosemite_Valley%2C_Yosemite_NP_-_Diliff.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Above_Yosemite_Valley.jpg/800px-Above_Yosemite_Valley.jpg",
    ],
    "Zion":                         [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Angels_Landing_Zion.jpg/800px-Angels_Landing_Zion.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Zion_National_Park_Angels_Landing_Sept_2010.jpg/800px-Zion_National_Park_Angels_Landing_Sept_2010.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/The_Narrows_Zion_NP.jpg/800px-The_Narrows_Zion_NP.jpg",
    ],
}

@st.cache_data(show_spinner=False)
def get_park_photo_urls(park_name: str) -> list[str]:
    import requests
    try:
        # Use Wikipedia's REST API to get page summary + thumbnail
        slug = park_name.replace(" ", "_") + "_National_Park"
        headers = {"User-Agent": "TrailPlanApp/1.0"}

        # Fetch main page thumbnail
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}",
            headers=headers, timeout=8
        )
        data = r.json()
        thumb = data.get("thumbnail", {}).get("source", "")
        original = data.get("originalimage", {}).get("source", "")

        # Also search Wikimedia Commons for more images
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

        # Build final list — thumbnail first, then commons
        results = []
        if original:
            results.append(original)
        elif thumb:
            results.append(thumb)
        results.extend(commons_urls)

        # Deduplicate
        seen = set()
        unique = [u for u in results if not (u in seen or seen.add(u))]
        return unique[:3] if len(unique) >= 3 else unique

    except Exception:
        return []


# ── Park data with coordinates ────────────────────────────────────────────────
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

# ── Layout: map left, settings right ─────────────────────────────────────────
map_col, settings_col = st.columns([2, 1])

with map_col:
    selected = st.session_state.selected_park

    st.markdown('<div class="map-instruction">🗺️ Click a green dot to select a national park</div>', unsafe_allow_html=True)

    # Build folium map
    m = folium.Map(
        location=[39.5, -98.35],
        zoom_start=4,
        tiles="CartoDB dark_matter",
        prefer_canvas=True
    )

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
                f"<b style='font-family:sans-serif;color:#e8ede4;background:#131f14'>{park_name}</b>",
                style="background:#131f14;border:1px solid #2a3d2b;color:#e8ede4;"
            ),
            popup=folium.Popup(park_name, max_width=200)
        ).add_to(m)

        # Pulse ring for selected park
        if is_selected:
            folium.CircleMarker(
                location=[info["lat"], info["lon"]],
                radius=18,
                color="#7ec850",
                fill=False,
                weight=2,
                opacity=0.5,
            ).add_to(m)

    map_data = st_folium(m, width="100%", height=420, returned_objects=["last_object_clicked_popup"])

    # Detect click
    if map_data and map_data.get("last_object_clicked_popup"):
        clicked = map_data["last_object_clicked_popup"]
        if clicked and clicked in PARKS:
            if clicked != st.session_state.selected_park:
                st.session_state.selected_park = clicked
                st.session_state.itinerary = None
                st.rerun()

    # ── Park photos below map ─────────────────────────────────────────────────
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
                    <div style="height:160px;overflow:hidden;border:1px solid #2a3d2b">
                        <img src="{url}"
                             style="width:100%;height:100%;object-fit:cover;display:block"/>
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
            yt_url = f"https://www.youtube.com/results?search_query={trail['youtube_search'].replace(' ', '+')}"
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
                <a href="{yt_url}" target="_blank" style="font-size:12px;color:#7ec850;text-decoration:none;border:1px solid rgba(126,200,80,0.3);padding:4px 12px;display:inline-block;margin-top:4px">▶ Watch on YouTube</a>
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
