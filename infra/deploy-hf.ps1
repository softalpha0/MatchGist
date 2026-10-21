# Publish MatchGist to a free Hugging Face Docker Space (no Azure, no card).
#
# Before running:
#   1. Create a Space at https://huggingface.co/new-space : SDK "Docker", template "Blank", hardware
#      "CPU basic" (free), visibility Public.
#   2. Create a Hugging Face access token with write access (Settings -> Access Tokens). Git asks for it
#      as the password on push; your username is the user name.
#   3. In the Space: Settings -> Variables and secrets -> add MATCHGIST_LLM_BASE_URL, MATCHGIST_LLM_MODEL,
#      MATCHGIST_LLM_CALLS_PER_MINUTE, MATCHGIST_LLM_CALLS_PER_DAY as variables and MATCHGIST_LLM_API_KEY
#      as a *secret*. Never put keys in the repo.
#
# Usage (from the repo root):
#   .\infra\deploy-hf.ps1 -Space <hf-username>/matchgist
#
# It pushes the committed code (git archive of HEAD, so .env and untracked files are never included) plus a
# Space README header to the Space's git repo. The Space then builds the Dockerfile itself.

param(
    [Parameter(Mandatory = $true)][string]$Space,
    [string]$Ref = "HEAD"
)

$ErrorActionPreference = "Stop"
$root = (git rev-parse --show-toplevel).Trim()
$work = Join-Path ([IO.Path]::GetTempPath()) ("matchgist-space-" + [guid]::NewGuid().ToString("N").Substring(0, 8))

git clone "https://huggingface.co/spaces/$Space" $work
if ($LASTEXITCODE -ne 0) { throw "Could not clone the Space. Check the name and that it exists." }

# Replace the Space's files with the committed tree (legacy/ is left out: it's not part of the app)
Get-ChildItem $work -Force | Where-Object { $_.Name -ne ".git" } | Remove-Item -Recurse -Force
$tar = Join-Path $work "src.tar"
git -C $root archive --format=tar -o $tar $Ref
tar -xf $tar -C $work
Remove-Item $tar
if (Test-Path (Join-Path $work "legacy")) { Remove-Item (Join-Path $work "legacy") -Recurse -Force }

# Spaces read their settings from YAML at the top of README.md
$header = @"
---
title: MatchGist
colorFrom: green
colorTo: gray
sdk: docker
app_port: 8000
pinned: false
license: mit
short_description: One match, sized to fit every fan. Fictional data only.
---

"@
$readme = Join-Path $work "README.md"
$utf8 = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($readme, $header + [IO.File]::ReadAllText($readme), $utf8)

$sha = (git -C $root rev-parse --short $Ref).Trim()
git -C $work add -A
git -C $work commit -m "Deploy MatchGist $sha"
git -C $work push
if ($LASTEXITCODE -ne 0) { throw "Push failed. Use your Hugging Face token (write) as the password." }

$user, $name = $Space -split "/", 2
Write-Host ""
Write-Host "Pushed. The Space is building (a few minutes): https://huggingface.co/spaces/$Space"
Write-Host "Live app once built: https://$($user.ToLower())-$($name.ToLower()).hf.space/live"
Remove-Item $work -Recurse -Force
