import matplotlib.pyplot as plt
import api_test.test_schedule_api as schedule_api

def plot_delays(schedule):
    delays = [train.get('delay_minutes', 0) for train in schedule]
    plt.hist(delays, bins=range(0, 31, 5))
    plt.title("Train Delay Distribution (Live Data)")
    plt.xlabel("Delay (minutes)")
    plt.ylabel("Number of Trains")
    plt.show()

if __name__ == "__main__":
    schedule = schedule_api.fetch_schedule()
    if schedule:
        plot_delays(schedule)
