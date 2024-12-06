import redis
from django.http import JsonResponse
import os
from django.views.decorators.csrf import csrf_exempt
import json
from dotenv import load_dotenv
import requests

load_dotenv()


redis_channel = os.getenv('REDIS_CHANNEL', '1')
redis_host = os.getenv('REDIS_HOST', '1')
redis_port = int(os.getenv('REDIS_PORT', 1))
seeAll_url = os.getenv('SEE_ALL_URL', '1')
seeCities_url = os.getenv('SEE_CITIES_URL', '1')
redis_db = 0
# Connect to Redis
redis_client = redis.StrictRedis(
    host = redis_host,
    port = redis_port,
    db = redis_db,
)
@csrf_exempt
def seeAll(request):
    if request.method == "GET":
        try:
            # Make a GET request to the Google Cloud Function
            response = requests.get(seeAll_url)
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
        channel = redis_channel
        results_list = []
        results_string = ""
        # Publish votes to Redis
        for party, count in votes.items():
            vote = f"{election_size}:{city_no}:{box_no}:{party}:{count}"
            results_list.append(vote)
        results_string = ",".join(results_list)
        redis_client.publish(channel, f"votes={results_string}")

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
        channel = redis_channel
        redis_client.publish(channel, "clear_db")
        return JsonResponse({'status': 'success', 'message': 'Database cleared.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
