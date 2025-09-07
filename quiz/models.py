from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capital = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)  # например: Europe, Asia

    def __str__(self):
        return f"{self.name} — {self.capital}"


class QuizRun(models.Model):
    DIRECTION_CHOICES = [
        ('c2cap', 'Страна → Столица'),
        ('cap2c', 'Столица → Страна'),
    ]
    created_at = models.DateTimeField(auto_now_add=True)
    direction = models.CharField(max_length=6, choices=DIRECTION_CHOICES)
    total = models.IntegerField(default=10)
    correct = models.IntegerField(default=0)
    region = models.CharField(max_length=100, blank=True)


class Attempt(models.Model):
    quiz = models.ForeignKey(QuizRun, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    user_answer = models.CharField(max_length=100)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
