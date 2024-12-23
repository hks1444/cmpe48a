# Publisher file with Redis connection and voting functions

import redis

# Connect to local Redis instance
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
channel = 'my_channel'

def clear_db():
    """Clear the Redis database."""
    redis_client.publish(channel, "clear_db")
    print("Database cleared.")

def vote(city_no, box_no, votes):
    """Register votes for each party in a specific city and box number using a Redis hash."""
    for party, count in votes.items():
        key = f"{city_no}:{box_no}:{party}"
        redis_client.publish(channel, f"votes={key},{count}")  # Notify subscriber of new vote

# Clear database and cast a vote
# clear_db()
votes = {"party1": 20, "party2": 330, "party3": 10}
vote(4, 2, votes)
