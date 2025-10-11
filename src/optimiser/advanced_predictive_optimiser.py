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

    # --- 1️⃣ Sort data and extract essentials ---
    if not data:
        return {"transitions": [], "summary": {}}
    data_sorted = sorted(data, key=lambda r: r.valid_from)
    times = [r.valid_from.astimezone(timezone.utc) for r in data_sorted]
    prices = [r.value_inc_vat for r in data_sorted]
    n = len(data_sorted)

    # --- 2️⃣ Identify all comfort slots by their index ---
    comfort_slots = set()
    for i, t in enumerate(times):
        # Use local time to check against comfort hours
        local_hour = t.astimezone().hour
        for start, end in comfort_hours:
            if start <= local_hour < end:
                comfort_slots.add(i)

    # --- 3️⃣ Corrected Algorithm: Proactive Scheduling ---
    on_indices = set()

    # Step A: Turn on for any negative price slots (always optimal)
    for i, price in enumerate(prices):
        if price < 0:
            on_indices.add(i)

    # Step B: Determine which comfort slots are already covered by warmth
    # from the negative-price heating sessions.
    uncovered_comfort_slots = set(comfort_slots)

    # Create a helper to update coverage
    def get_covered_slots(heating_slots: set) -> set:
        covered = set()
        for i in heating_slots:
            # Add the slot itself and the subsequent slots covered by heat retention
            for j in range(retain_slots):
                if i + j < n:
                    covered.add(i + j)
        return covered

    # Step C: Iteratively find the cheapest way to cover remaining comfort slots
    while uncovered_comfort_slots:
        # Find the earliest comfort slot that still needs heating
        target_slot = min(uncovered_comfort_slots)

        # Define the window to look for the best time to preheat
        # This window is from the start of the preheat period up to the target slot itself
        window_start = max(0, target_slot - preheat_slots)
        window_end = target_slot

        # Find the cheapest slot within this preheating window
        best_price = float("inf")
        best_heating_slot = -1

        for i in range(window_start, window_end + 1):
            if prices[i] < best_price:
                best_price = prices[i]
                best_heating_slot = i

        # Schedule the heating at the cheapest time
        if best_heating_slot != -1:
            on_indices.add(best_heating_slot)

        # Recalculate which slots are now covered and remove them from the 'uncovered' set
        all_covered_slots = get_covered_slots(on_indices)
        uncovered_comfort_slots -= all_covered_slots

    # --- 4️⃣ Build the full schedule and calculate costs ---
    full_schedule = []
    warm_remaining = 0
    total_cost = 0.0
    on_slots_count = len(on_indices)

    for i in range(n):
        on = i in on_indices
        if on:
            warm_remaining = retain_slots

        warm = warm_remaining > 0
        if warm_remaining > 0:
            warm_remaining -= 1

        cost = prices[i] * power_kw * slot_duration_hours / 100 if on else 0.0
        total_cost += cost

        full_schedule.append(
            {
                "time": times[i].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "on": on,
                "warm": warm,
                "price": prices[i],
                "cost": cost,
            }
        )

    # --- 5️⃣ Compute summary ---
    warm_comfort_slots = sum(
        1 for i in comfort_slots if i < len(full_schedule) and full_schedule[i]["warm"]
    )
    summary = {
        "total_slots": n,
        "on_slots": on_slots_count,
        "on_hours": on_slots_count * slot_duration_hours,
        "total_cost": round(total_cost, 3),
        "average_on_price": (
            round(sum(s["price"] for s in full_schedule if s["on"]) / on_slots_count, 3)
            if on_slots_count
            else None
        ),
        "comfort_slots": len(comfort_slots),
        "warm_comfort_slots": warm_comfort_slots,
    }

    # --- 6️⃣ Extract transitions only ---
    transitions = []
    last_state = None
    for s in full_schedule:
        if s["on"] != last_state:
            transitions.append({"time": s["time"], "on": s["on"], "price": s["price"]})
            last_state = s["on"]

    return {"transitions": transitions, "summary": summary}
