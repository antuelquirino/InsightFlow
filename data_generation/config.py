from datetime import date, timedelta

PROJECT_ID = "insightflow-analytics-489617"
DATASET_RAW = "raw"


N_ORGANIZATIONS = 500
N_USERS = 2000
N_EVENTS = 100000


TODAY = date.today()
HISTORICAL_START_DATE = TODAY - timedelta(days=730)