import random

from django.contrib import messages
from django.db import transaction
from django.db.models import Max, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from core.models import LottoTicket, LotteryRound, Purchase, WinningResult


def index(request):
	return render(
		request,
		"lotto_admin/index.html",
		{
			"sales_url_name": "lotto_admin:sales_history",
			"draw_url_name": "lotto_admin:draw_lottery",
			"winning_url_name": "lotto_admin:winning_history",
		},
	)


def _next_round_number() -> int:
	latest_round_number = LotteryRound.objects.aggregate(max_no=Max("round_number"))["max_no"]
	return (latest_round_number or 0) + 1


def _create_placeholder_round() -> LotteryRound:
	return LotteryRound.objects.create(
		round_number=_next_round_number(),
		draw_date=timezone.now(),
		win_numbers=[0, 0, 0, 0, 0, 0],
		bonus_number=0,
		is_drawn=False,
	)


def _get_current_round() -> LotteryRound:
	current_round = LotteryRound.objects.filter(is_drawn=False).order_by("-round_number").first()
	if current_round:
		return current_round
	return _create_placeholder_round()


def _draw_numbers() -> tuple[list[int], int]:
	numbers = random.sample(range(1, 46), 7)
	return sorted(numbers[:6]), numbers[6]


def _calculate_rank(ticket_numbers, win_numbers, bonus_number):
	matched_count = len(set(ticket_numbers) & set(win_numbers))
	bonus_matched = bonus_number in ticket_numbers

	if matched_count == 6:
		return WinningResult.Rank.FIRST
	if matched_count == 5 and bonus_matched:
		return WinningResult.Rank.SECOND
	if matched_count == 5:
		return WinningResult.Rank.THIRD
	if matched_count == 4:
		return WinningResult.Rank.FOURTH
	if matched_count == 3:
		return WinningResult.Rank.FIFTH
	return None


def sales_history(request):
	purchases = (
		Purchase.objects.select_related("round")
		.prefetch_related("lottoticket_set")
		.order_by("-purchase_date")
	)
	latest_round = LotteryRound.objects.order_by("-round_number").first()
	total_sales_amount = Purchase.objects.aggregate(total=Sum("purchase_amount"))["total"] or 0

	return render(
		request,
		"lotto_admin/sales_history.html",
		{
			"purchases": purchases,
			"latest_round": latest_round,
			"total_sales_amount": total_sales_amount,
		},
	)


@transaction.atomic
def draw_lottery(request):
	current_round = _get_current_round()

	if request.method == "POST":
		if current_round.is_drawn:
			messages.info(request, "이미 추첨이 완료된 회차입니다.")
			return redirect("lotto_admin:draw_lottery")

		win_numbers, bonus_number = _draw_numbers()
		current_round.win_numbers = win_numbers
		current_round.bonus_number = bonus_number
		current_round.is_drawn = True
		current_round.draw_date = timezone.now()
		current_round.save()

		tickets = LottoTicket.objects.filter(purchase__round=current_round).select_related("purchase")
		winning_results = []
		for ticket in tickets:
			rank = _calculate_rank(ticket.numbers, win_numbers, bonus_number)
			winning_results.append(WinningResult(ticket=ticket, rank=rank))
		WinningResult.objects.bulk_create(winning_results)

		_create_placeholder_round()
		messages.success(request, f"{current_round.round_number}회차 추첨이 완료되었습니다.")
		return redirect("lotto_admin:draw_lottery")

	latest_drawn_round = LotteryRound.objects.filter(is_drawn=True).order_by("-round_number").first()
	latest_winning_results = (
		WinningResult.objects.select_related("ticket", "ticket__purchase", "ticket__purchase__round")
		.order_by("-id")[:50]
	)

	return render(
		request,
		"lotto_admin/draw_lottery.html",
		{
			"current_round": current_round,
			"latest_drawn_round": latest_drawn_round,
			"latest_winning_results": latest_winning_results,
		},
	)


def winning_history(request):
	winning_results = (
		WinningResult.objects.select_related("ticket", "ticket__purchase", "ticket__purchase__round")
		.order_by("-id")
	)

	return render(
		request,
		"lotto_admin/winning_history.html",
		{
			"winning_results": winning_results,
		},
	)
