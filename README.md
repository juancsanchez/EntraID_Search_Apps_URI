# Entra ID Application Search by Redirect URI

This Python script searches all application registrations within a Microsoft Entra ID (formerly Azure AD) tenant to find which ones contain a specific redirect URI. It's a helpful tool for administrators who need to track down applications associated with a particular domain or endpoint, especially during service migrations or decommissioning.

The script uses the Microsoft Graph API to fetch application data, handles pagination for large tenants, and displays the application's name, ID, and its owners.

## Features

- Searches across `web` and `spa` application types.
- Checks `redirectUris`, `homePageUrl`, and `logoutUrl` for the specified string.
- Retrieves and displays the application's display name, App ID, and a list of its owners.
- Handles Graph API pagination automatically to scan all applications in the tenant.
- Uses a secure client credentials flow for authentication.
- All configuration is managed in an external `config.json` file, keeping secrets out of the code.

## Prerequisites

- Python 3.6+
- Access to a Microsoft Entra ID tenant.
- Permissions to create an App Registration in the tenant and grant it admin consent for API permissions.

## Setup

Follow these steps to configure and run the script.

### 1. Install Dependencies

The script requires the `requests` library. It's recommended to use a Python virtual environment.

```bash
pip install requests
```

### 2. Create an Entra ID App Registration

The script needs its own identity in Entra ID to securely access the Microsoft Graph API.

1.  Navigate to the **Microsoft Entra admin center**.
2.  Go to **Identity > Applications > App registrations** and select **New registration**.
3.  Give it a descriptive name (e.g., `GraphAppUriSearcher`).
4.  Leave the other options as default and click **Register**.
5.  Once created, copy the **Application (client) ID** and **Directory (tenant) ID** from the app's **Overview** page. You will need these for the configuration file.

### 3. Configure API Permissions

The App Registration needs permission to read application data from the Graph API.

1.  In your new App Registration, go to the **API permissions** blade.
2.  Click **Add a permission** and select **Microsoft Graph**.
3.  Choose **Application permissions**.
4.  Search for and add the following permissions:
    - `Application.Read.All`: Allows the script to read the properties of all applications.
    - `User.Read.All`: Allows the script to read the full profile of user objects, which is needed to display the names of application owners.
5.  After adding the permissions, you **must** click the **Grant admin consent for [Your Tenant]** button. The status for each permission should change to "Granted".

### 4. Create a Client Secret

1.  In your App Registration, go to the **Certificates & secrets** blade.
2.  Click **New client secret**, give it a description (e.g., `app-search-script-secret`), and choose an expiry duration.
3.  **Immediately copy the secret's "Value"**. This is your only chance to see it.

### 5. Create the `config.json` File

In the same directory as the `searchAppByRedirectURI.py` script, create a file named `config.json`. Add the following content and replace the placeholder values with the information you collected in the previous steps.

```json
{
  "TENANT_ID": "YOUR_DIRECTORY_TENANT_ID",
  "CLIENT_ID": "YOUR_APPLICATION_CLIENT_ID",
  "CLIENT_SECRET": "YOUR_CLIENT_SECRET_VALUE",
  "SEARCH_STRING": "https://your.uri.to.search.for"
}
```

## Usage

After completing the setup, you can run the script from your terminal.

```bash
python searchAppByRedirectURI.py
```

The script will output its progress, printing details for each application that matches the `SEARCH_STRING`. A final summary is provided at the end of the search.

### Example Output

```
Configuration loaded successfully.
Requesting access token...
Access token acquired successfully.

Starting search for URI containing: 'example.com'
==================================================
Fetching page 1...
  [FOUND] Match in App: 'My Web App' (App ID: 12345678-abcd-1234-abcd-1234567890ab)
  > Matched URI: https://app.example.com/auth
  > Owners: Jane Doe, John Smith

==================================================
Search complete.

Summary: Found 1 application(s) with the specified URI.
- App: My Web App (12345678-abcd-1234-abcd-1234567890ab)
  Owners: Jane Doe, John Smith
```