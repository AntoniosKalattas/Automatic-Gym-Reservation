from autoReservation import GymReservationBot, ReservationConfig
from datetime import datetime

def selfTest():
    """
    Runs a self-test of the gym reservation bot.
    """
    print("Running self-test...")
    config = ReservationConfig()
    bot = GymReservationBot(config)
    
    # Use test parameters for the reservation
    time_option = str(1)
    saturday_time_option = str(1)
    day = str(datetime.now().day  +1)
    headless = False  # Run in non-headless mode for visibility during test

    if bot.make_reservation(time_option, saturday_time_option, day, headless, True):
        print("***************************Self Test Passed!***************************")
    else:
        print("***************************Self Test Failed***************************")

if __name__ == "__main__":
    selfTest()
