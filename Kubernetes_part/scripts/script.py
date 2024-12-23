import requests
import random
import time
BASE_URL = 'http://127.0.0.1:8000/voting/'
# URL of the Django server (update as needed)
VOTING_URL = f'{BASE_URL}vote/'
CLEAR_DB_URL = f'{BASE_URL}clear-db/'
SEE_ALL_URL = f'{BASE_URL}see-all/'
SEE_CITIES_URL = f'{BASE_URL}see-cities/'

def send_vote(election_size, city_no, box_no, party_votes):
    """
    Send a vote request to the Django server.
    """
    data = {
        "city_no": city_no,
        "box_no": box_no,
        "votes": party_votes,
        "election_size": election_size
    }
    print(f"Sending vote: {data}")
    response = requests.post(VOTING_URL, json=data)
    print(f"Response: {response.status_code}, {response.json()}")

def clear_db():
    """
    Clear the database.
    """
    response = requests.post(CLEAR_DB_URL)
    print(f"Response: {response.status_code}, {response.json()}")

def see_all():
    """
    Get all votes from the database.
    """
    response = requests.get(SEE_ALL_URL)
    print(f"Response: {response.status_code}, {response.json()}")

def see_cities():
    """
    Get all cities from the database.
    """
    response = requests.get(SEE_CITIES_URL)
    print(f"Response: {response.status_code}, {response.json()}")


def simulate_election(election_size):
    box_number = 100
    if election_size == 1:
        box_number = 10
    elif election_size == 2:
        box_number = 1000
    elif election_size == 3:
        box_number = 10000
    for city_no in range(1, 2):
        for box_no in range(1, box_number+1):
            dict = {}
            number_of_votes = random.randint(1, 450)
            for party in ['party1', 'party2', 'party3', 'party4', 'party5', 'party6', 'party7', 'party8', 'party9', 'party10']:
                if number_of_votes > 1:
                    dict[party] = random.randint(1, number_of_votes)
                else:
                    dict[party] = 0
                number_of_votes -= dict[party]
            send_vote(election_size, city_no, box_no, dict)


if __name__ == '__main__':
    #time.sleep(10)
    clear_db()
    time.sleep(10)
    simulate_election(1)
    for i in range(1, 10):
        time.sleep(10)
        see_all()
        see_cities()
    
