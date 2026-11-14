
import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Global Aviation Analytics",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM UI
# ==========================================

st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"] {
        background: var(--secondary-background-color);
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.15);
    }

    [data-testid="stPlotlyChart"] {
        border-radius: 12px;
    }

    div[data-testid="stSidebarContent"] {
        padding-top: 1.5rem;
    }

    .main-title {
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 0;
    }

    .sub-title {
        color: gray;
        margin-top: 5px;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# DATA LOADING - CACHED
# ==========================================

@st.cache_data(show_spinner="Loading airport dataset...")
def load_data():

    data = pd.read_csv(
        "dataset/processed/airports_geospatial.csv",
        low_memory=False
    )

    data["latitude_deg"] = pd.to_numeric(
        data["latitude_deg"], errors="coerce"
    )

    data["longitude_deg"] = pd.to_numeric(
        data["longitude_deg"], errors="coerce"
    )

    data = data.dropna(
        subset=["latitude_deg", "longitude_deg"]
    )

    data["iso_country"] = data["iso_country"].fillna(
        "Unknown"
    )

    data["type"] = data["type"].fillna("Unknown")

    data["name"] = data["name"].fillna("Unknown Airport")

    return data


df = load_data()


# ==========================================
# HEADER
# ==========================================

st.markdown(
    '<div class="main-title">✈️ Global Aviation Infrastructure</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">Global Airport Distribution & Geospatial Analytics</div>',
    unsafe_allow_html=True
)

st.divider()


# ==========================================
# SIDEBAR FILTERS
# ==========================================

st.sidebar.title("✈️ Dashboard Controls")

st.sidebar.caption("Customize your aviation analysis")

country_options = sorted(
    df["iso_country"].unique().tolist()
)

type_options = sorted(
    df["type"].unique().tolist()
)

with st.sidebar.form("filter_form"):

    st.subheader("Geographic Filter")

    selected_country = st.selectbox(
        "Select Country",
        ["All Countries"] + country_options,
        index=0
    )

    st.divider()

    st.subheader("Airport Categories")

    selected_types = st.multiselect(
        "Select Airport Types",
        options=type_options,
        default=type_options,
        placeholder="Choose airport types...",
        help="Select one or multiple airport categories."
    )

    st.divider()

    apply_filter = st.form_submit_button(
        "Apply Filters",
        type="primary",
        use_container_width=True
    )

    reset_filter = st.form_submit_button(
        "Reset Filters",
        use_container_width=True
    )


# ==========================================
# FILTER PROCESSING
# ==========================================

if "active_country" not in st.session_state:
    st.session_state.active_country = "All Countries"

if "active_types" not in st.session_state:
    st.session_state.active_types = type_options.copy()

if apply_filter:
    st.session_state.active_country = selected_country
    st.session_state.active_types = selected_types

if reset_filter:
    st.session_state.active_country = "All Countries"
    st.session_state.active_types = type_options.copy()

filtered_df = df

if st.session_state.active_country != "All Countries":
    filtered_df = filtered_df[
        filtered_df["iso_country"]
        == st.session_state.active_country
    ]

filtered_df = filtered_df[
    filtered_df["type"].isin(st.session_state.active_types)
]


# ==========================================
# EMPTY DATA CHECK
# ==========================================

if filtered_df.empty:

    st.warning(
        "No airport records found. Please change your filters."
    )

    st.stop()


# ==========================================
# KPI METRICS
# ==========================================

st.subheader("Overview")

col1, col2, col3, col4 = st.columns(4)

scheduled_count = (
    filtered_df["scheduled_service"]
    .astype(str)
    .str.strip()
    .str.lower()
    .eq("yes")
    .sum()
    if "scheduled_service" in filtered_df.columns
    else 0
)

col1.metric(
    "Total Airports",
    f"{len(filtered_df):,}"
)

col2.metric(
    "Countries",
    f"{filtered_df['iso_country'].nunique():,}"
)

col3.metric(
    "Airport Types",
    f"{filtered_df['type'].nunique():,}"
)

col4.metric(
    "Scheduled Airports",
    f"{scheduled_count:,}"
)

st.divider()


# ==========================================
# GLOBAL AIRPORT MAP
# ==========================================

st.subheader("🌍 Global Airport Distribution")

# Limit map records to improve rendering performance
MAP_LIMIT = 5000

if len(filtered_df) > MAP_LIMIT:

    map_df = filtered_df.sample(
        n=MAP_LIMIT,
        random_state=42
    )

    st.caption(
        f"Showing a representative sample of {MAP_LIMIT:,} "
        f"airports from {len(filtered_df):,} filtered records."
    )

else:
    map_df = filtered_df


fig_map = px.scatter_geo(
    map_df,
    lat="latitude_deg",
    lon="longitude_deg",
    color="type",
    hover_name="name",
    hover_data=["iso_country"],
    projection="natural earth",
    opacity=0.65
)

fig_map.update_layout(
    height=550,
    margin=dict(l=0, r=0, t=20, b=0),
    legend_title_text="Airport Type"
)

fig_map.update_traces(
    marker=dict(size=4)
)

st.plotly_chart(
    fig_map,
    use_container_width=True,
    config={
        "displayModeBar": False,
        "scrollZoom": False,
        "responsive": True
    }
)


# ==========================================
# COUNTRY & TYPE ANALYSIS
# ==========================================

st.divider()

left, right = st.columns(2)

with left:

    st.subheader("Top 15 Countries")

    country_data = (
        filtered_df["iso_country"]
        .value_counts()
        .head(15)
        .rename_axis("Country")
        .reset_index(name="Airports")
    )

    fig_country = px.bar(
        country_data,
        x="Airports",
        y="Country",
        orientation="h",
        text="Airports",
        color="Airports",
        color_continuous_scale="Blues"
    )

    fig_country.update_layout(
        height=450,
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=20, b=10)
    )

    st.plotly_chart(
        fig_country,
        use_container_width=True,
        config={"displayModeBar": False}
    )


with right:

    st.subheader("Airport Type Distribution")

    type_data = (
        filtered_df["type"]
        .value_counts()
        .rename_axis("Type")
        .reset_index(name="Count")
    )

    fig_type = px.pie(
        type_data,
        names="Type",
        values="Count",
        hole=0.55,
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig_type.update_layout(
        height=450,
        margin=dict(l=10, r=10, t=20, b=10),
        legend_title_text="Airport Type"
    )

    st.plotly_chart(
        fig_type,
        use_container_width=True,
        config={"displayModeBar": False}
    )


# ==========================================
# LATITUDE DISTRIBUTION
# ==========================================

st.divider()

st.subheader("📊 Geographic Coordinate Analysis")

col1, col2 = st.columns(2)

with col1:

    fig_lat = px.histogram(
        filtered_df,
        x="latitude_deg",
        nbins=40,
        title="Latitude Distribution",
        color_discrete_sequence=["#3498db"]
    )

    fig_lat.update_layout(height=350)

    st.plotly_chart(
        fig_lat,
        use_container_width=True,
        config={"displayModeBar": False}
    )


with col2:

    fig_lon = px.histogram(
        filtered_df,
        x="longitude_deg",
        nbins=40,
        title="Longitude Distribution",
        color_discrete_sequence=["#16a085"]
    )

    fig_lon.update_layout(height=350)

    st.plotly_chart(
        fig_lon,
        use_container_width=True,
        config={"displayModeBar": False}
    )


# ==========================================
# DATA TABLE
# ==========================================

st.divider()

st.subheader("Airport Records")

st.caption(
    f"Showing first 100 records out of {len(filtered_df):,} airports."
)

st.dataframe(
    filtered_df.head(100),
    use_container_width=True,
    height=350,
    hide_index=True
)


# ==========================================
# DOWNLOAD DATA
# ==========================================

@st.cache_data
def convert_csv(data):

    return data.to_csv(index=False).encode("utf-8")


st.download_button(
    label="⬇️ Download Filtered Dataset",
    data=convert_csv(filtered_df),
    file_name="filtered_airports.csv",
    mime="text/csv",
    use_container_width=True
)


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Global Aviation Infrastructure Analysis | "
    "Python • Pandas • Plotly • Streamlit"
)
