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
    
    # Create tables
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
    
    conn.commit()
    conn.close()

# Populate the states table with US states
def populate_states():
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    states = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", 
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", 
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", 
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", 
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", 
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", 
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", 
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", 
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", 
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", 
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", 
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", 
        "WI": "Wisconsin", "WY": "Wyoming"
    }
    
    for code, name in states.items():
        cursor.execute('INSERT OR IGNORE INTO states VALUES (?, ?)', (code, name))
    
    conn.commit()
    conn.close()

#Fetch parks data from NPS API and store in database
def get_parks_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    state_codes = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", 
        "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", 
        "VA", "WA", "WV", "WI", "WY"
    ]
    
    activity_id_map = {}  # To track activity IDs
    
    for state_code in state_codes:
        params = {
            'stateCode': state_code,
            'api_key': API_KEY,
            'limit': 100  # Ensure we get all parks
        }
        
        try:
            print(f"Fetching parks for state {state_code}...")
            response = requests.get(f'{BASE_URL}/parks', params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process each park
            for park in data.get('data', []):
                # Insert or update park info DETAILS
                cursor.execute('''
                INSERT OR REPLACE INTO parks 
                (park_code, full_name, designation, description, url, weather_info)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    park.get('parkCode'),
                    park.get('fullName'),
                    park.get('designation'),
                    park.get('description'),
                    park.get('url'),
                    park.get('weatherInfo', '')
                ))
                
                # Create state-park relationship - STATE & PARK TABLE
                cursor.execute('''
                INSERT OR IGNORE INTO state_parks (state_code, park_code)
                VALUES (?, ?)
                ''', (state_code, park.get('parkCode')))
                
                # Process activities -  ACTIVITIES TABLE
                for activity in park.get('activities', []):
                    activity_name = activity.get('name')
                    
                    # Check if activity already exists in our map
                    if activity_name not in activity_id_map:
                        cursor.execute('''
                        INSERT OR IGNORE INTO activities (activity_name)
                        VALUES (?)
                        ''', (activity_name,))
                        
                        # Get the assigned ID
                        cursor.execute('SELECT activity_id FROM activities WHERE activity_name = ?', (activity_name,))
                        activity_id = cursor.fetchone()[0]
                        activity_id_map[activity_name] = activity_id
                    else:
                        activity_id = activity_id_map[activity_name]
                    
                    # Create park-activity relationship
                    cursor.execute('''
                    INSERT OR IGNORE INTO park_activities (park_code, activity_id)
                    VALUES (?, ?)
                    ''', (park.get('parkCode'), activity_id))
            
            conn.commit()
            
            # Respect API rate limits
            time.sleep(0.5)
            
        except requests.RequestException as e:
            print(f"Error fetching parks for {state_code}: {e}")
    
    conn.close()

def main():
    """Main function to set up and populate the database"""
    print("Setting up database schema...")
    create_database_schema()
    
    print("Populating states table...")
    populate_states()
    
    print("Fetching parks data from NPS API...")
    get_parks_data()
    
    print("Database setup complete!")

if __name__ == '__main__':
    main()