# Istanbul Stays

A data-driven web application for searching and comparing Airbnb listings in Istanbul.

Istanbul is one of the most visited cities in the world, and travellers searching for a
short-term rental face thousands of listings with no simple way to compare them by price,
neighbourhood, or room type. This application turns raw Airbnb data into a searchable
tool where users can filter listings, read guest reviews, explore pricing trends, and
add, update, or remove listings.

**Author:** Dany Chamseddine
**Course:** [course number / term]
**Live app:** [paste your Streamlit Community Cloud URL here]

---

## Features

- **Search and filter** listings by neighbourhood, room type, nightly price, minimum-night
  requirement, and yearly availability
- **Map view** of matching listings using their latitude and longitude
- **Guest reviews** for any selected listing, retrieved with a SQL join between the
  `listings` and `reviews` tables
- **Neighbourhood insights**: average nightly price by neighbourhood, listing counts by
  neighbourhood and room type, and the most reviewed listings
- **Full CRUD**: create, read, update, and delete listings, with primary key and foreign
  key constraints enforced by the database

---

## Database design

The database is a SQLite database with two tables in a one-to-many relationship:
one listing can have many reviews.

```
listings                              reviews
--------                              -------
id                INTEGER PK   <----  listing_id  INTEGER NOT NULL (FK)
name              TEXT                id          INTEGER PK
neighbourhood     TEXT                date        TEXT
room_type         TEXT                reviewer_name TEXT
price             REAL                comments    TEXT
latitude          REAL
longitude         REAL
minimum_nights    INTEGER
availability_365  INTEGER
```

**Constraints**

- `id` is an `INTEGER PRIMARY KEY` in both tables, so every row is uniquely identifiable
- `listing_id` is `NOT NULL` — a review that belongs to no listing is meaningless
- `FOREIGN KEY (listing_id) REFERENCES listings(id)` — a review can never reference a
  listing that does not exist
- `PRAGMA foreign_keys = ON` is set on every connection, because SQLite does not enforce
  foreign keys unless explicitly told to
- Data types: `REAL` for price and coordinates, `INTEGER` for counts, `TEXT` for names,
  dates, and comments

**Design decisions**

- `room_type` is stored as a column rather than its own table, since it has only four
  possible values
- `neighbourhood_group` and `license` were dropped from the raw data because they were
  empty or mostly blank
- `host_id` and `host_name` were excluded for privacy reasons

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | The Streamlit application |
| `istanbul_app.db` | The SQLite database |
| `build_database.ipynb` | Notebook that creates the database from the raw CSV files |
| `requirements.txt` | Python dependencies |

### A note on the database file

The full database built from the raw Inside Airbnb data is approximately 130 MB, which
exceeds GitHub's 100 MB file limit. The version in this repository uses the same schema
and the same constraints, but keeps the five most recent reviews per listing with
comment text capped at 400 characters. Every listing is retained and all application
functionality is unchanged. `build_database.ipynb` reproduces the full database from the
original CSV files.

---

## Running locally

```bash
git clone [your repository URL]
cd [repository name]
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Technologies

- **SQLite** — a file-based relational database requiring no server
- **Python / pandas** — data cleaning and loading
- **Streamlit** — the web interface
- **Streamlit Community Cloud** — deployment

---

## Data source

Inside Airbnb. *Istanbul listings and reviews.* https://insideairbnb.com/get-the-data/

---

## AI assistance

The Streamlit application code and this README were developed with AI assistance.
The database design, schema, constraints, and SQL query logic are the author's own work.
