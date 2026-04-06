import pandas as pd
import uuid
import random
from datetime import datetime, timezone, timedelta
from bigquery_loader import load_dataframe



def run_daily_incremental():
    print("🚀 Iniciando carga incremental segura...")
    
    
    now = datetime.now(timezone.utc) - timedelta(minutes=5)
    today_dt = now.strftime("%Y-%m-%d %H:%M:%S")
    today_date_only = now.strftime("%Y-%m-%d")

   
    org_id = str(uuid.uuid4())
    orgs_df = pd.DataFrame([{
        "organization_id": org_id,
        "name": f"New Corp {random.randint(100, 999)}",
        "industry": "SaaS",
        "country": "US",
        "company_size": "Medium",
        "created_at": today_dt
    }])


    users_df = pd.DataFrame([
        {
            "user_id": str(uuid.uuid4()),
            "organization_id": org_id,
            "user_name": "User Incremental A",
            "email": "inc.a@example.com",
            "role": "engineer",
            "signup_date": today_dt
        },
        {
            "user_id": str(uuid.uuid4()),
            "organization_id": org_id,
            "user_name": "User Incremental B",
            "email": "inc.b@example.com",
            "role": "data_analyst",
            "signup_date": today_dt
        }
    ])

    
    subs_df = pd.DataFrame([{
        "subscription_id": str(uuid.uuid4()),
        "organization_id": org_id,
        "plan_id": "growth",
        "mrr": 99,
        "status": "active",
        "start_date": today_date_only,
        "end_date": None
    }])

    
    events_rows = []
    for u_id in users_df["user_id"]:
        for _ in range(10):
            events_rows.append({
                "event_id": str(uuid.uuid4()),
                "user_id": u_id,
                "organization_id": org_id,
                "event_name": random.choice(["login", "view_dashboard"]),
                "event_timestamp": today_dt 
            })
    events_df = pd.DataFrame(events_rows)

    
    print("Uploading Data (MODE APPEND)...")
    
    
    load_dataframe(orgs_df, "organizations", full_refresh=False)
    load_dataframe(users_df, "users", full_refresh=False)
    load_dataframe(subs_df, "subscriptions", full_refresh=False)
    load_dataframe(events_df, "product_events", full_refresh=False)

    print(f"✅ Success {today_dt}")

if __name__ == "__main__":
    run_daily_incremental()