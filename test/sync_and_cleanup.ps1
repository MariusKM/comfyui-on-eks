# sync_and_cleanup.ps1

param (
    [string]$Region
)

if (-not $Region) {
    Write-Output "Usage: .\sync_and_cleanup.ps1 -Region <aws-region>"
    exit 1
}

# Get AWS Account ID
$accountId = (aws sts get-caller-identity --query "Account" --output text)

# Define S3 bucket name and base directory
$bucket = "comfyui-models-$accountId-$Region"
$baseDir = Join-Path -Path (Get-Location) -ChildPath "comfyui-models"

# Check if base directory exists
if (!(Test-Path -Path $baseDir)) {
    Write-Output "Error: The base directory $baseDir does not exist. Run setup_directories.ps1 first and add the files."
    exit 1
}

# Sync with S3 bucket
aws s3 sync $baseDir "s3://$bucket/" --region $Region

if ($?) {
    Write-Output "Sync complete."

    # Clean up: delete base directory and all contents
    Remove-Item -Recurse -Force -Path $baseDir
    Write-Output "Local directory $baseDir has been removed after sync."
} else {
    Write-Output "Error during sync. Local directory was not deleted."
}