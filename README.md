# Istanbul Stays

A data-driven web application for searching and comparing Airbnb listings in Istanbul.

Istanbul is one of the most visited cities in the world, and travellers searching for a
short-term rental face thousands of listings with no simple way to compare them by price,
neighbourhood, or room type. This application turns raw Airbnb data into a searchable
tool where users can filter listings, read guest reviews, explore pricing trends, and
add, update, or remove listings.

**Author:** Dany Chamseddine
**Course:** 
**Live app:** 

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

The listing table has all the information about listings, and it holds the main primary key to join when querying between both tables: the id column. This join is possible because listings.id and reviews.listing_id (which is the foreign key of the reviews table) both contain the id of the listing, allowing them to be matched to reveal reviews about individual listings.  A row in the listings table is a listing with all of its details such as the neighborhood and yearly availability, while a row in the reviews table is one individual review and its commenter. Each row has the id of the listing attached to it, allowing us to perform joins on the id of the listing. Through this, we can have both tables in their own respective element, but we also allow for the possibility of joins (as signified by the 1 listing -> many reviews notation) to ensure that 1 listing can return several reviews. This allows users to see reviews based on different characteristics of the listing, such as what neighborhood it is in and whatnot.

Several changes were made throughout the handling of the actual data. I removed pre-existing columns from the listing table due to them being mostly empty or blank: license and neighborhood_group.  I also opted to keep room_type as a column instead of fleshing it out to a table due to it having only four values. Host_id and host_name were also excluded from the final listings table for privacy concerns.

Here is a list of the constraints featured in creating the tables and database:
Foreign keys were explicitly turned on using cur.execute("PRAGMA foreign_keys = ON;") because SQLite ignores foreign keys automatically unless told otherwise.
Id in both tables was made as an INTEGER PRIMARY KEY; PRIMARY KEY so that each row can be uniquely identified and INTEGER so that the table recognizes it’s always a non decimal number
Listing_id was also an INTEGER and was marked NOT NULL as a null listing review is useless
I ensured “FOREIGN KEY (listing_id) REFERENCES listings(id)” was implemented so that listing_id always refers to a listing that DOES exist
Appropriate data types such as REAL for decimals (latitude/longitude) and INTEGER for availability_365 were implemented in the creation of the tables.

These rules are absolutely mandatory to ensure smooth data importation, retrieval, and manipulation; the main thing being that the data needs to always refer to listings that actually exist.

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
