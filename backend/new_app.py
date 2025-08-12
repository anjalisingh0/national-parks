from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__, template_folder='../templates')


# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '../database/national_parks_new.db')

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def get_parks_by_state(state_code):
    """Get all national parks for a specific state from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query to get parks for a specific state with "National Park" designation
    cursor.execute('''
    SELECT p.* FROM parks p
    JOIN state_parks sp ON p.park_code = sp.park_code
    WHERE sp.state_code = ?
    ORDER BY p.full_name
    ''', (state_code,))
    
    parks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return parks

def get_all_parks():
    """Get all parks organized by state from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query all state codes
    cursor.execute('SELECT state_code FROM states ORDER BY state_code')
    states = [row['state_code'] for row in cursor.fetchall()]
    
    all_parks = {}
    
    for state in states:
        parks = get_parks_by_state(state)
        if parks:
            all_parks[state] = parks
    
    conn.close()
    return all_parks

def get_park_details(park_code):
    """Get detailed information about a specific park"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get park details
    cursor.execute('SELECT * FROM parks WHERE park_code = ?', (park_code,))
    park = dict(cursor.fetchone() or {})
    
    if park:
        # Get activities for this park
        cursor.execute('''
        SELECT a.activity_name FROM activities a
        JOIN park_activities pa ON a.activity_id = pa.activity_id
        WHERE pa.park_code = ?
        ORDER BY a.activity_name
        ''', (park_code,))
        
        activities = [{'name': row['activity_name']} for row in cursor.fetchall()]
        park['activities'] = activities
        
        # Get states for this park
        cursor.execute('''
        SELECT s.state_code FROM states s
        JOIN state_parks sp ON s.state_code = sp.state_code
        WHERE sp.park_code = ?
        ORDER BY s.state_code
        ''', (park_code,))
        
        states = [row['state_code'] for row in cursor.fetchall()]
        park['states'] = ','.join(states)
        
        # Get multimedia for this park
        cursor.execute('''
        SELECT title, caption, url, credit FROM multimedia WHERE park_code = ?
        ''', (park_code,))
        
        multimedia = [{'title': row['title'], 'caption': row['caption'], 'url': row['url'], 'credit': row['credit']} for row in cursor.fetchall()]
        park['multimedia'] = multimedia
        
        # Get people associated with this park
        cursor.execute('''
        SELECT name, role FROM people WHERE park_code = ?
        ''', (park_code,))
        
        people = [{'name': row['name'], 'role': row['role']} for row in cursor.fetchall()]
        park['people'] = people
    
    conn.close()
    return park


def get_all_designations():
    """Get all unique park designations from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query to get all unique designations
    cursor.execute('SELECT DISTINCT designation FROM parks ORDER BY designation')
    designations = [row['designation'] for row in cursor.fetchall()]
    conn.close()
    
    return designations


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_parks', methods=['GET'])
def fetch_parks():
    state_code = request.args.get('state_code', '').upper()
    parks = get_parks_by_state(state_code)
    return jsonify(parks)

@app.route('/get_all_parks', methods=['GET'])
def fetch_all_parks():
    parks = get_all_parks()
    return jsonify(parks)

@app.route('/get_park_details', methods=['GET'])
def fetch_park_details():
    park_code = request.args.get('park_code')
    park_details = get_park_details(park_code)
    
    if not park_details:
        # Handle case where park_details is empty or doesn't exist
        return "Park not found", 404
    
    return render_template('park_details.html', park=park_details)

@app.route('/get_designations', methods=['GET'])
def fetch_designations():
    designations = get_all_designations()
    return jsonify(designations)

@app.route('/get_parks_by_designation', methods=['GET'])
def fetch_parks_by_designation():
    designation = request.args.get('designation')
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT state_code FROM states ORDER BY state_code')
    states = [row['state_code'] for row in cursor.fetchall()]

    all_parks = {}
    for state in states:
        cursor.execute('''
        SELECT p.* FROM parks p
        JOIN state_parks sp ON p.park_code = sp.park_code
        WHERE sp.state_code = ? AND p.designation = ?
        ORDER BY p.full_name
        ''', (state, designation))
        parks = [dict(row) for row in cursor.fetchall()]
        if parks:
            all_parks[state] = parks

    conn.close()
    return jsonify(all_parks)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
