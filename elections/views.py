from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum
from .models import Position, Candidate
from voting.models import ManagerToken, Vote
from users.decorators import admin_required

from django.http import JsonResponse
from django.db.models import Count
# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from elections.models import Position, Candidate
from django.db.models import Sum

@login_required
@admin_required
def admin_dashboard(request):

    positions = Position.objects.all()
    candidates = Candidate.objects.all()

    # LIVE SUMMARY
    total_votes = Vote.objects.count()

    candidate_summary = Candidate.objects.annotate(
        manager_count=Count("managertoken")
    )

    if request.method == "POST":

        # CREATE POSITION
        if "create_position" in request.POST:
            name = request.POST.get("position_name")
            if name:
                Position.objects.create(name=name)

        # DELETE POSITION
        if "delete_position" in request.POST:
            position_id = request.POST.get("delete_position")
            Position.objects.filter(id=position_id).delete()

        # CREATE CANDIDATE
        if "create_candidate" in request.POST:
            name = request.POST.get("candidate_name")
            position_id = request.POST.get("candidate_position")
            photo = request.FILES.get("candidate_photo")

            if name and position_id:
                Candidate.objects.create(
                    name=name,
                    position_id=position_id,
                    photo=photo
                )

        # EDIT CANDIDATE
        if "edit_candidate" in request.POST:
            candidate_id = request.POST.get("candidate_id")
            candidate = get_object_or_404(Candidate, id=candidate_id)

            candidate.name = request.POST.get("candidate_name")
            candidate.position_id = request.POST.get("candidate_position")

            if request.FILES.get("candidate_photo"):
                candidate.photo = request.FILES.get("candidate_photo")

            candidate.save()

        return redirect("admin_dashboard")

    return render(request, "admin_dashboard.html", {
        "positions": positions,
        "candidates": candidate_summary,
        "total_votes": total_votes
    })
@admin_required
def admin_live_summary(request):
    total_votes = Vote.objects.count()

    leaders = []

    positions = Position.objects.all()
    for position in positions:
        candidates = Candidate.objects.filter(position=position).annotate(
            vote_count=Count("vote")
        ).order_by("-vote_count")

        if candidates.exists():
            leader = candidates.first()
            leaders.append({
                "position": position.name,
                "leader": leader.name,
                "votes": leader.vote_count
            })

    return JsonResponse({
        "total_votes": total_votes,
        "leaders": leaders
    })

from django.shortcuts import redirect

from django.db.models import Sum


def manager_dashboard(request):
    token_hash = request.session.get("manager_token")

    if not token_hash:
        return redirect("manager_login")

    try:
        token = ManagerToken.objects.get(
            token_hash=token_hash,
            is_active=True
        )
    except ManagerToken.DoesNotExist:
        return redirect("manager_login")

    candidate = token.candidate
    position = candidate.position

    candidates = Candidate.objects.filter(position=position).order_by("-vote_count")

    total_votes = candidates.aggregate(total=Sum("vote_count"))["total"] or 0

    # Calculate ranking
    ranking = list(candidates).index(candidate) + 1
    total_candidates = candidates.count()

    percentage = 0
    if total_votes > 0:
        percentage = (candidate.vote_count / total_votes) * 100

    return render(request, "manager_dashboard.html", {
        "candidate": candidate,
        "votes": candidate.vote_count,
        "percentage": round(percentage, 2),
        "ranking": ranking,
        "total_candidates": total_candidates
    })