from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models, transaction
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Models
class Party(models.Model):
    party_id = models.AutoField(primary_key=True)
    partyname = models.CharField(max_length=100, unique=True)

class VoteCount(models.Model):
    city_number = models.IntegerField()
    ballotbox_no = models.IntegerField()
    partyname = models.CharField(max_length=100)
    count = models.IntegerField()

    class Meta:
        unique_together = ('city_number', 'ballotbox_no', 'partyname')

def isValidVote(city_number, ballotbox_no, partyname, count, count_sum, election_size):
    try:
        # Check validation conditions
        if election_size == 1:
            if ballotbox_no < 1 or ballotbox_no > 1000:
                return False
        elif election_size == 2:
            if ballotbox_no < 1 or ballotbox_no > 10000:
                return False
        elif election_size == 3:
            if ballotbox_no < 1 or ballotbox_no > 100000:
                return False
        else:
            return False
        
        if city_number < 1 or city_number > 81:
            return False
        if count_sum > 400 or count_sum < count:
            return False

        # Check if party exists
        party_exists = Party.objects.filter(partyname=partyname).exists()
        if not party_exists:
            return False

        return True
    except Exception as e:
        print(f"Error validating vote: {e}")
        return False

def insert_vote_count(city_number, ballotbox_no, partyname, count):
    try:
        VoteCount.objects.update_or_create(
            city_number=city_number,
            ballotbox_no=ballotbox_no,
            partyname=partyname,
            defaults={'count': count}
        )
        print(f"Inserted/Updated record for city_number: {city_number}, ballotbox_no: {ballotbox_no}, partyname: {partyname}")
    except Exception as e:
        print(f"Error inserting record: {e}")
        raise e

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
        
        count_sum = sum(int(count) for count in votes.values())

        with transaction.atomic():
            for party, count in votes.items():
                if isValidVote(city_no, box_no, party, int(count), count_sum, election_size):
                    insert_vote_count(city_no, box_no, party, int(count))
                else:
                    return JsonResponse({'status': 'error', 'message': 'Invalid vote data'}, status=400)

        return JsonResponse({'status': 'success', 'message': 'Votes registered.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def seeAll(request):
    if request.method == "GET":
        try:
            votes = VoteCount.objects.all()
            
            # Structure the response
            votes_by_location = {}
            total_votes = {}
            
            for vote in votes:
                # Initialize dictionaries if they don't exist
                if str(vote.city_number) not in votes_by_location:
                    votes_by_location[str(vote.city_number)] = {}
                if str(vote.ballotbox_no) not in votes_by_location[str(vote.city_number)]:
                    votes_by_location[str(vote.city_number)][str(vote.ballotbox_no)] = {}
                
                # Add votes to structure
                votes_by_location[str(vote.city_number)][str(vote.ballotbox_no)][vote.partyname] = vote.count
                
                # Update total votes
                if vote.partyname not in total_votes:
                    total_votes[vote.partyname] = 0
                total_votes[vote.partyname] += vote.count
            
            response_data = {
                'votes': votes_by_location,
                'total_votes': total_votes
            }
            return JsonResponse(response_data, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Only GET method is allowed."}, status=405)

@csrf_exempt
def seeCities(request):
    if request.method == "GET":
        try:
            from django.db.models import Sum
            cities_data = {}
            
            city_totals = VoteCount.objects.values('city_number').annotate(
                total=Sum('count')
            )
            
            for city in city_totals:
                cities_data[str(city['city_number'])] = city['total']
            
            return JsonResponse(cities_data, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Only GET method is allowed."}, status=405)

@csrf_exempt
def clear_db(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        with transaction.atomic():
            VoteCount.objects.all().delete()
            # Initialize parties
            default_parties = ['party1', 'party2', 'party3', 'party4', 'party5', 'party6']
            for party_name in default_parties:
                Party.objects.get_or_create(partyname=party_name)
        return JsonResponse({'status': 'success', 'message': 'Database cleared and parties initialized.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def health_check(request):
    return JsonResponse({"status": "healthy"})