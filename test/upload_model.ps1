param (
    [string]$Region,
    [string]$LocalModelPath
)

if (-not $Region -or -not $LocalModelPath) {
    Write-Output "Usage: .\upload_model.ps1 -Region <aws-region> -LocalModelPath <path-to-your-model>"
    exit 1
}

# Get AWS Account ID
$accountId = (aws sts get-caller-identity --query "Account" --output text)

# Define bucket name
$bucket = "comfyui-models-$accountId-$Region"

# Verify or create directories if needed
$directories = @("checkpoints", "clip", "clip_vision", "configs", "controlnet", "diffusers", "embeddings", "gligen", "hypernetworks", "loras", "style_models", "unet", "upscale_models", "vae", "vae_approx")
$baseDir = "$env:USERPROFILE\comfyui-models"

foreach ($dir in $directories) {
    New-Item -Path "$baseDir\$dir" -ItemType Directory -Force | Out-Null
    New-Item -Path "$baseDir\$dir\put_here" -ItemType File -Force | Out-Null
}

# Copy the model to the checkpoints directory
Copy-Item -Path $LocalModelPath -Destination "$baseDir\checkpoints\" -Force

# Upload directory to S3
aws s3 sync $baseDir "s3://$bucket/" --region $Region

# Clean up local directories after upload
Remove-Item -Path $baseDir -Recurse -Force
