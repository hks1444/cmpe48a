import redis
from django.http import JsonResponse, HttpResponse 
import os
from django.views.decorators.csrf import csrf_exempt
import json
from dotenv import load_dotenv
import requests

load_dotenv()

class VoteStorage:
    def __init__(self):
        self.redis = redis.Redis(host='redis', port=6379, db=0)

    def add_vote(self, city_no, box_no, votes, election_size):
        pipe = self.redis.pipeline()
        vote_key = f"votes:{city_no}:{box_no}"
        pipe.hmset(vote_key, votes)
        
        for party, count in votes.items():
            pipe.hincrby("total_votes", party, int(count))
            pipe.hincrby(f"city:{city_no}", party, int(count))
        
        pipe.execute()

    def get_all_votes(self):
        vote_keys = self.redis.keys("votes:*")
        votes = {}
        
        for key in vote_keys:
            city, box = key.decode().split(":")[1:]
            if city not in votes:
                votes[city] = {}
            votes[city][box] = {k.decode(): v.decode() for k, v in self.redis.hgetall(key).items()}
            
        total_votes = {k.decode(): v.decode() for k, v in self.redis.hgetall("total_votes").items()}
        
        return {
            "votes": votes,
            "total_votes": total_votes
        }

    def get_cities(self):  # Added missing method
        city_keys = self.redis.keys("city:*")
        cities = {}
        
        for key in city_keys:
            city_no = key.decode().split(":")[1]
            city_votes = {k.decode(): v.decode() for k, v in self.redis.hgetall(key).items()}
            cities[city_no] = sum(int(count) for count in city_votes.values())
            
        return cities

    def clear_db(self):
        self.redis.flushall()


redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = int(os.getenv('REDIS_PORT', 6379))
vote_storage = VoteStorage()

@csrf_exempt
def health_check(request):
    return HttpResponse("OK")

@csrf_exempt
def seeAll(request):
    if request.method == "GET":
        try:
            data = vote_storage.get_all_votes()
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Only GET method is allowed."}, status=405)

@csrf_exempt
def seeCities(request):
    if request.method == "GET":
        try:
            data = vote_storage.get_cities()
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Only GET method is allowed."}, status=405)

@csrf_exempt
def vote(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        city_no = data['city_no']
        box_no = data['box_no']
        votes = data['votes']
        election_size = data['election_size']
        
        vote_storage.add_vote(city_no, box_no, votes, election_size)
        return JsonResponse({'status': 'success', 'message': 'Votes registered.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def clear_db(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        vote_storage.clear_db()
        return JsonResponse({'status': 'success', 'message': 'Database cleared.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)