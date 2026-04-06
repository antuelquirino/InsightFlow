from generators.organizations import generate_organizations
from generators.users import generate_users
from generators.subscriptions import generate_subscriptions
from generators.events import generate_events
from bigquery_loader import create_dataset, load_dataframe
from config import N_ORGANIZATIONS, N_USERS, N_EVENTS

def main():
    print("--- 🔍 STARTING FINAL DEPLOY ---")
    
    
    create_dataset() 

    
    orgs = generate_organizations(N_ORGANIZATIONS)
    users = generate_users(orgs, N_USERS)
    subs = generate_subscriptions(orgs, N_ORGANIZATIONS)
    events = generate_events(users, subs, N_EVENTS)

    print(f"AUDIT: Orgs:{len(orgs)}, Users:{len(users)}, Subs:{len(subs)}, Events:{len(events)}")

   
    print("🚀 All counts match! Uploading to BigQuery...")
    load_dataframe(orgs, "organizations", full_refresh=True)
    load_dataframe(users, "users", full_refresh=True)
    load_dataframe(subs, "subscriptions", full_refresh=True)
    load_dataframe(events, "product_events", full_refresh=True)
    
    print("--- ✅ FINISHED SUCCESSFULLY ---")

if __name__ == "__main__":
    main()