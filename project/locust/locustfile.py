from locust import HttpUser, task, between
import random
import json
from threading import Lock

# Shared counter and lock
current_i = 1
lock = Lock()

class VotingUser(HttpUser):
    wait_time = between(1, 3)
    
    # def on_start(self):
    #     """Clear DB when test starts"""
    #     self.client.post("/voting/clear-db/")

    def _simulate_election(self, election_size, box_number, city_no):
        """
        Helper method to simulate an election
        """
        votes = {}
        number_of_votes = random.randint(1, 450)
        
        # Generate random votes for each party
        for party in [f'party{i}' for i in range(1, 8)]:
            if number_of_votes > 1:
                votes[party] = random.randint(1, number_of_votes)
            else:
                votes[party] = 0
            number_of_votes -= votes[party]

        # Prepare data payload
        data = {
            "city_no": city_no,
            "box_no": box_number,
            "votes": votes,
            "election_size": election_size,
        }

        # Send vote
        self.client.post(
            "/voting/vote/",
            json=data,
            headers={'Content-Type': 'application/json'}
        )

class QuickTestUser(VotingUser):
    """
    A user class for quick testing with smaller numbers
    """
    @task
    def simulate_quick_test(self):
        global current_i
        
        # Lock to ensure each user gets a unique `i`
        with lock:
            i = current_i
            current_i += 1
            if current_i > 81:  # Stop after 80 iterations
                current_i = 1  # Optionally, wrap around
        
        # Perform tasks with the assigned `i`
        self._simulate_election(1, 1, i)
        self.view_all_votes()
        self.view_cities()

    def view_all_votes(self):
        """View all votes"""
        self.client.get("/voting/see-all/")

    def view_cities(self):
        """View cities"""
        self.client.get("/voting/see-cities/")
