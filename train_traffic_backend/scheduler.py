from models import ScheduleRequest

def get_optimized_schedule(request: ScheduleRequest):
    trains_sorted = sorted(request.trains, key=lambda t: (t.priority, t.arrival))
    used_platforms = set()
    scheduled = []
    for t in trains_sorted:
        if t.platform not in used_platforms:
            scheduled.append(t.dict())
            used_platforms.add(t.platform)
    result = {
    "date": request.date,
    "trains": sorted(request.trains, key=lambda x: x.arrival)  # Example optimization logic
}
    return result
