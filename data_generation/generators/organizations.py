import pandas as pd
import uuid
import random
from faker import Faker
from datetime import datetime

fake = Faker()

def generate_organizations(n_orgs):
    industries = ["SaaS", "Fintech", "HealthTech", "Logistics", "EdTech", "AI Services"]
    sizes = ["Small", "Medium", "Enterprise"]
    
    rows = []
    for _ in range(n_orgs):
        rows.append({
            "organization_id": str(uuid.uuid4()),
            "name": fake.company(), 
            "industry": random.choice(industries),
            "country": fake.country_code(), 
            "company_size": random.choices(sizes, weights=[50, 35, 15])[0],
            "created_at": fake.date_between(start_date="-730d", end_date="today").strftime("%Y-%m-%d %H:%M:%S")
        })
    return pd.DataFrame(rows)