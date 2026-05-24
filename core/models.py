from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField
# Create your models here.
class LotteryRound(models.Model):
    round_number = models.IntegerField(unique=True)
    draw_date = models.DateTimeField()
    win_numbers = ArrayField(models.IntegerField(), size=6)
    bonus_number = models.IntegerField()
    is_drawn = models.BooleanField(default=False)

    def __str__(self):
        return f"Round {self.round_number} - {self.draw_date}"
    
class Purchase(models.Model):
    round = models.ForeignKey(LotteryRound, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    purchase_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Purchase for Round {self.round.round_number} - {self.purchase_date}"

class LottoTicket(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    ticket_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    numbers = ArrayField(models.IntegerField(), size=6)

    def __str__(self):
        return f"Ticket {self.ticket_number} for Purchase {self.purchase.id}"   

class WinningResult(models.Model):
    ticket = models.OneToOneField(LottoTicket, on_delete=models.CASCADE)
    class Rank(models.IntegerChoices):
        FIRST = 1, "1등"
        SECOND = 2, "2등"
        THIRD = 3, "3등"
        FOURTH = 4, "4등"
        FIFTH = 5, "5등"
    rank = models.IntegerField(choices=Rank.choices, null=True, blank=True)

    def __str__(self):
        return f"Winning Result for Ticket {self.ticket.ticket_number}"
