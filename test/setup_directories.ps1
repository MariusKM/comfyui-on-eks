# setup_directories.ps1

param (
    [string]$Region
)

if (-not $Region) {
    Write-Output "Usage: .\setup_directories.ps1 -Region <aws-region>"
    exit 1
}

# Get AWS Account ID
$accountId = (aws sts get-caller-identity --query "Account" --output text)

# Define base directory and required subdirectories
$baseDir = Join-Path -Path (Get-Location) -ChildPath "comfyui-models"
$directories = @("checkpoints", "clip", "clip_vision", "configs", "control", "embeddings", "loras", "vae", "other")

# Create base directory
if (!(Test-Path -Path $baseDir)) {
    New-Item -ItemType Directory -Path $baseDir
}

# Create subdirectories
foreach ($dir in $directories) {
    $fullPath = Join-Path -Path $baseDir -ChildPath $dir
    if (!(Test-Path -Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath
    }
}

Write-Output "Directories created in $baseDir. Please add the necessary files before running the sync script."
