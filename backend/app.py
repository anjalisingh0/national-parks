from flask import Flask, render_template, request, jsonify
import os
import requests

from dotenv import load_dotenv

app = Flask(__name__)

API_KEY = os.getenv('NPS_API_KEY', 'YOUR_API_KEY_HERE')
BASE_URL = 'https://developer.nps.gov/api/v1'

def get_parks_by_state(state_code):
    """
    Fetch national parks for a given state code.
    
    :param state_code: Two-letter state abbreviation (e.g., 'CA', 'NY')
    :return: List of parks in the state
    """
    params = {
        'stateCode': state_code,
        'api_key': API_KEY
    }
    
    try:
        response = requests.get(f'{BASE_URL}/parks', params=params)
        response.raise_for_status()
        data = response.json()
 
        # Filter only "National Park" designations
        national_parks = [park for park in data.get('data', []) if park.get('designation') == 'National Park']
        return national_parks
        
    except requests.RequestException as e:
        print(f"Error fetching parks: {e}")
        return []

# Fetch all states and their national parks
def get_all_parks():
    state_codes = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", 
        "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", 
        "VA", "WA", "WV", "WI", "WY"
    ]
    
    all_parks = {}
    
    for state in state_codes:
        parks = get_parks_by_state(state)
        if parks:
            all_parks[state] = parks
    
    return all_parks



def get_park_details(park_code):
    params = {'parkCode': park_code, 'api_key': API_KEY}
    try:
        response = requests.get(f'{BASE_URL}/parks', params=params)
        print(response)
        response.raise_for_status()
        print(response.json().get('data', [])[0])
        return response.json().get('data', [])[0] if response.json().get('data') else None
    except requests.RequestException:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_parks', methods=['GET'])
def fetch_parks():
    state_code = request.args.get('state_code').upper()
    parks = get_parks_by_state(state_code)
    return jsonify(parks)

@app.route('/get_all_parks', methods=['GET'])
def fetch_all_parks():
    parks = get_all_parks()
    print(parks)
    return jsonify(parks)

@app.route('/get_park_details', methods=['GET'])
def fetch_park_details():
    park_code = request.args.get('park_code')
    park_details = get_park_details(park_code)
    return jsonify(park_details)

if __name__ == '__main__':
    app.run(debug=True)
