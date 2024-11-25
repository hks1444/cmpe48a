import redis
import psycopg2
from psycopg2 import sql
import requests
from dotenv import load_dotenv
import os
load_dotenv()

redis_client = redis.StrictRedis(host=os.getenv("REDIS_HOST",""), port=os.getenv("REDIS_PORT",6379), db=os.getenv("REDIS_DB",0))
channel = os.getenv("REDIS_CHANNEL","")
pubsub = redis_client.pubsub()
pubsub.subscribe(channel)

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

conn = psycopg2.connect(**connection_params)
cur = conn.cursor()

try:
    # Execute the create table query
    cur.execute(create_table_query)
    conn.commit()
    # Execute the create table query
    cur.execute(create_party_table_query)
    conn.commit()

    # Execute the insert query
    cur.execute(insert_parties_query)
    conn.commit()

    print("Tables created and populated successfully.")
except Exception as e:
    print(f"Error creating party table: {e}")

# Function to insert data
def insert_vote_count(city_number, ballotbox_no, partyname, count):
    try:
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

def clear_db():
    """Clear the postgreSQL database."""
    cur.execute("DELETE FROM vote_counts")
    conn.commit()
    print("Database cleared.")

def insert_vote(data):
    """Insert a new vote into the Redis database."""
    votes = data.split("=")[1]
    votes = votes.split(",")
    count_sum = 0
    for vote in votes:
        election_size, city_no, box_no, party, count = vote.split(":")
        count_sum += int(count)
    for vote in votes:
        election_size, city_no, box_no, party, count = vote.split(":")
        # Data to send in the request
        data = {
            "city_number": int(city_no),
            "ballotbox_no": int(box_no),
            "partyname": party,
            "count": int(count),
            "election_size": int(election_size),
            "count_sum": count_sum
        }

        # Sending the POST request
        response = requests.post(url, json=data)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            response_data = response.json()
            print(data)
            # Check if 'valid' is true or false
            if response_data.get("valid") is True:
                insert_vote_count(city_no, box_no, party, count)
                print("The vote is valid.")
            else:
                print("The vote is invalid.")
        else:
            print("Failed to send POST request:", response.status_code)

print(f"Subscribed to {channel}. Waiting for messages...")

for message in pubsub.listen():
    if message['type'] == 'message':
        data = message['data'].decode('utf-8')
        
        if data == "clear_db":
            clear_db()
        
        elif data.startswith("vote"):
            insert_vote(data)
        else:
            break

cur.close()
conn.close()
