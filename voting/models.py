# Create your models here.
import hashlib
import secrets
from django.db import models
from elections.models import Position, Candidate



class VoterToken(models.Model):
    token_hash = models.CharField(max_length=64, unique=True)
    allowed_positions = models.ManyToManyField(Position)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token_hash
    def generate_token():
        import secrets, hashlib
        raw = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        return raw, token_hash

class Vote(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
class ManagerToken(models.Model):
    token_hash = models.CharField(max_length=64, unique=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_token():
        import secrets, hashlib
        raw = secrets.token_hex(16)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        return raw, token_hash

    def __str__(self):
        return f"ManagerToken for {self.candidate.name}"