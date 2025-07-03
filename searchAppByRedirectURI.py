import requests
import json
import sys

# --- Configuration ---
# Parameters are now loaded from an external config.json file.

def load_config(filename="config.json"):
    """Loads configuration from a JSON file."""
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
            # Check for required keys
            required_keys = ["TENANT_ID", "CLIENT_ID", "CLIENT_SECRET", "SEARCH_STRING"]
            for key in required_keys:
                if key not in config or not config[key]:
                    print(f"Error: '{key}' is missing or empty in {filename}.")
                    sys.exit(1) # Exit the script if config is incomplete
            print("Configuration loaded successfully.")
            return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{filename}' not found.")
        print("Please create it and add your Entra ID app details.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filename}'. Please check its format.")
        sys.exit(1)

def get_access_token(config):
    """
    Authenticates and retrieves an access token from Microsoft Entra ID
    using the client credentials flow.
    """
    authority = f"https://login.microsoftonline.com/{config['TENANT_ID']}"
    token_url = f"{authority}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": config['CLIENT_ID'],
        "client_secret": config['CLIENT_SECRET'],
        "scope": "https://graph.microsoft.com/.default",
    }
    print("Requesting access token...")
    try:
        token_r = requests.post(token_url, data=token_data)
        token_r.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        token = token_r.json().get("access_token")
        if not token:
            print("Error: Access token not found in the response.")
            print("Response:", token_r.json())
            return None
        print("Access token acquired successfully.")
        return token
    except requests.exceptions.RequestException as e:
        print(f"Error acquiring access token: {e}")
        if 'token_r' in locals():
            print("Response content:", token_r.text)
        return None

def find_apps_with_uri(access_token, search_string):
    """
    Searches all Entra ID applications for a specific URI and its owners,
    handling pagination.
    """
    if not access_token:
        print("Cannot proceed without a valid access token.")
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    graph_api_endpoint = "https://graph.microsoft.com/v1.0"
    # Modified the API call to select and expand the 'owners' property
    next_link = f"{graph_api_endpoint}/applications?$select=displayName,appId,web,spa,owners&$expand=owners"
    found_apps = []
    page_num = 1

    print(f"\nStarting search for URI containing: '{search_string}'\n" + "="*50)

    while next_link:
        try:
            print(f"Fetching page {page_num}...")
            response = requests.get(next_link, headers=headers)
            response.raise_for_status()
            data = response.json()

            applications = data.get("value", [])
            
            for app in applications:
                app_name = app.get('displayName', 'N/A')
                app_id = app.get('appId', 'N/A')
                uris_to_check = []

                if app.get("web"):
                    web_info = app["web"]
                    if web_info.get("redirectUris"):
                        uris_to_check.extend(web_info["redirectUris"])
                    if web_info.get("homePageUrl"):
                        uris_to_check.append(web_info["homePageUrl"])
                    if web_info.get("logoutUrl"):
                        uris_to_check.append(web_info["logoutUrl"])

                if app.get("spa"):
                    spa_info = app["spa"]
                    if spa_info.get("redirectUris"):
                        uris_to_check.extend(spa_info["redirectUris"])

                for uri in uris_to_check:
                    if uri and search_string in uri:
                        print(f"  [FOUND] Match in App: '{app_name}' (App ID: {app_id})")
                        print(f"  > Matched URI: {uri}")
                        
                        # Process the owners list
                        owners_list = []
                        if app.get("owners"):
                            for owner in app["owners"]:
                                # Use displayName if available, otherwise use userPrincipalName
                                owner_name = owner.get('displayName', owner.get('userPrincipalName', 'Unknown Owner'))
                                owners_list.append(owner_name)
                        
                        app_owners = owners_list if owners_list else ["No owners listed"]
                        print(f"  > Owners: {', '.join(app_owners)}\n")

                        if app_id not in [found_app['appId'] for found_app in found_apps]:
                            found_apps.append({
                                "displayName": app_name, 
                                "appId": app_id, 
                                "uri": uri,
                                "owners": app_owners
                            })
                        break
            
            next_link = data.get("@odata.nextLink")
            page_num += 1

        except requests.exceptions.RequestException as e:
            print(f"An error occurred during API request: {e}")
            if 'response' in locals(): print("Response content:", response.text)
            break
        except json.JSONDecodeError:
            print("Failed to decode JSON from response.")
            if 'response' in locals(): print("Response content:", response.text)
            break
            
    print("="*50 + "\nSearch complete.")
    if found_apps:
        print(f"\nSummary: Found {len(found_apps)} application(s) with the specified URI.")
        for app in found_apps:
            print(f"- App: {app['displayName']} ({app['appId']})")
            print(f"  Owners: {', '.join(app['owners'])}")
    else:
        print("No applications found matching the criteria.")


if __name__ == "__main__":
    # --- API Permissions Note ---
    # Your Entra ID App Registration needs the following APPLICATION permissions:
    # 1. Application.Read.All - To read application properties.
    # 2. User.Read.All - To read the display names of the user objects who are owners.
    #    (Without this, you may only get owner IDs instead of names).
    # Remember to grant admin consent for these permissions in your tenant.

    # Load configuration from the external file
    config = load_config()
    
    # Get the token using the loaded config
    access_token = get_access_token(config)
    
    # Run the search using the token and search string from the config
    find_apps_with_uri(access_token, config["SEARCH_STRING"])
