from typing import Any, Dict


def print_optimised_heating_schedule(optimised_heating_schedule: Dict[str, Any]):
    # Print summary
    print("\n--- Optimization Summary ---")
    for k, v in optimised_heating_schedule["summary"].items():
        print(f"{k:25}: {v}")

    # Print ALL transitions
    print("\n--- Transitions---")
    for s in optimised_heating_schedule["transitions"]:
        print(
            (
                f"{s['time']} → "
                f"{'ON' if s['on'] else 'OFF'} | "
                f"price={s['price']:.3f}p"
            )
        )
