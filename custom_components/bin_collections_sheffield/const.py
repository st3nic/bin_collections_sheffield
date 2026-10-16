from datetime import time

DOMAIN = "sheffield_bins"

API_URL = "https://wasteservices.sheffield.gov.uk/api/getCalendarData/"

COUNCIL_ID = "1"

CONF_UPRN = "uprn"

CONF_REMINDER_TIME = "reminder_time"

DEFAULT_REMINDER_TIME = "18:00:00"

# Bins out tonight turns off at this time on collection day.
REMINDER_OFF_TIME = time(7, 0)

MANUFACTURER = "Sheffield City Council"

SCAN_INTERVAL_HOURS = 2
