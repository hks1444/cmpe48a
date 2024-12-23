import requests
import random
import time
import json

BASE_URL = 'http://34.110.171.4/voting/'

VOTING_URL = f'{BASE_URL}vote/'
CLEAR_DB_URL = f'{BASE_URL}clear-db/'
SEE_ALL_URL = f'{BASE_URL}see-all/'
SEE_CITIES_URL = f'{BASE_URL}see-cities/'

def send_vote(election_size, city_no, box_no):
    """
    Generate and send random votes for a ballot box
    """
    # Generate random votes for parties
    votes = {}
    remaining_votes = random.randint(100, 400)
    parties = ['party1', 'party2', 'party3', 'party4', 'party5']
    
    for i, party in enumerate(parties):
        if i == len(parties) - 1:
            votes[party] = remaining_votes
        else:
            vote_count = random.randint(1, max(2, remaining_votes - (len(parties) - i)))
            votes[party] = vote_count
            remaining_votes -= vote_count

    data = {
        "city_no": city_no,
        "box_no": box_no,
        "votes": votes,
        "election_size": election_size
    }

    print(f"\nSending vote: {json.dumps(data, indent=2)}")
    try:
        response = requests.post(VOTING_URL, json=data)
        print(f"Response: {response.status_code}, {response.json()}")
    except Exception as e:
        print(f"Error: {str(e)}")

def clear_db():
    """Clear the database"""
    print("\nClearing database...")
    try:
        response = requests.post(CLEAR_DB_URL)
        print(f"Response: {response.status_code}, {response.json()}")
    except Exception as e:
        print(f"Error: {str(e)}")

def see_all():
    """Get all votes"""
    print("\nGetting all votes...")
    try:
        response = requests.get(SEE_ALL_URL)
        print(f"Response: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

def see_cities():
    """Get city totals"""
    print("\nGetting city totals...")
    try:
        response = requests.get(SEE_CITIES_URL)
        print(f"Response: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

def simulate_election():
    """Run a complete election simulation"""
    # Clear existing data
    clear_db()
    time.sleep(1)

    # Simulate votes for 3 cities, 5 boxes each
    for city_no in range(1, 4):
        for box_no in range(1, 6):
            send_vote(1, city_no, box_no)
            time.sleep(0.5)  # Wait between votes

    # Check results
    see_all()
    see_cities()

if __name__ == "__main__":
    print("Starting election simulation...")
    simulate_election()