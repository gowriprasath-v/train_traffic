def check_for_alerts(schedule):
    alerts = []
    for train in schedule:
        if train.get('delay_minutes', 0) > 5:
            alerts.append(f"Train {train['train_id']} delayed by {train['delay_minutes']} minutes")
    return alerts

if __name__ == "__main__":
    import api_test.test_schedule_api as schedule_api
    schedule = schedule_api.fetch_schedule()
    if schedule:
        alert_list = check_for_alerts(schedule)
        for alert in alert_list:
            print(alert)
