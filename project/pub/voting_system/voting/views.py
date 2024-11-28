import redis
from django.http import JsonResponse
import os
from django.views.decorators.csrf import csrf_exempt
import json
from dotenv import load_dotenv
import requests
import psycopg2

load_dotenv()

# Function to insert data
def insert_vote_count(city_number, ballotbox_no, partyname, count):
    try:
        conn = psycopg2.connect(**connection_params)
        cur = conn.cursor()
        insert_query = '''
        INSERT INTO vote_counts (city_number, ballotbox_no, partyname, count)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (city_number, ballotbox_no, partyname)
        DO UPDATE SET count = EXCLUDED.count;
        '''
        cur.execute(insert_query, (city_number, ballotbox_no, partyname, count))
        conn.commit()
        print(f"Inserted/Updated record for city_number: {city_number}, ballotbox_no: {ballotbox_no}, partyname: {partyname}")
    except Exception as e:
        print(f"Error inserting record: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def clear_db_utility():
    """Clear the postgreSQL database."""
    conn = psycopg2.connect(**connection_params)
    cur = conn.cursor()

    # Execute the create table query
    cur.execute(create_table_query)
    conn.commit()
    # Execute the create table query
    cur.execute(create_party_table_query)
    conn.commit()

    # Execute the insert query
    cur.execute(insert_parties_query)
    conn.commit()
    
    cur.execute("DELETE FROM vote_counts")
    conn.commit()
    cur.close()
    conn.close()


seeAll_url = os.getenv('SEE_ALL_URL', '1')
seeCities_url = os.getenv('SEE_CITIES_URL', '1')
url = os.getenv('URL', '')
connection_params = {
    'dbname': os.getenv('DB_NAME', ''),
    'user': os.getenv('DB_USER', ''),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', ''),
    'port': os.getenv('DB_PORT', '')
}

# Define the query to create the party table
create_party_table_query = '''
CREATE TABLE IF NOT EXISTS party (
    party_id SERIAL PRIMARY KEY,
    partyname VARCHAR(100) UNIQUE
);
'''

# Define the query to insert party names
insert_parties_query = '''
INSERT INTO party (partyname) VALUES
    ('party1'),
    ('party2'),
    ('party3'),
    ('party4'),
    ('party5'),
    ('party6')
ON CONFLICT (partyname) DO NOTHING;
'''

create_table_query = '''
CREATE TABLE IF NOT EXISTS vote_counts (
    city_number INTEGER,
    ballotbox_no INTEGER,
    partyname VARCHAR(100),
    count INTEGER,
    UNIQUE (city_number, ballotbox_no, partyname)
);
'''

@csrf_exempt
def seeAll(request):
    if request.method == "GET":
        try:
            # Make a GET request to the Google Cloud Function
            response = requests.get('https://get-total-votes-771655325553.us-central1.run.app')
            if response.status_code == 200:
                # Parse the JSON response
                response_data = response.json()
                if response_data is None:
                    return JsonResponse({}, status=200, safe=False)
                return JsonResponse(response_data, status=200,safe=False)
        except requests.exceptions.RequestException as e:
            # Handle errors during the request
            return JsonResponse({"error": str(e)}, status=500)
    else:
        # Return an error for unsupported HTTP methods
        return JsonResponse({"error": "Only GET method is allowed."}, status=405)

@csrf_exempt
def seeCities(request):
    if request.method == "GET":
        try:
            # Make a GET request to the Google Cloud Function
            response = requests.get(seeCities_url)
            if response.status_code == 200:
                # Parse the JSON response
                response_data = response.json()
                print(response_data)
                if response_data is None:
                    return JsonResponse({}, status=200, safe=False)
                return JsonResponse(response_data, status=200,safe=False)
        except requests.exceptions.RequestException as e:
            # Handle errors during the request
            return JsonResponse({"error": str(e)}, status=500)
    else:
        # Return an error for unsupported HTTP methods
        return JsonResponse({"error": "Only GET method is allowed."}, status=405)



@csrf_exempt
def vote(request):
    """
    HTTP endpoint to register votes.
    Expects JSON input: {
    "city_no": 1,
    "box_no": 1,
    "votes": {
        "party1": 74,
        "party2": 181,
        "party3": 8,
        "party4": 20,
        "party5": 11,
        "party6": 6,
        "party7": 0,
        "party8": 0,
        "party9": 0,
        "party10": 0
    },
    "election_size": 1}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        # Parse request data
        data = json.loads(request.body.decode('utf-8'))  
        city_no = data['city_no']
        box_no = data['box_no']
        votes = data['votes']
        election_size = data['election_size']
        count_sum = 0
        for party, count in votes.items():
            count_sum += int(count)
        for party, count in votes.items():
            # Data to send in the request
            data = {
                "city_number": int(city_no),
                "ballotbox_no": int(box_no),
                "partyname": party,
                "count": int(count),
                "election_size": int(election_size),
                "count_sum": count_sum
            }
            insert_vote_count(city_no, box_no, party, count)
            break
            # Sending the POST request
            response = requests.post(url, json=data)

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the JSON response
                response_data = response.json()
                print(data)
                # Check if 'valid' is true or false
                if response_data.get("valid") is True:
                    print("The vote is valid.")
                    insert_vote_count(city_no, box_no, party, count)
                else:
                    print("The vote is invalid.")
            else:
                print("Failed to send POST request:", response.status_code)
                return JsonResponse({'status': 'error', 'message': 'Failed to send POST request.'}, status=500)       
        return JsonResponse({'status': 'success', 'message': 'Votes registered.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def clear_db(request):
    """
    HTTP endpoint to clear the Redis database.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        clear_db_utility()
        return JsonResponse({'status': 'success', 'message': 'Database cleared.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
