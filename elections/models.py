# Create your models here.
from django.db import models
from users.models import User

class Position(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Candidate(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to="candidates/")
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    vote_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name