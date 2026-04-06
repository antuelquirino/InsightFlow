import pandas as pd
import uuid
import random
from datetime import datetime, timedelta

def generate_subscriptions(org_df, n_subs):
    rows = []
    org_ids = org_df["organization_id"].tolist()
    
    # 1. Definimos planes variados para análisis de segmentos
    plans = [
        {"id": "starter", "mrr": 29.0, "weight": 50},
        {"id": "growth", "mrr": 99.0, "weight": 35},
        {"id": "enterprise", "mrr": 499.0, "weight": 15}
    ]
    
    now = datetime.now()

    for i in range(n_subs):
        org_id = org_ids[i % len(org_ids)]
        
       
        days_back = random.randint(0, 540) 
        start_dt = now - timedelta(days=days_back)
        
        
        plan = random.choices(plans, weights=[p["weight"] for p in plans])[0]
        
       
        status = random.choices(["active", "canceled"], weights=[80, 20])[0]
        end_dt = None
        if status == "canceled":
           
            days_active = random.randint(30, max(31, days_back))
            end_dt = (start_dt + timedelta(days=days_active)).strftime("%Y-%m-%d %H:%M:%S")

        rows.append({
            "subscription_id": str(uuid.uuid4()),
            "organization_id": org_id,
            "plan_id": plan["id"],
            "mrr": plan["mrr"],
            "start_date": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": end_dt,
            "status": status
        })
        
    return pd.DataFrame(rows)