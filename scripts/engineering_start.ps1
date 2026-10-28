<#
JEV-ORBITA Engineering Start (BuildArena S02, Autopilot).

Starts one tracked, isolated Claude Code engineering run. The run gets only:
the system prompt, the initial instruction, the official BuildArena MCP, the
official BuildArena 2.0 checkout (read access) and the jev_orbita helpers.
User-level CLAUDE.md, hooks, plugins and memories are excluded by using a
dedicated CLAUDE_CONFIG_DIR, so no unrelated human context enters the run.

  .\scripts\engineering_start.ps1                 # new run (refuses if preflight is blocked)
  .\scripts\engineering_start.ps1 -Resume <dir>   # administrative resume: "Continue the previous work."
  .\scripts\engineering_start.ps1 -Login          # one-time authentication of the isolated profile
#>
param(
    [string]$Resume = "",
    [switch]$Login,
    [string]$Model = "claude-opus-5-5"
)
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "env.ps1")
$env:CLAUDE_CONFIG_DIR = Join-Path $Here ".claude-agent"
New-Item -ItemType Directory -Force -Path $env:CLAUDE_CONFIG_DIR | Out-Null

if ($Login) { claude; exit $LASTEXITCODE }

$BuildArena = $env:ORBITA_BUILDARENA_ROOT
$Settings = '{"disableAllHooks": true}'

if ($Resume) {
    $Run = Resolve-Path $Resume
    $Session = (Get-Content (Join-Path $Run "session.json") | ConvertFrom-Json).session_id
    $Message = "Continue the previous work."
    Add-Content (Join-Path $Run "admin_messages.log") ("{0}`t{1}" -f (Get-Date).ToUniversalTime().ToString("o"), $Message)
    Push-Location (Join-Path $Run "workspace")
    claude -p $Message --resume $Session --model $Model --output-format stream-json --verbose `
        --permission-mode bypassPermissions --strict-mcp-config --mcp-config (Join-Path $Run "mcp.json") `
        --settings $Settings --add-dir $BuildArena |
        Tee-Object -Append -FilePath (Join-Path $Run "transcript.jsonl")
    Pop-Location
    exit $LASTEXITCODE
}

$env:PYTHONPATH = Join-Path $Here "src"
python (Join-Path $Here "scripts\preflight.py") | Out-File -Encoding utf8 (Join-Path $env:TEMP "orbita-preflight.json")
if ($LASTEXITCODE -ne 0) { Get-Content (Join-Path $env:TEMP "orbita-preflight.json"); throw "Preflight blocked: Engineering Start refused." }

$Stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$Run = Join-Path $Here "runs\$Stamp"
$Work = Join-Path $Run "workspace"
New-Item -ItemType Directory -Force -Path $Work, (Join-Path $Work "machines"), (Join-Path $Work "experiments"), (Join-Path $Work "submission") | Out-Null
Copy-Item (Join-Path $Here "prompts\agent_system.md") (Join-Path $Work "CLAUDE.md")
Copy-Item -Recurse (Join-Path $Here "src\jev_orbita") (Join-Path $Work "jev_orbita")
Copy-Item (Join-Path $env:TEMP "orbita-preflight.json") (Join-Path $Run "preflight.json")

$Mcp = @{ mcpServers = @{ "build-arena" = @{ command = "uv"; args = @(
    "run", "--directory", $BuildArena, "python", "-m", "buildarena.mcp_server",
    "--save-dir", (Join-Path $Work "machines")) } } } | ConvertTo-Json -Depth 6
Set-Content -Encoding utf8 (Join-Path $Run "mcp.json") $Mcp

$SessionId = [guid]::NewGuid().ToString()
@{ session_id = $SessionId; model = $Model; started_utc = $Stamp; mode = "autopilot";
   harness_commit = (git -C $Here rev-parse HEAD); buildarena_commit = (git -C $BuildArena rev-parse HEAD) } |
    ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $Run "session.json")
$Instruction = Get-Content -Raw (Join-Path $Here "prompts\autopilot_initial.md")
Copy-Item (Join-Path $Here "prompts\autopilot_initial.md") (Join-Path $Run "initial_instruction.md")

Write-Host "Engineering Start: $Run (session $SessionId)"
Push-Location $Work
claude -p $Instruction --session-id $SessionId --model $Model --output-format stream-json --verbose `
    --permission-mode bypassPermissions --strict-mcp-config --mcp-config (Join-Path $Run "mcp.json") `
    --settings $Settings --add-dir $BuildArena |
    Tee-Object -FilePath (Join-Path $Run "transcript.jsonl")
Pop-Location
python (Join-Path $Here "scripts\transcript_to_md.py") $Run
