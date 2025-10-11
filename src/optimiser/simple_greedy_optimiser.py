from datetime import timezone
from typing import List, Tuple, Dict, Any
from src.rates.types import Rate


def optimize_heating_schedule(
    data: List[Rate],
    comfort_hours: List[Tuple[int, int]] = [(7, 9), (17, 22)],
    preheat_slots: int = 2,  # 1 hour = 2 half-hour slots
    retain_slots: int = 4,  # 2 hours = 4 half-hour slots
    slot_duration_hours: float = 0.5,
    power_kw: float = 1.0,
) -> Dict[str, Any]:
    """
    Determine an optimal heating schedule that minimizes cost while ensuring comfort.
    Handles negative pricing and thermal retention.
    Only returns ON/OFF transition points.
    """

    # --- 1️⃣ Sort data chronologically ---
    data_sorted = sorted(data, key=lambda r: r.valid_from)

    # --- 2️⃣ Extract times and prices ---
    times = [r.valid_from.astimezone(timezone.utc) for r in data_sorted]
    prices = [r.value_inc_vat for r in data_sorted]
    n = len(data_sorted)

    # --- 3️⃣ Identify comfort slots ---
    comfort_slots = set()
    for i, t in enumerate(times):
        for start, end in comfort_hours:
            if start <= t.hour < end:
                comfort_slots.add(i)

    # --- 4️⃣ Build schedule ---
    full_schedule = []
    warm_remaining = 0
    total_cost = 0.0
    on_slots = 0

    for i, (t, price) in enumerate(zip(times, prices)):
        is_comfort = i in comfort_slots
        on = False

        # Case 1: Negative price → always ON
        if price < 0:
            on = True
            warm_remaining = retain_slots

        # Case 2: Comfort period → must be warm
        elif is_comfort:
            if warm_remaining <= 0:
                on = True
                warm_remaining = retain_slots

        # Case 3: Approaching comfort → preheat if beneficial
        else:
            upcoming = [i + j for j in range(1, preheat_slots + 1) if i + j < n]
            if any(idx in comfort_slots for idx in upcoming):
                future_prices = [prices[idx] for idx in upcoming]
                if price <= min(future_prices, default=price):
                    on = True
                    warm_remaining = retain_slots

        # Warmth retention
        warm = warm_remaining > 0
        if warm_remaining > 0:
            warm_remaining -= 1

        # Cost per slot
        cost = price * power_kw * slot_duration_hours / 100
        if on:
            total_cost += cost
            on_slots += 1

        full_schedule.append(
            {
                "time": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "on": on,
                "warm": warm,
                "price": price,
                "cost": cost,
            }
        )

    # --- 5️⃣ Compute summary ---
    comfort_total = len(comfort_slots)
    warm_comfort = sum(
        1 for i in comfort_slots if i < len(full_schedule) and full_schedule[i]["warm"]
    )
    summary = {
        "total_slots": n,
        "on_slots": on_slots,
        "on_hours": on_slots * slot_duration_hours,
        "total_cost": round(total_cost, 3),
        "average_on_price": (
            round(sum(s["price"] for s in full_schedule if s["on"]) / on_slots, 3)
            if on_slots
            else None
        ),
        "comfort_slots": comfort_total,
        "warm_comfort_slots": warm_comfort,
    }

    # --- 6️⃣ Extract transitions only ---
    transitions = []
    last_state = None
    for s in full_schedule:
        if s["on"] != last_state:
            transitions.append({"time": s["time"], "on": s["on"], "price": s["price"]})
            last_state = s["on"]

    return {"transitions": transitions, "summary": summary}
