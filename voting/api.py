from rest_framework.decorators import api_view
from rest_framework.response import Response
from elections.models import Candidate

@api_view(["GET"])
def stats(request, position_id):
    candidates = Candidate.objects.filter(position_id=position_id)
    total = sum(c.vote_count for c in candidates)

    data = []
    for c in candidates:
        percent = (c.vote_count / total * 100) if total > 0 else 0
        data.append({
            "name": c.name,
            "votes": c.vote_count,
            "percent": round(percent, 2)
        })

    return Response(data)