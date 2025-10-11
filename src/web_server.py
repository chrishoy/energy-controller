from flask import Flask, render_template, jsonify
from src.octopus_api import get_octopus_rates
from src.config import get_config
from src.optimiser import Optimiser
from src.optimiser.types import OptimisationParams, OptimisationStrategy
from src.utils.date_utils import datetime_to_json_str
import os


app = Flask(__name__)

# Create templates directory
os.makedirs(os.path.join(os.path.dirname(__file__), "templates"), exist_ok=True)


@app.route("/")
def index():
    """Render the main page with energy rates."""
    return render_template("index.html")


@app.route("/api/rates")
def get_rates():
    """API endpoint to get the latest rates."""
    try:
        rate_data = get_octopus_rates()
        current_rate = rate_data.current
        return jsonify(
            {
                "as_at": datetime_to_json_str(rate_data.as_at),
                "data_read_at": datetime_to_json_str(rate_data.data_read_at),
                "current": {
                    "value_exc_vat": (
                        current_rate.value_exc_vat if current_rate else None
                    ),
                    "value_inc_vat": (
                        current_rate.value_inc_vat if current_rate else None
                    ),
                    "valid_from": (
                        datetime_to_json_str(current_rate.valid_from)
                        if current_rate
                        else None
                    ),
                    "valid_to": (
                        datetime_to_json_str(current_rate.valid_to)
                        if current_rate
                        else None
                    ),
                },
                "latest": [
                    {
                        "value_exc_vat": rate.value_exc_vat,
                        "value_inc_vat": rate.value_inc_vat,
                        "valid_from": datetime_to_json_str(rate.valid_from),
                        "valid_to": datetime_to_json_str(rate.valid_to),
                    }
                    for rate in rate_data.latest
                ],
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/heating-schedule")
def get_heating_schedule():
    """API endpoint to get the optimized heating schedule."""
    try:
        # --- 1. Get prices from Octopus
        rate_data = get_octopus_rates()

        # --- 2. Define optimisation params
        optimisation_params = OptimisationParams(
            comfort_hours=[(7, 9), (16, 22)],
            preheat_slots=2,
            power_kw=3.5,
        )

        # --- 3. Use specific strategy to created an optimised heading schedule
        optimiser = Optimiser()

        # --- Simple Greedy or Advanced Predictive ---
        strategy = OptimisationStrategy.ADVANCED_PREDICTIVE

        optimisation_results = optimiser.run_optimisation(
            data=rate_data.latest,
            strategy=strategy,
            optimisation_params=optimisation_params,
        )

        return jsonify(optimisation_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Load configuration
    config = get_config()
    # Create the templates directory if it doesn't exist
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=config.DEBUG)
