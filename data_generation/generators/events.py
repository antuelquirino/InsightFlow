import pandas as pd
import uuid
import random
from datetime import datetime, timedelta, timezone

def generate_events(users_df, subs_df, n_events):
    rows = []
    
    event_names = ["login", "view_dashboard", "run_query", "export_data"]
    event_weights = [0.5, 0.3, 0.15, 0.05] 
    
    
    users_list = users_df[["user_id", "organization_id"]].values.tolist()
    subs_list = subs_df[["organization_id", "start_date"]].values.tolist()
    
   
    subs_map = {row[0]: row[1] for row in subs_list}
    
    
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)

    print(f"Generating {n_events} events with UTC synchronization and safety margin...")

    for _ in range(n_events):
        user_id, org_id = random.choice(users_list)
        
       
        raw_start = subs_map.get(org_id, "2023-01-01")
        
        if isinstance(raw_start, str):
           
            start_dt = datetime.strptime(raw_start[:10], "%Y-%m-%d")
        else:
            
            start_dt = raw_start.replace(tzinfo=None) if hasattr(raw_start, 'tzinfo') else raw_start

        
        total_seconds_life = int((now_utc - start_dt).total_seconds())

        if total_seconds_life <= 0:
            
            event_date = start_dt
        else:
           
            random_second = random.randint(0, total_seconds_life)
            event_date = start_dt + timedelta(seconds=random_second)

        
        rows.append({
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "organization_id": org_id,
            "event_name": random.choices(event_names, weights=event_weights)[0],
            "event_timestamp": event_date.isoformat() 
        })
    
    df = pd.DataFrame(rows)
    return df