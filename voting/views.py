from django.shortcuts import render
import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from elections.models import Position, Candidate
from .models import VoterToken, ManagerToken
from django.shortcuts import render, redirect
from users.decorators import admin_required
from .models import VoterToken
from elections.models import Position

# Create your views here.
import hashlib
from django.shortcuts import render, redirect
from django.db import transaction
from django.db.models import F
from django_ratelimit.decorators import ratelimit
from .models import VoterToken, Vote
from elections.models import Position, Candidate
from django.db.models import Count
from django.db.models.functions import TruncHour
from django.http import JsonResponse
from .models import Vote
from elections.models import Candidate
from django.db.models import Count
from django.http import JsonResponse
from voting.models import Vote, ManagerToken
from elections.models import Candidate, Position

def admin_statistics(request):

    total_votes = Vote.objects.count()
    total_tokens = ManagerToken.objects.count()
    used_tokens = ManagerToken.objects.filter(is_active=True).count()

    positions_data = []

    for position in Position.objects.all():
        candidates = Candidate.objects.filter(position=position).annotate(
            total_votes=Count('vote')
        ).order_by('-vote_count')

        positions_data.append({
            "position": position.name,
            "candidates": [
                {
                    "name": c.name,
                    "votes": c.vote_count
                }
                for c in candidates
            ]
        })

    return JsonResponse({
        "total_votes": total_votes,
        "turnout_percentage": round((used_tokens / total_tokens) * 100, 2) if total_tokens else 0,
        "positions": positions_data
    })

def manager_live_stats(request):
    candidate = request.user.candidate

    total_votes = Vote.objects.filter(
        candidate__position=candidate.position
    ).count()

    candidate_votes = Vote.objects.filter(
        candidate=candidate
    ).count()

    percentage = round((candidate_votes / total_votes) * 100, 2) if total_votes > 0 else 0

    candidates_with_votes = Candidate.objects.filter(
        position=candidate.position
    ).annotate(
        vote_count=Count('vote_set')   # <-- THIS IS THE FIX
    ).order_by('-vote_count')

    ranking = 1
    for idx, c in enumerate(candidates_with_votes, start=1):
        if c.id == candidate.id:
            ranking = idx
            break

    leader = candidates_with_votes.first()
    leader_votes = leader.vote_count if leader else 0

    vote_diff = max(leader_votes - candidate_votes, 0)

    return JsonResponse({
        "votes": candidate_votes,
        "percentage": percentage,
        "ranking": ranking,
        "vote_diff": vote_diff,
        "leader_votes": leader_votes
    })
@login_required
@login_required
def admin_tokens(request):

    if request.user.role != "ADMIN":
        return redirect("home")

    positions = Position.objects.all()
    candidates = Candidate.objects.all()

    generated_tokens = []
    manager_token = None

    if request.method == "POST":

        # Generate voter tokens
        if "generate_voters" in request.POST:
            quantity = int(request.POST.get("voter_quantity", 1))
            selected_positions = request.POST.getlist("positions")

            for _ in range(quantity):
                raw, token_hash = VoterToken.generate_token()
                token = VoterToken.objects.create(token_hash=token_hash)

                if request.POST.get("all_positions"):
                    token.allowed_positions.set(Position.objects.all())
                else:
                    token.allowed_positions.set(selected_positions)

            generated_tokens.append(raw)

        # Generate manager token
        if "generate_manager" in request.POST:
            candidate_id = request.POST.get("candidate")
            candidate = Candidate.objects.get(id=candidate_id)

    # get quantity safely
            quantity =1

            for _ in range(quantity):
                raw, token_hash = ManagerToken.generate_token()
                ManagerToken.objects.create(
                    token_hash=token_hash,
                    candidate=candidate)

            manager_token = raw

    return render(request, "admin_tokens.html", {
        "positions": positions,
        "candidates": candidates,
        "generated_tokens": generated_tokens,
        "manager_token": manager_token
    })


@login_required
def export_tokens(request):
    tokens = request.session.get("generated_tokens", [])

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="voter_tokens.csv"'

    writer = csv.writer(response)
    writer.writerow(["Voter Tokens"])

    for token in tokens:
        writer.writerow([token])

    return response
@ratelimit(key='ip', rate='5/m', block=True)
def home(request):
    if request.method == "POST":
        raw_token = request.POST.get("token")
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        try:
            token = VoterToken.objects.get(token_hash=token_hash, is_active=True)
            request.session["token_hash"] = token_hash
            return redirect("vote")
        except:
            return render(request, "home.html", {"error": "Invalid or used token"})
    return render(request, "home.html")

def vote(request):
    token_hash = request.session.get("token_hash")
    token = VoterToken.objects.get(token_hash=token_hash, is_active=True)

    positions = token.allowed_positions.all()
    print("TOKEN:", token)
    print("ALLOWED:", token.allowed_positions.all())

    if request.method == "POST":
        with transaction.atomic():
            for position in positions:
                candidate_id = request.POST.get(f"position_{position.id}")
                if candidate_id:
                    Vote.objects.create(position=position, candidate_id=candidate_id)
                    Candidate.objects.filter(id=candidate_id).update(
                        vote_count=F("vote_count") + 1
                    )
            token.is_active = False
            token.save()
            

        return redirect("home")

    return render(request, "vote.html", {"positions": positions})
from django.http import JsonResponse
from django.db.models import Sum
from .models import ManagerToken
from elections.models import Candidate


def manager_live_stats(request):
    token_hash = request.session.get("manager_token")

    if not token_hash:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        token = ManagerToken.objects.get(
            token_hash=token_hash,
            is_active=True
        )
    except ManagerToken.DoesNotExist:
        return JsonResponse({"error": "Invalid token"}, status=403)

    candidate = token.candidate
    position = candidate.position

    total_votes_position = Candidate.objects.filter(
        position=position
    ).aggregate(total=Sum("vote_count"))["total"] or 0

    percentage = 0
    if total_votes_position > 0:
        percentage = (candidate.vote_count / total_votes_position) * 100

    return JsonResponse({
        "votes": candidate.vote_count,
        "percentage": round(percentage, 2)
    })