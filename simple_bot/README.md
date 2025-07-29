# Bot Framework

## Notes
https://learn.microsoft.com/en-us/azure/bot-service/bot-service-quickstart-create-bot?view=azure-bot-service-4.0&tabs=csharp%2Cvs

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo apt install cookiecutter
cookiecutter https://github.com/microsoft/BotBuilder-Samples/releases/download/Templates/echo.zip
```
bot_name: echo_bot
bot_description: A bot that echoes back user response.
```
cd echo_bot
pip install -r requirements.txt
python app.py
```
Getting a browser to view the results:
```
sudo wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt install --fix-broken -y
sudo dpkg -i google-chrome-stable_current_amd64.deb
```
On host machine (not within WSL)
Add the file `.wslconfig` to `/Users/<profile name>` with the content:
```
[wsl2]
networkingMode=mirrored
```
Then restart `wsl` by running `wsl --shutdown`.

Also edit `app.py`:
```
# change host="localhost" to "127.0.0.1"
web.run_app(APP, host="127.0.0.1", port=CONFIG.PORT)
```

Open Bot Framework Emulator on the host machine, click "Open Bot" and enter 
"http://127.0.0.1:3978/api/messages" for the Bot URL, then click "Connect".


# Building Bots
https://github.com/Microsoft/BotBuilder-Samples/blob/main/README.md

Connecting to Azure Open AI
- Create an Azure OpenAI resource
- In the resource on Azure portal, go to Overview > Explore Azure AI Foundry Portal
- In Azure AI Foundry, go to Get Started - Model catalog
- Im choosing gpt-4.1
- The result page will show some code on usage as well as Target URI and Key.
```
# project_2/.env
AZURE_OPENAI_API_KEY="<key>"
AZURE_OPENAI_ENDPOINT="https://openai-robotoad.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview"
```

# Working on IcM Integration 
https://support.microsoft.com/en-us/windows/manage-devices-used-with-your-microsoft-account-d4044995-81db-b24b-757e-1102d148f441

```
sudo apt install seahorse
```
https://learn.microsoft.com/en-us/entra/msal/python/advanced/linux-broker-py-wsl?tabs=ubuntudep
