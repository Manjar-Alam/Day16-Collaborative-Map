# Step 1 — Import libraries
import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import gspread
import json

# Step 2 — Configure the application
st.set_page_config(
    page_title="Places We Dream of Visiting",
    page_icon="🌍",
    layout="wide"
)

st.markdown("""

<style>
/* Main page */
.stApp {
    background: #F4F7FA;
    color: #17324D;
}

[data-testid="stAppViewContainer"] {
    background: #F4F7FA;
}

.block-container {
    max-width: 1450px;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

/* Readable typography */
h1, h2, h3, h4, p, label,
[data-testid="stMarkdownContainer"],
[data-testid="stCaptionContainer"] {
    color: #17324D !important;
}

/* Hero banner */
.hero {
    background: linear-gradient(120deg, #092D3E, #116B70);
    padding: 30px 35px;
    border-radius: 16px;
    margin-bottom: 22px;
    color: white !important;
}

.hero h1 {
    color: #FFFFFF !important;
    font-size: 32px;
    font-weight: 800;
    margin: 0 0 10px 0;
    letter-spacing: 0.5px;
}

.hero h3 {
    color: #BCE8E2 !important;
    font-size: 16px;
    font-weight: 500;
    margin: 0 0 14px 0;
}

.hero p {
    color: #E4F2F2 !important;
    font-size: 13px;
    margin: 0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #E8F0F3;
}

[data-testid="stSidebar"] * {
    color: #17324D !important;
}

/* Buttons */
.stButton > button {
    background: #087F83;
    color: white !important;
    border: none;
    border-radius: 9px;
    font-weight: 700;
    padding: 10px 15px;
}

.stButton > button:hover {
    background: #075E63;
    border: none;
}

/* Metrics and data */
[data-testid="stMetric"] {
    background: white;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #DCE6EA;
}

[data-testid="stMetricLabel"] {
    color: #557080 !important;
}

[data-testid="stMetricValue"] {
    color: #087F83 !important;
}

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 10px;
}
/* Text typed inside input fields */
.stTextInput input {
    color: #17324D !important;
    background-color: #FFFFFF !important;
    -webkit-text-fill-color: #17324D !important;
}

/* Placeholder text */
.stTextInput input::placeholder {
    color: #8296A3 !important;
    opacity: 1;
}

/* Input label */
.stTextInput label {
    color: #17324D !important;
}
/* Country dropdown text */
.stSelectbox div[data-baseweb="select"] {
    color: #17324D !important;
    background-color: #FFFFFF !important;
}

/* Live preview success message */
div[data-testid="stAlert"] {
    background-color: #D5F0E8 !important;
    border: 1px solid #168568 !important;
    border-radius: 10px !important;
    opacity: 1 !important;
}

div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span,
div[data-testid="stAlert"] svg {
    color: #075B46 !important;
    fill: #075B46 !important;
    opacity: 1 !important;
    font-weight: 700 !important;
}

/* Selected country in dropdown */
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    opacity: 1 !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
    color: #17324D !important;
    -webkit-text-fill-color: #17324D !important;
    opacity: 1 !important;
}

/* Dropdown options */
div[data-baseweb="popover"] li {
    color: #17324D !important;
    background-color: #FFFFFF !important;
}

div[data-baseweb="popover"] li:hover {
    background-color: #D5F0E8 !important;
}

</style>

""", unsafe_allow_html=True)


st.markdown("""
<div class="hero">
    <h1>🌍 PLACES WE DREAM OF VISITING</h1>
    <h3>ONE WORLD. MANY DREAMS. ONE COLLABORATIVE MAP.</h3>
    <p>30-Day Map Challenge &nbsp; | &nbsp; Day 16
    &nbsp; | &nbsp; Collaborative Map</p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    "### Explore our collective travel dreams",
)
st.markdown(
    "Choose a country, add your name, and become part of "
    "a growing map of places people hope to explore."
)


# Step 3 — Load world boundaries and connect to Google Sheets
@st.cache_data
def load_world():
    world = gpd.read_file(
        "data/ne_110m_admin_0_countries.shp"
    )
    return world.to_crs("EPSG:4326")




@st.cache_resource
def connect_sheet():
    if "gcp_service_account" in st.secrets:
        credentials = dict(st.secrets["gcp_service_account"])
    else:
        with open("service_account.json", "r") as f:
            credentials = json.load(f)

    # Robustly clean and normalize private key formatting
    raw_key = credentials["private_key"].replace("\\n", "\n")
    clean_lines = [line.strip() for line in raw_key.splitlines() if line.strip()]
    credentials["private_key"] = "\n".join(clean_lines) + "\n"
    import base64

key = credentials["private_key"]

st.write("Private key starts correctly:", key.startswith("-----BEGIN PRIVATE KEY-----"))
st.write("Private key ends correctly:", key.strip().endswith("-----END PRIVATE KEY-----"))
st.write("Private key length:", len(key))
st.write("Private key contains literal newline escapes:", "\\n" in key)
st.write("Private key contains actual line breaks:", "\n" in key)

base64_part = key.replace("-----BEGIN PRIVATE KEY-----", "")
base64_part = base64_part.replace("-----END PRIVATE KEY-----", "")
base64_part = "".join(base64_part.split())

try:
    base64.b64decode(base64_part, validate=True)
    st.write("Base64 validation: PASSED")
except Exception as e:
    st.write("Base64 validation: FAILED", str(e))

    gc = gspread.service_account_from_dict(credentials)

    sheet = gc.open_by_key(
        st.secrets["SHEET_ID"]
    ).sheet1

    return sheet





@st.cache_data(ttl=5)
def load_contributions():

    sheet = connect_sheet()

    # Read all worksheet values
    records = sheet.get_all_values()

    # Empty spreadsheet
    if not records:
        return pd.DataFrame(
            columns=["Contributor", "Country"]
        )

    # First row contains column headings
    headers = [
        str(value).strip()
        for value in records[0]
    ]

    # Check required columns
    if "Contributor" not in headers or "Country" not in headers:
        raise ValueError(
            f"Incorrect Google Sheet headers: {headers}. "
            "Expected Contributor and Country in the first row."
        )

    # Convert rows into a DataFrame
    df = pd.DataFrame(
        records[1:],
        columns=headers
    )

    # Keep only required columns
    df = df[["Contributor", "Country"]]

    # Remove empty rows
    df = df.dropna()
    df = df[
        (df["Contributor"].str.strip() != "") &
        (df["Country"].str.strip() != "")
    ]

    return df


world = load_world()
countries = sorted(world["NAME"].dropna().unique())

# Step 4 — Collect participant information
st.sidebar.header("✈️ Add Your Dream Destination")

name = st.sidebar.text_input(
    "Your name",
    placeholder="Enter your name"
)

country = st.sidebar.selectbox(
    "Which country do you dream of visiting?",
    countries,
    index=None,
    placeholder="Select a country"
)

contributions = load_contributions()

if not contributions.empty:
    counts = contributions.groupby("Country").size().to_dict()
else:
    counts = {}

# Add a temporary vote for live preview
preview_counts = counts.copy()

if country:
    preview_counts[country] = (
        preview_counts.get(country, 0) + 1
    )

map_data = world.copy()

map_data["Dream_Count"] = (
    map_data["NAME"].map(preview_counts).fillna(0)
)

# Step 5 — Create the interactive world map
geojson = json.loads(map_data.to_json())

fig = px.choropleth(
    map_data,
    geojson=geojson,
    locations="NAME",
    featureidkey="properties.NAME",
    color="Dream_Count",
    hover_name="NAME",
    hover_data={"Dream_Count": True},
    color_continuous_scale=[
        [0.00, "#EAF0F3"],
        [0.25, "#B7DDE0"],
        [0.50, "#66B8B5"],
        [0.75, "#238A91"],
        [1.00, "#084C61"]
    ],
    projection="natural earth",
    title="OUR DREAM DESTINATIONS AROUND THE WORLD"
)


fig.update_geos(
    showcoastlines=True,
    coastlinecolor="#FFFFFF",
    coastlinewidth=1,
    showland=True,
    landcolor="#EAF0F3",
    showocean=True,
    oceancolor="#DCEAF1",
    showcountries=True,
    countrycolor="#FFFFFF",
    countrywidth=0.8,
    showframe=False,
    projection_type="natural earth"
)

fig.update_layout(
    height=700,
    margin=dict(l=0, r=10, t=65, b=10),
    paper_bgcolor="#F4F7FA",
    plot_bgcolor="#F4F7FA",
    font=dict(
        family="Arial",
        color="#17324D",
        size=12
    ),
    title=dict(
        text="OUR DREAM DESTINATIONS AROUND THE WORLD",
        font=dict(size=19, color="#17324D"),
        x=0.02,
        xanchor="left"
    ),
    coloraxis_colorbar=dict(
        title=dict(
            text="Dream Votes",
            font=dict(color="#17324D")
        ),
        tickfont=dict(color="#17324D")
    ),
    dragmode="pan"
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displayModeBar": True,
        "displaylogo": False,
        "scrollZoom": True,
        "responsive": True,
        "modeBarButtonsToAdd": [
            "select2d",
            "lasso2d"
        ]
    }
)


if country:
    st.markdown(f"""
    <div style="
        background-color:#D5F0E8;
        border-left:5px solid #087F83;
        padding:15px 20px;
        border-radius:8px;
        color:#075B46;
        font-size:16px;
        font-weight:700;
        margin:12px 0;
    ">
        🌍 Live Preview: {country} is your selected destination.
        Submit to add it to our community map!
    </div>
    """, unsafe_allow_html=True)

# Step 6 — Save contribution to Google Sheets
if st.sidebar.button(
    "Submit My Dream Destination",
    type="primary",
    use_container_width=True
):
    if not name.strip():
        st.sidebar.error("Please enter your name.")

    elif not country:
        st.sidebar.error("Please select a country.")

    else:
        connect_sheet().append_row(
            [name.strip(), country],
            value_input_option="USER_ENTERED"
        )

        load_contributions.clear()

        st.sidebar.success(
            f"Your dream destination, {country}, has been saved!"
        )

        st.rerun()

# Step 7 — Display collaborative statistics
st.divider()

st.subheader("🌏 Our Collective Travel Dreams")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Contributions",
    len(contributions)
)

col2.metric(
    "Countries Selected",
    contributions["Country"].nunique()
    if not contributions.empty else 0
)

col3.metric(
    "Dream Destinations",
    len(counts)
)

if not contributions.empty:
    st.subheader("✈️ Community Contributions")

    st.dataframe(
        contributions,
        use_container_width=True,
        hide_index=True
    )
else:
    st.write("Be the first to add your dream destination!")
