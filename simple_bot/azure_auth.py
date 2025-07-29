from msal import PublicClientApplication
from uuid import uuid4

client_id = ""
username=""
scope = ["User.ReadBasic.All"]

app = PublicClientApplication(
    client_id=client_id,
    authority="https://login.microsoftonline.com/common",
    enable_broker_on_windows=True,
    enable_broker_on_wsl=True
)

# The pattern to acquire a token looks like this.
result = None

# Firstly, check the cache to see if this end user has signed in before
accounts = app.get_accounts(username=username)
if accounts:
    print("Account(s) exists in cache, probably with token too. Let's try.")
    result = app.acquire_token_silent(scope, account=accounts[0])

if not result:
    print("No suitable token exists in cache. Let's get a new one from AAD.")
    
    result = app.acquire_token_interactive(scope,parent_window_handle=app.CONSOLE_WINDOW_HANDLE)
    
if "access_token" in result:
    print("Access token is: %s" % result['access_token'])

else:
    print(result.get("error"))
    print(result.get("error_description"))
    print(result.get("correlation_id"))  # You may need this when reporting a bug
    if 65001 in result.get("error_codes", []):  # Not mean to be coded programatically, but...
        # AAD requires user consent for U/P flow
        print("Visit this to consent:", app.get_authorization_request_url(scope))