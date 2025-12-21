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

def get_event_context(report_date_str, lookback_days=7):
    """
    Generates event context for the given date.
    
    Args:
        report_date_str (str): Date in 'YYYY-MM-DD' format.
        lookback_days (int): Number of past days to check for recent events.
        
    Returns:
        dict: Context dictionary with flags and notes.
    """
    report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
    
    # Flag Normalization Mapping
    NORM_MAP = {
        "TRIPLE_WITCHING_CALENDAR_OVERRIDE": "TRIPLE_WITCHING",
        "MONTHLY_OPEX_OVERRIDE": "MONTHLY_OPEX",
        "FOMC_MEETING": "FOMC",
        "CPI_RELEASE": "CPI",
        "NFP_REPORT": "NFP"
    }

    # Load manual calendar
    calendar_events = {}
    manual_calendar_loaded = False
    cal_path = os.path.join(os.path.dirname(__file__), 'event_calendar.json')
    try:
        with open(cal_path, 'r') as f:
            raw_cal = json.load(f)
            # Normalize flags on load
            for d, flags in raw_cal.items():
                normalized = [NORM_MAP.get(f, f) for f in flags]
                calendar_events[d] = normalized
            manual_calendar_loaded = True
    except Exception as e:
        print(f"Warning: Could not load event_calendar.json: {e}")

    context = {
        "as_of": report_date_str,
        "source": {
            "manual_calendar_loaded": manual_calendar_loaded,
            "cal_path": cal_path
        },
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
        c = calendar.Calendar()
        weekdays = [d for d in c.itermonthdates(date_obj.year, date_obj.month) if d.month == date_obj.month and d.weekday() < 5]
        if weekdays and date_obj == weekdays[-1]:
            flags.append("MONTH_END")
            if date_obj.month in [3, 6, 9, 12]:
                flags.append("QUARTER_END")

        return list(set(flags)) # Dedupe

    # Check Today (Report Date)
    context["flags_today"] = check_date(report_date)

    # Check Recent (last N days)
    for i in range(1, lookback_days + 1):
        past_date = report_date - timedelta(days=i)
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
        "RUSSELL_REBALANCE": "High volume in small caps expected due to index reconstitution.",
        "INDEX_REBALANCE": "Mechanical flows due to index weighting changes.",
        "AUCTION_WEEK": "Treasury auction cycle; rates positioning may be hedge-related.",
        "REFUNDING": "Quarterly refunding announcements; significant rates impact possible.",
        "CPI": "Consumer Price Index data release; high volatility expected.",
        "NFP": "Non-Farm Payrolls report; high volatility expected."
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
