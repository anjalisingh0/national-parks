import os
import requests
import sqlite3
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
API_KEY = os.getenv('NPS_API_KEY', 'YOUR_API_KEY_HERE')
BASE_URL = 'https://developer.nps.gov/api/v1'

# Database configuration
DB_PATH = 'national_parks_new.db'

def create_database_schema():
    """Create the database schema if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create states, parks, and activities tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS states (
        state_code TEXT PRIMARY KEY,
        state_name TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parks (
        park_code TEXT PRIMARY KEY,
        full_name TEXT,
        designation TEXT,
        description TEXT,
        url TEXT,
        weather_info TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS state_parks (
        state_code TEXT,
        park_code TEXT,
        PRIMARY KEY (state_code, park_code),
        FOREIGN KEY (state_code) REFERENCES states(state_code),
        FOREIGN KEY (park_code) REFERENCES parks(park_code)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        activity_id INTEGER PRIMARY KEY,
        activity_name TEXT UNIQUE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS park_activities (
        park_code TEXT,
        activity_id INTEGER,
        PRIMARY KEY (park_code, activity_id),
        FOREIGN KEY (park_code) REFERENCES parks(park_code),
        FOREIGN KEY (activity_id) REFERENCES activities(activity_id)
    )
    ''')

    # Multimedia and people tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS multimedia (
        media_id INTEGER PRIMARY KEY AUTOINCREMENT,
        park_code TEXT,
        title TEXT,
        caption TEXT,
        url TEXT,
        credit TEXT,
        FOREIGN KEY (park_code) REFERENCES parks(park_code)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS people (
        person_id INTEGER PRIMARY KEY AUTOINCREMENT,
        park_code TEXT,
        name TEXT,
        role TEXT,
        FOREIGN KEY (park_code) REFERENCES parks(park_code)
    )
    ''')

    conn.commit()
    conn.close()

# Fetch parks data and additional info
def get_parks_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    state_codes = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
    for state_code in state_codes:
        params = {'stateCode': state_code, 'api_key': API_KEY, 'limit': 100}
        try:
            print(f"Fetching parks for state {state_code}...")
            response = requests.get(f'{BASE_URL}/parks', params=params)
            response.raise_for_status()
            data = response.json()
            for park in data.get('data', []):
                park_code = park.get('parkCode')
                cursor.execute('''
                INSERT OR REPLACE INTO parks (park_code, full_name, designation, description, url, weather_info)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    park_code,
                    park.get('fullName'),
                    park.get('designation'),
                    park.get('description'),
                    park.get('url'),
                    park.get('weatherInfo', '')
                ))
                # Multimedia
                for media in park.get('images', []):
                    cursor.execute('''
                    INSERT INTO multimedia (park_code, title, caption, url, credit)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (park_code, media.get('title'), media.get('caption'), media.get('url'), media.get('credit')))
                # People
                for person in park.get('contacts', {}).get('phoneNumbers', []):
                    cursor.execute('''
                    INSERT INTO people (park_code, name, role)
                    VALUES (?, ?, ?)
                    ''', (park_code, person.get('name', 'N/A'), person.get('type', 'N/A')))
            conn.commit()
            time.sleep(0.5)
        except requests.RequestException as e:
            print(f"Error fetching parks for {state_code}: {e}")
    conn.close()

def main():
    print("Setting up database schema...")
    create_database_schema()
    print("Fetching parks data from NPS API...")
    get_parks_data()
    print("Database setup complete!")

if __name__ == '__main__':
    main()