import json
import os
from datetime import datetime, timedelta
import calendar

def get_third_friday(year, month):
    """Calculates the date of the 3rd Friday of the given month."""
    c = calendar.Calendar(firstweekday=calendar.MONDAY)
    month_cal = c.monthdatescalendar(year, month)
    fridays = [day for week in month_cal for day in week if day.weekday() == calendar.FRIDAY and day.month == month]
    return fridays[2]

def get_event_context(report_date_str, lookback_days=3):
    """
    Generates event context for the given date.
    
    Args:
        report_date_str (str): Date in 'YYYY-MM-DD' format.
        lookback_days (int): Number of past days to check for recent events.
        
    Returns:
        dict: Context dictionary with flags and notes.
    """
    report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
    
    # Load manual calendar
    calendar_events = {}
    try:
        cal_path = os.path.join(os.path.dirname(__file__), 'event_calendar.json')
        with open(cal_path, 'r') as f:
            calendar_events = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load event_calendar.json: {e}")

    context = {
        "as_of": report_date_str,
        "flags_today": [],
        "flags_recent": [],
        "notes": {}
    }

    # Helper to check a specific date
    def check_date(date_obj):
        flags = []
        d_str = date_obj.strftime("%Y-%m-%d")
        
        # 1. Manual Calendar Checks
        if d_str in calendar_events:
            flags.extend(calendar_events[d_str])

        # 2. Deterministic Checks
        
        # Monthly OPEX (3rd Friday)
        third_friday = get_third_friday(date_obj.year, date_obj.month)
        if date_obj == third_friday:
            flags.append("MONTHLY_OPEX")
            # Triple Witching (Mar, Jun, Sep, Dec)
            if date_obj.month in [3, 6, 9, 12]:
                flags.append("TRIPLE_WITCHING")

        # Month End (Business day approx: Last weekday)
        # Simple heuristic: if tomorrow is next month
        # Better heuristic: check if it's the last weekday
        last_day_of_month = calendar.monthrange(date_obj.year, date_obj.month)[1]
        is_last_day = (date_obj.day == last_day_of_month)
        # Or simpler: if it's a weekday and adding 1-3 days lands in next month?
        # Let's stick to strict: Is it the last *weekday*?
        # Get all weekdays in month
        c = calendar.Calendar()
        weekdays = [d for d in c.itermonthdates(date_obj.year, date_obj.month) if d.month == date_obj.month and d.weekday() < 5]
        if weekdays and date_obj == weekdays[-1]:
            flags.append("MONTH_END")
            if date_obj.month in [3, 6, 9, 12]:
                flags.append("QUARTER_END")

        return list(set(flags)) # Dedupe

    # Check Today
    context["flags_today"] = check_date(report_date)

    # Check Recent (last N days)
    for i in range(1, lookback_days + 1):
        past_date = report_date - timedelta(days=i)
        # Only check business days? For simplicity, check all, assuming calendar ignores weekends.
        # But Triple Witching is always Friday. If today is Monday (lag=3), Friday was 3 days ago.
        past_flags = check_date(past_date)
        context["flags_recent"].extend(past_flags)
    
    context["flags_recent"] = list(set(context["flags_recent"]))

    # Populate Notes based on flags found
    all_flags = set(context["flags_today"] + context["flags_recent"])
    
    definitions = {
        "MONTHLY_OPEX": "Expiry/roll can cause mechanical volume/OI changes. Downgrade directional inference.",
        "TRIPLE_WITCHING": "Expiry across index options, single-stock options, and futures; positioning signals may be distorted.",
        "MONTH_END": "Portfolio rebalancing flows possible.",
        "QUARTER_END": "Significant window dressing and rebalancing flows likely.",
        "FOMC": "Federal Reserve meeting; expect volatility.",
        "RUSSELL_REBALANCE": "High volume in small caps expected due to index reconstitution."
    }

    for flag in all_flags:
        if flag in definitions:
            context["notes"][flag] = definitions[flag]
        else:
            context["notes"][flag] = "Market event."

    return context

if __name__ == "__main__":
    # Quick test
    print(json.dumps(get_event_context(datetime.now().strftime("%Y-%m-%d")), indent=2))
