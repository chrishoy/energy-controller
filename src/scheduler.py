import schedule
import time
from octopus_api import get_current_price

# from heating_controller import set_heating_mode


def job():
    price = get_current_price()
    print(f"Current energy price: {price}")
    # if price < 20:  # cheap
    #     set_heating_mode("comfort")
    # else:
    #     set_heating_mode("eco")


def start_scheduler():
    schedule.every(1).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)
