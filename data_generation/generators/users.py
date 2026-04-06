import pandas as pd
import uuid
import random
from faker import Faker
from config import TODAY

fake = Faker()
roles = ["product_manager", "data_analyst", "engineer", "founder", "marketing_lead"]

def generate_users(org_df, n_users):
    rows = []
    org_ids = org_df["organization_id"].tolist()
    
    for _ in range(n_users):
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        rows.append({
            "user_id": str(uuid.uuid4()),
            "organization_id": random.choice(org_ids),
            "user_name": f"{first_name} {last_name}", 
            "email": f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}",
            "role": random.choice(roles),        
            "signup_date": fake.date_between(start_date="-730d", end_date=TODAY).strftime("%Y-%m-%d %H:%M:%S")
        })
    return pd.DataFrame(rows)