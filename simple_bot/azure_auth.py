from msal import PublicClientApplication
from uuid import uuid4

client_id = ""

app = PublicClientApplication(
    client_id=client_id,
    authority="https://login.microsoftonline.com/common",
    enable_broker_on_windows=True
)

flow = app.initiate_device_flow(scopes=["User.Read"])
print(flow)  # Prompts you to visit a URL and enter a code
result = app.acquire_token_by_device_flow(flow)
print("Access token:", result["access_token"])
