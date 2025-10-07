from flask import Flask, render_template, jsonify
from src.octopus_api import get_octopus_rates
from src.config import get_config
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
                "as_at": rate_data.as_at.isoformat(),
                "data_read_at": rate_data.data_read_at.isoformat(),
                "current": {
                    "value_exc_vat": (
                        current_rate.value_exc_vat if current_rate else None
                    ),
                    "value_inc_vat": (
                        current_rate.value_inc_vat if current_rate else None
                    ),
                    "valid_from": (
                        current_rate.valid_from.isoformat() if current_rate else None
                    ),
                    "valid_to": (
                        current_rate.valid_to.isoformat() if current_rate else None
                    ),
                },
                "latest": [
                    {
                        "value_exc_vat": rate.value_exc_vat,
                        "value_inc_vat": rate.value_inc_vat,
                        "valid_from": rate.valid_from.isoformat(),
                        "valid_to": rate.valid_to.isoformat(),
                    }
                    for rate in rate_data.latest
                ],
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Load configuration
    config = get_config()
    # Create the templates directory if it doesn't exist
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=config.DEBUG)
