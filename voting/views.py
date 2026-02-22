from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Sum
from django_ratelimit.decorators import ratelimit
import hashlib
import csv

from elections.models import Position, Candidate
from users.decorators import admin_required
from .models import VoterToken, ManagerToken, Vote


# =========================
# ADMIN STATISTICS
# =========================
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.decorators import admin_required
from elections.models import Position, Candidate
from voting.models import Vote, VoterToken

@login_required
@admin_required
def admin_statistics_page(request):
    # Overall statistics
    total_votes = Vote.objects.count()
    total_tokens = VoterToken.objects.count()
    used_tokens = VoterToken.objects.filter(is_active=False).count()
    turnout = round((used_tokens / total_tokens) * 100, 2) if total_tokens > 0 else 0

    # Positions and candidates
    positions_data = []
    for position in Position.objects.all():
        candidates = Candidate.objects.filter(position=position).order_by('-vote_count')
        total_position_votes = sum(c.vote_count for c in candidates)
        positions_data.append({
            "position": position.name,
            "total_votes": total_position_votes,
            "candidates": [
                {"name": c.name, "votes": c.vote_count} for c in candidates
            ]
        })

    return render(request, "admin_statistics.html", {
        "total_votes": total_votes,
        "turnout_percentage": turnout,
        "used_tokens": used_tokens,
        "total_tokens": total_tokens,
        "positions": positions_data,
    })



# =========================
# MANAGER LIVE STATS
# =========================

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

    percentage = (
        (candidate.vote_count / total_votes_position) * 100
        if total_votes_position > 0 else 0
    )

    # Ranking
    ranked_candidates = Candidate.objects.filter(
        position=position
    ).order_by('-vote_count')

    ranking = 1
    for idx, c in enumerate(ranked_candidates, start=1):
        if c.id == candidate.id:
            ranking = idx
            break

    leader = ranked_candidates.first()
    leader_votes = leader.vote_count if leader else 0
    vote_diff = max(leader_votes - candidate.vote_count, 0)

    return JsonResponse({
        "votes": candidate.vote_count,
        "percentage": round(percentage, 2),
        "ranking": ranking,
        "vote_diff": vote_diff,
        "leader_votes": leader_votes
    })


# =========================
# TOKEN GENERATION (ADMIN)
# =========================
@login_required
@admin_required
def admin_statistics_data(request):

    total_votes = Vote.objects.count()
    total_tokens = VoterToken.objects.count()
    used_tokens = VoterToken.objects.filter(is_active=False).count()

    turnout = round((used_tokens / total_tokens) * 100, 2) if total_tokens > 0 else 0

    positions_data = []

    for position in Position.objects.all():

        candidates = Candidate.objects.filter(
            position=position
        ).order_by('-vote_count')

        total_position_votes = sum(c.vote_count for c in candidates)

        positions_data.append({
            "position": position.name,
            "total_votes": total_position_votes,
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
        "turnout_percentage": turnout,
        "used_tokens": used_tokens,
        "total_tokens": total_tokens,
        "positions": positions_data
    })

@login_required
@admin_required
def admin_tokens(request):

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

            request.session["generated_tokens"] = generated_tokens

        # Generate manager token
        if "generate_manager" in request.POST:
            candidate_id = request.POST.get("candidate")
            candidate = Candidate.objects.get(id=candidate_id)

            raw, token_hash = ManagerToken.generate_token()
            ManagerToken.objects.create(
                token_hash=token_hash,
                candidate=candidate
            )

            manager_token = raw

    return render(request, "admin_tokens.html", {
        "positions": positions,
        "candidates": candidates,
        "generated_tokens": generated_tokens,
        "manager_token": manager_token
    })


# =========================
# EXPORT TOKENS
# =========================

@login_required
@admin_required
def export_tokens(request):

    tokens = request.session.get("generated_tokens", [])

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="voter_tokens.csv"'

    writer = csv.writer(response)
    writer.writerow(["Voter Tokens"])

    for token in tokens:
        writer.writerow([token])

    return response


# =========================
# VOTER LOGIN
# =========================

@ratelimit(key='ip', rate='5/m', block=True)
def home(request):

    if request.method == "POST":
        raw_token = request.POST.get("token")
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        try:
            token = VoterToken.objects.get(
                token_hash=token_hash,
                is_active=True
            )
            request.session["token_hash"] = token_hash
            return redirect("vote")

        except VoterToken.DoesNotExist:
            return render(request, "home.html", {
                "error": "Invalid or used token"
            })

    return render(request, "home.html")


# =========================
# VOTING PAGE
# =========================

def vote(request):

    token_hash = request.session.get("token_hash")

    if not token_hash:
        return redirect("home")

    try:
        token = VoterToken.objects.get(
            token_hash=token_hash,
            is_active=True
        )
    except VoterToken.DoesNotExist:
        return redirect("home")

    positions = token.allowed_positions.all()

    if request.method == "POST":
        with transaction.atomic():
            for position in positions:
                candidate_id = request.POST.get(f"position_{position.id}")
                if candidate_id:
                    Vote.objects.create(
                        token=token,
                        position=position,
                        candidate_id=candidate_id
                    )

                    Candidate.objects.filter(id=candidate_id).update(
                        vote_count=F("vote_count") + 1
                    )

            token.is_active = False
            token.save()

        return redirect("home")

    return render(request, "vote.html", {
        "positions": positions
    })