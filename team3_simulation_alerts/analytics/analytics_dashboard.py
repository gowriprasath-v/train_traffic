import sys
import os

# Add the parent directory (project root) to sys.path so imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import api_test.test_schedule_api as schedule_api
import matplotlib.pyplot as plt

def plot_delays(schedule):
    if not schedule:
        print("No schedule data to plot.")
        return

    delays = []
    for train in schedule:
        delay = train.get('delay_minutes', 0)
        try:
            delay = int(delay)
        except (ValueError, TypeError):
            delay = 0
        delays.append(delay)

    max_delay = max(delays) if delays else 35
    bins = list(range(0, max(31, max_delay + 1), 5))

    plt.hist(delays, bins=bins, edgecolor='black', align='left')

    plt.title("Train Delay Distribution (Live Data)")
    plt.xlabel("Delay (minutes)")
    plt.ylabel("Number of Trains")
    plt.xticks(bins)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    counts, _, patches = plt.hist(delays, bins=bins, edgecolor='black', alpha=0)
    for count, patch in zip(counts, patches):
        if count > 0:
            height = patch.get_height()
            plt.text(patch.get_x() + patch.get_width()/2, height + 0.1, str(int(count)),
                     ha='center', va='bottom')

    plt.show()

if __name__ == "__main__":
    schedule = schedule_api.fetch_schedule()
    if schedule:
        if "trains" in schedule:
            plot_delays(schedule["trains"])
        else:
            print("Schedule data does not contain 'trains'")
    else:
        print("Failed to retrieve schedule data.")
