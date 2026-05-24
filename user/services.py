from decimal import Decimal
import random

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from core.models import LottoTicket, LotteryRound, Purchase


TICKET_PRICE = Decimal("1000.00")
QUANTITY_MIN = 1
QUANTITY_MAX = 10


def _next_round_number() -> int:
    last_round = LotteryRound.objects.aggregate(max_no=Max("round_number"))["max_no"]
    return (last_round or 0) + 1


def get_or_create_active_round() -> LotteryRound:
    round_obj = LotteryRound.objects.filter(is_drawn=False).order_by("-round_number").first()
    if round_obj:
        return round_obj

    # win_numbers/bonus_number are non-null in current schema, so initialize placeholders.
    return LotteryRound.objects.create(
        round_number=_next_round_number(),
        draw_date=timezone.now(),
        win_numbers=[0, 0, 0, 0, 0, 0],
        bonus_number=0,
        is_drawn=False,
    )


def _generate_random_numbers() -> list[int]:
    return sorted(random.sample(range(1, 46), 6))


def _validate_numbers(numbers: list[int]) -> list[int]:
    if len(numbers) > 6:
        raise ValidationError("번호는 최대 6개까지 선택할 수 있습니다.")

    if any(number < 1 or number > 45 for number in numbers):
        raise ValidationError("번호는 1~45 범위여야 합니다.")

    if len(set(numbers)) != len(numbers):
        raise ValidationError("중복 번호는 선택할 수 없습니다.")

    return sorted(numbers)


def _fill_to_six(numbers: list[int]) -> list[int]:
    if len(numbers) >= 6:
        return sorted(numbers)

    remaining_pool = [n for n in range(1, 46) if n not in numbers]
    random_fill = random.sample(remaining_pool, 6 - len(numbers))
    return sorted(numbers + random_fill)


@transaction.atomic
def create_purchase(mode: str, numbers: list[int], quantity: int) -> tuple[Purchase, list[LottoTicket]]:
    if quantity < QUANTITY_MIN or quantity > QUANTITY_MAX:
        raise ValidationError(f"매수는 {QUANTITY_MIN}~{QUANTITY_MAX} 사이여야 합니다.")

    mode = mode if mode in {"manual", "semi", "auto"} else "manual"
    normalized_numbers = _validate_numbers(numbers)

    if mode == "manual":
        if len(normalized_numbers) != 6:
            raise ValidationError("수동 구매는 번호를 정확히 6개 선택해야 합니다.")
        ticket_number_sets = [normalized_numbers] * quantity
    elif mode == "semi":
        if len(normalized_numbers) == 0:
            raise ValidationError("반자동 구매는 최소 1개 이상 번호를 선택해야 합니다.")
        completed = _fill_to_six(normalized_numbers)
        ticket_number_sets = [completed] * quantity
    else:  # auto
        ticket_number_sets = [_generate_random_numbers() for _ in range(quantity)]

    round_obj = get_or_create_active_round()
    purchase = Purchase.objects.create(
        round=round_obj,
        purchase_amount=TICKET_PRICE * quantity,
    )

    tickets = [
        LottoTicket(purchase=purchase, numbers=number_set)
        for number_set in ticket_number_sets
    ]
    LottoTicket.objects.bulk_create(tickets)

    saved_tickets = list(LottoTicket.objects.filter(purchase=purchase).order_by("id"))
    return purchase, saved_tickets
