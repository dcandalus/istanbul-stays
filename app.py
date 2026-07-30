"""
Istanbul Stays - Airbnb listing explorer
Application code (Streamlit interface) - developed with AI assistance.
Database schema, constraints, and SQL query logic authored by Dany Chamseddine.
"""

import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "istanbul_app.db"

st.set_page_config(page_title="Istanbul Stays", page_icon="🏙️", layout="wide")


# ---------------------------------------------------------------- database
@st.cache_resource
def get_connection():
    """Open the SQLite database and turn on foreign key enforcement."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_listing_id ON reviews(listing_id);")
    conn.commit()
    return conn


conn = get_connection()


@st.cache_data
def load_neighbourhoods():
    q = "SELECT DISTINCT neighbourhood FROM listings WHERE neighbourhood IS NOT NULL ORDER BY neighbourhood;"
    return pd.read_sql_query(q, conn)["neighbourhood"].tolist()


@st.cache_data
def load_room_types():
    q = "SELECT DISTINCT room_type FROM listings WHERE room_type IS NOT NULL ORDER BY room_type;"
    return pd.read_sql_query(q, conn)["room_type"].tolist()


def run(query, params=()):
    return pd.read_sql_query(query, conn, params=params)


# ---------------------------------------------------------------- header
st.title("🏙️ Istanbul Stays")
st.caption(
    "Search and compare Airbnb listings across Istanbul, view guest reviews, "
    "and explore pricing trends by neighbourhood."
)

tab_search, tab_insights, tab_manage = st.tabs(
    ["🔎 Search listings", "📊 Neighbourhood insights", "✏️ Manage listings"]
)


# ================================================================ TAB 1
with tab_search:
    st.sidebar.header("Filters")

    neighbourhoods = load_neighbourhoods()
    room_types = load_room_types()

    chosen_hoods = st.sidebar.multiselect("Neighbourhood", neighbourhoods)
    chosen_rooms = st.sidebar.multiselect("Room type", room_types)

    max_price = st.sidebar.slider(
        "Maximum nightly price (TRY)", 0, 20000, 5000, step=250
    )
    max_nights = st.sidebar.slider("Maximum minimum-night requirement", 1, 30, 7)
    only_available = st.sidebar.checkbox("Only listings available this year", value=False)
    reviewed_only = st.sidebar.checkbox("Only listings that have reviews", value=True)
    limit = st.sidebar.select_slider("Results to show", [25, 50, 100, 250], value=50)

    # Build the WHERE clause from whichever filters the user selected
    clauses = ["price IS NOT NULL", "price <= ?", "minimum_nights <= ?"]
    params = [max_price, max_nights]

    if chosen_hoods:
        clauses.append("neighbourhood IN (%s)" % ",".join("?" * len(chosen_hoods)))
        params += chosen_hoods

    if chosen_rooms:
        clauses.append("room_type IN (%s)" % ",".join("?" * len(chosen_rooms)))
        params += chosen_rooms

    if only_available:
        clauses.append("availability_365 > 0")

    if reviewed_only:
        clauses.append(
            "EXISTS (SELECT 1 FROM reviews WHERE reviews.listing_id = listings.id)"
        )

    where = " AND ".join(clauses)

    results = run(
        f"""
        SELECT id, name, neighbourhood, room_type, price,
               minimum_nights, availability_365, latitude, longitude
        FROM listings
        WHERE {where}
        ORDER BY price ASC
        LIMIT ?;
        """,
        params + [limit],
    )

    total = run(f"SELECT COUNT(*) AS n FROM listings WHERE {where};", params)["n"][0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Matching listings", f"{total:,}")
    c2.metric("Median price shown", f"{results['price'].median():,.0f} TRY" if len(results) else "-")
    c3.metric("Neighbourhoods", results["neighbourhood"].nunique() if len(results) else 0)

    if results.empty:
        st.warning("No listings match those filters. Try widening the price range.")
    else:
        st.dataframe(
            results.drop(columns=["latitude", "longitude"]),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Where these listings are")
        st.map(results[["latitude", "longitude"]].dropna(), size=20)

        # ---- reviews for one listing (JOIN between the two tables)
        st.subheader("Guest reviews")
        options = {f"{r['name']}  -  {r['neighbourhood']}": r["id"] for _, r in results.iterrows()}
        picked = st.selectbox("Choose a listing to read its reviews", list(options.keys()))
        listing_id = options[picked]

        reviews = run(
            """
            SELECT listings.name, listings.neighbourhood, listings.price,
                   reviews.date, reviews.reviewer_name, reviews.comments
            FROM listings
            JOIN reviews ON listings.id = reviews.listing_id
            WHERE listings.id = ?
            ORDER BY reviews.date DESC;
            """,
            (listing_id,),
        )

        if reviews.empty:
            st.info("This listing has no reviews yet.")
        else:
            st.write(f"**{len(reviews)} review(s)**")
            for _, row in reviews.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['reviewer_name']}** · {row['date']}")
                    st.write(row["comments"])


# ================================================================ TAB 2
with tab_insights:
    st.subheader("Average nightly price by neighbourhood")
    avg_price = run(
        """
        SELECT neighbourhood, ROUND(AVG(price), 0) AS avg_price, COUNT(*) AS listings
        FROM listings
        WHERE price IS NOT NULL
        GROUP BY neighbourhood
        HAVING COUNT(*) >= 20
        ORDER BY avg_price DESC
        LIMIT 15;
        """
    )
    st.bar_chart(avg_price.set_index("neighbourhood")["avg_price"])
    st.caption("Neighbourhoods with at least 20 listings, highest average price first.")

    st.subheader("Where the listings are concentrated")
    counts = run(
        """
        SELECT neighbourhood, COUNT(*) AS listings
        FROM listings
        GROUP BY neighbourhood
        ORDER BY listings DESC
        LIMIT 15;
        """
    )
    st.bar_chart(counts.set_index("neighbourhood")["listings"])

    st.subheader("Most reviewed listings")
    most_reviewed = run(
        """
        SELECT listings.name, listings.neighbourhood, listings.price,
               COUNT(reviews.id) AS review_count
        FROM listings
        JOIN reviews ON listings.id = reviews.listing_id
        GROUP BY listings.id
        ORDER BY review_count DESC
        LIMIT 10;
        """
    )
    st.dataframe(most_reviewed, use_container_width=True, hide_index=True)

    st.subheader("Listings by room type")
    by_room = run(
        "SELECT room_type, COUNT(*) AS listings FROM listings GROUP BY room_type ORDER BY listings DESC;"
    )
    st.bar_chart(by_room.set_index("room_type")["listings"])


# ================================================================ TAB 3
with tab_manage:
    st.write(
        "Add, update, or remove listings. All changes are written to the database "
        "and respect the primary key and foreign key constraints."
    )

    add, edit, remove = st.columns(3)

    # ---- CREATE
    with add:
        st.markdown("### Add a listing")
        with st.form("add_listing"):
            new_name = st.text_input("Listing name")
            new_hood = st.selectbox("Neighbourhood", load_neighbourhoods(), key="add_hood")
            new_room = st.selectbox("Room type", load_room_types(), key="add_room")
            new_price = st.number_input("Price (TRY)", min_value=0.0, value=1500.0)
            new_nights = st.number_input("Minimum nights", min_value=1, value=1)
            new_avail = st.number_input("Availability (days/year)", 0, 365, 180)
            if st.form_submit_button("Add listing"):
                if not new_name.strip():
                    st.error("A listing needs a name.")
                else:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO listings
                            (name, neighbourhood, room_type, price,
                             minimum_nights, availability_365)
                        VALUES (?, ?, ?, ?, ?, ?);
                        """,
                        (new_name, new_hood, new_room, new_price, new_nights, new_avail),
                    )
                    conn.commit()
                    st.success(f"Added listing #{cur.lastrowid}.")

    # ---- UPDATE
    with edit:
        st.markdown("### Update a price")
        with st.form("edit_listing"):
            edit_id = st.number_input("Listing ID", min_value=1, step=1, key="edit_id")
            edit_price = st.number_input("New price (TRY)", min_value=0.0, value=2000.0)
            if st.form_submit_button("Update price"):
                cur = conn.cursor()
                cur.execute(
                    "UPDATE listings SET price = ? WHERE id = ?;", (edit_price, edit_id)
                )
                conn.commit()
                if cur.rowcount:
                    st.success(f"Listing #{edit_id} updated.")
                else:
                    st.error(f"No listing found with ID {edit_id}.")

    # ---- DELETE
    with remove:
        st.markdown("### Delete a listing")
        with st.form("delete_listing"):
            del_id = st.number_input("Listing ID", min_value=1, step=1, key="del_id")
            st.caption(
                "Reviews belonging to the listing are removed first, because the "
                "foreign key does not allow a review to reference a listing that "
                "no longer exists."
            )
            if st.form_submit_button("Delete listing"):
                cur = conn.cursor()
                cur.execute("DELETE FROM reviews WHERE listing_id = ?;", (del_id,))
                removed_reviews = cur.rowcount
                cur.execute("DELETE FROM listings WHERE id = ?;", (del_id,))
                conn.commit()
                if cur.rowcount:
                    st.success(
                        f"Deleted listing #{del_id} and {removed_reviews} related review(s)."
                    )
                else:
                    st.error(f"No listing found with ID {del_id}.")

    st.divider()
    st.markdown("### Look up a listing by ID")
    lookup_id = st.number_input("Listing ID", min_value=1, step=1, key="lookup_id")
    if st.button("Look up"):
        found = run("SELECT * FROM listings WHERE id = ?;", (lookup_id,))
        if found.empty:
            st.warning("No listing with that ID.")
        else:
            st.dataframe(found, use_container_width=True, hide_index=True)


st.divider()
st.caption(
    "Data source: Inside Airbnb (insideairbnb.com). Built with Streamlit, "
    "Python, pandas and SQLite."
)
