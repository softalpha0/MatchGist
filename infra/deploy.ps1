# MatchGist -> Azure Container Apps (consumption plan). Run from the repo root in PowerShell after `az login`.
# Review docs/deploy.md first: this creates billable resources (small, but not zero).
# The image comes from GitHub Container Registry, published by CI on every push to main.

param(
  [string]$ResourceGroup = "rg-matchgist",
  [string]$Location = "swedencentral",
  [string]$Environment = "cae-matchgist",
  [string]$App = "matchgist",
  [string]$Image = "ghcr.io/softalpha0/matchgist:latest",
  [int]$MinReplicas = 0   # 0 = scale to zero when idle (cheapest; ~10-20 s cold start). 1 = always warm.
)

$ErrorActionPreference = "Stop"

# Secrets come from your local environment (load .env yourself, or set them in this session). Never commit them.
$openaiKey = $env:AZURE_OPENAI_API_KEY
$speechKey = $env:AZURE_SPEECH_KEY

az extension add --name containerapp --upgrade --only-show-errors
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait

az group create --name $ResourceGroup --location $Location --output none
az containerapp env create --name $Environment --resource-group $ResourceGroup --location $Location --output none

$secrets = @()
$envVars = @(
  "AZURE_OPENAI_ENDPOINT=$($env:AZURE_OPENAI_ENDPOINT)",
  "AZURE_OPENAI_DEPLOYMENT_FAST=$($env:AZURE_OPENAI_DEPLOYMENT_FAST)",
  "AZURE_OPENAI_API_VERSION=$(if ($env:AZURE_OPENAI_API_VERSION) { $env:AZURE_OPENAI_API_VERSION } else { '2024-10-21' })",
  "AZURE_SPEECH_REGION=$($env:AZURE_SPEECH_REGION)"
)
if ($openaiKey) { $secrets += "openai-key=$openaiKey"; $envVars += "AZURE_OPENAI_API_KEY=secretref:openai-key" }
if ($speechKey) { $secrets += "speech-key=$speechKey"; $envVars += "AZURE_SPEECH_KEY=secretref:speech-key" }

$createArgs = @(
  "containerapp", "create",
  "--name", $App, "--resource-group", $ResourceGroup, "--environment", $Environment,
  "--image", $Image, "--target-port", "8000", "--ingress", "external",
  "--cpu", "0.5", "--memory", "1.0Gi",
  # one replica: live matches and SSE streams are held in memory
  "--min-replicas", "$MinReplicas", "--max-replicas", "1",
  "--env-vars") + $envVars
if ($secrets.Count -gt 0) { $createArgs += @("--secrets") + $secrets }
az @createArgs --output none

$fqdn = az containerapp show --name $App --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn -o tsv
Write-Host "MatchGist is live at https://$fqdn"
Write-Host "Check: https://$fqdn/health  and  https://$fqdn/config"
