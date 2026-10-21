# Deploying MatchGist to Azure

MatchGist ships as **one container**: FastAPI serves the API, the live SSE stream and the static web UI.
CI builds the image on every push and publishes it to GitHub Container Registry (`ghcr.io/<you>/<repo>:latest`)
on pushes to `main`. Azure Container Apps then runs that image. No Azure Container Registry is needed.

Nothing in this guide is run for you. Each step that creates a billable resource is marked 💲.

## 0. What it costs (estimates; check the Azure pricing calculator)

| Resource | Setting | Rough cost |
|---|---|---|
| Container Apps, consumption plan | 0.5 vCPU / 1 GiB, **min replicas 0** | Close to free within the monthly free grant; ~10–20 s cold start after idling |
| Container Apps, consumption plan | same, **min replicas 1** (always warm for judges) | Roughly $10–35 / month, depending on idle-rate billing |
| Log Analytics (created with the environment) | default | Small; pennies at demo volume |
| Azure OpenAI mini model | ~100 short calls per match | About $0.01–0.03 per full match |
| Azure AI Speech | **F0 (free) tier**: 0.5 M characters / month | Free at demo volume |

Set a **$50 budget alert** before anything else (step 1).

## 1. Budget alert (do this first)

Azure portal → **Cost Management + Billing** → **Budgets** → **Add**:
scope your subscription, amount **50**, monthly. Add alert conditions at 50%, 80% and 100% of actual cost, and
100% of forecast, emailed to you.

(CLI alternative: `az consumption budget create --budget-name matchgist-50 --amount 50 --category cost --time-grain monthly --start-date 2026-10-01 --end-date 2027-01-31`,
then add the email notifications in the portal.)

## 2. Model (Microsoft Foundry) 💲

1. Go to https://ai.azure.com, create (or open) a project, and **deploy a small chat model**.
   ⚠️ `gpt-4o-mini` (2024-07-18) is reported retired on Azure in 2026. Check the model catalog and Microsoft's
   *Model retirements* page, then pick the current small/mini chat model your region offers.
2. Copy the **endpoint** (`https://<resource>.openai.azure.com/`), an **API key**, and your **deployment name**.
3. Put them in your local `.env` (never committed):
   ```
   AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
   AZURE_OPENAI_API_KEY=<key>
   AZURE_OPENAI_DEPLOYMENT_FAST=<deployment name>
   ```
4. Run locally and check `http://127.0.0.1:8000/config`: `llm_mode` should say `azure-openai`.

## 3. Voice (Azure AI Speech, free tier)

```powershell
az cognitiveservices account create --name mg-speech --resource-group rg-matchgist --kind SpeechServices --sku F0 --location swedencentral --yes
az cognitiveservices account keys list --name mg-speech --resource-group rg-matchgist --query key1 -o tsv
```
Set `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION=swedencentral` in `.env`. Before the demo, check the voices
in `backend/app/voice/tts.py` exist in the portal's Voice Gallery. Nigerian Pidgin has no dedicated voice we
could confirm, so it's read by `en-NG-EzinneNeural` and the UI says so.

## 4. Publish the image

Push to `main` on GitHub. The CI job `image` builds and smoke-tests the container, then pushes
`ghcr.io/<owner>/<repo>:latest`. In GitHub → your profile → **Packages** → the package → **Package settings**,
set visibility to **Public** so Azure can pull it without credentials.

## 5. Deploy to Container Apps 💲

```powershell
az login
# load your .env into this PowerShell session (secrets stay local)
Get-Content .env | Where-Object { $_ -match '^[A-Z_]+=.+' } | ForEach-Object { $k, $v = $_ -split '=', 2; Set-Item "env:$k" $v }
.\infra\deploy.ps1 -Image ghcr.io/softalpha0/<repo>:latest -MinReplicas 0
```

The script prints the public URL. Check `/health` and `/config`, then open `/live` in a private window.

To update after a new push: `az containerapp update -n matchgist -g rg-matchgist --image ghcr.io/softalpha0/<repo>:latest`.

## Notes

- **Max replicas is 1** on purpose: live matches and SSE streams live in memory. One replica serves many
  viewers (each viewer can start their own replay; at most 40 live matches at once).
- With a model configured, try 30× speed for the smoothest demo; at 60× and above, deliveries may trail the
  pitch by a few seconds while the agents work (the match never waits for them).
- To tear everything down: `az group delete --name rg-matchgist`.
