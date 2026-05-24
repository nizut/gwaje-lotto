from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.models import LotteryRound, LottoTicket, Purchase
from .forms import PurchaseForm
from .services import create_purchase


def _calculate_rank(ticket_numbers, win_numbers, bonus_number):
    matched_count = len(set(ticket_numbers) & set(win_numbers))
    bonus_matched = bonus_number in ticket_numbers

    if matched_count == 6:
        return 1
    if matched_count == 5 and bonus_matched:
        return 2
    if matched_count == 5:
        return 3
    if matched_count == 4:
        return 4
    if matched_count == 3:
        return 5
    return None

def index(request):
    latest_round = LotteryRound.objects.order_by('-round_number').first()
    return render(request, 'user/index.html', {'latest_round': latest_round})


def purchase(request):
    allowed_modes = {"manual", "semi", "auto"}
    mode = request.GET.get("mode", "manual")
    if mode not in allowed_modes:
        mode = "manual"

    if request.method == "POST":
        mode = request.POST.get("mode", "manual")
        if mode not in allowed_modes:
            mode = "manual"

        form = PurchaseForm(request.POST)
        if form.is_valid():
            numbers = form.cleaned_data["numbers"]
            quantity = form.cleaned_data["quantity"]

            try:
                purchase_obj, _tickets = create_purchase(
                    mode=mode,
                    numbers=numbers,
                    quantity=quantity,
                )
            except ValidationError as exc:
                form.add_error(None, exc.message)
            else:
                return redirect("user:purchase_success", purchase_id=purchase_obj.id)
    else:
        form = PurchaseForm(initial={"quantity": 1})

    return render(
        request,
        "user/purchase.html",
        {
            "form": form,
            "mode": mode,
        },
    )


def purchase_success(request, purchase_id):
    purchase_obj = get_object_or_404(Purchase, id=purchase_id)
    tickets = purchase_obj.lottoticket_set.all().order_by("id")

    return render(
        request,
        "user/purchase_success.html",
        {
            "purchase": purchase_obj,
            "tickets": tickets,
        },
    )


def check(request):
    purchase_id = request.GET.get("purchase_id", "").strip()
    ticket_number = request.GET.get("ticket_number", "").strip()

    result = None
    error_message = None

    if request.method == "GET" and (purchase_id or ticket_number):
        tickets = []

        selected_round = None

        if purchase_id:
            try:
                purchase_obj = Purchase.objects.select_related("round").get(id=purchase_id)
            except (Purchase.DoesNotExist, ValueError):
                error_message = "구매 ID를 찾을 수 없습니다."
            else:
                tickets = list(purchase_obj.lottoticket_set.all().order_by("id"))
                selected_round = purchase_obj.round

        elif ticket_number:
            try:
                ticket = LottoTicket.objects.select_related("purchase", "purchase__round").get(ticket_number=ticket_number)
                tickets = [ticket]
                selected_round = ticket.purchase.round
            except LottoTicket.DoesNotExist:
                error_message = "티켓 번호를 찾을 수 없습니다."

        if tickets and selected_round and not selected_round.is_drawn:
            error_message = "아직 추첨을 안했습니다."
        elif tickets and selected_round and selected_round.is_drawn:
            result_tickets = []
            for ticket in tickets:
                rank = _calculate_rank(ticket.numbers, selected_round.win_numbers, selected_round.bonus_number)
                result_tickets.append(
                    {
                        "ticket": ticket,
                        "rank": rank,
                    }
                )

            result = {
                "round": selected_round,
                "tickets": result_tickets,
            }

    return render(
        request,
        "user/check.html",
        {
            "result": result,
            "error_message": error_message,
            "purchase_id": purchase_id,
            "ticket_number": ticket_number,
        },
    )