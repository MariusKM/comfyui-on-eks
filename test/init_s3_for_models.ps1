param (
    [Parameter(Mandatory=$true)]
    [string]$region
)

# Get AWS Account ID
$account = (aws sts get-caller-identity --query Account --output text)
$bucket = "comfyui-models-$account-$region"

# Define directories
$dirs = @("checkpoints", "clip", "clip_vision", "configs", "controlnet", "diffusers", "embeddings", "gligen", "hypernetworks", "loras", "style_models", "unet", "upscale_models", "vae", "vae_approx")

# Create directories and placeholder files
foreach ($dir in $dirs) {
    $path = "$HOME\comfyui-models\$dir"
    New-Item -ItemType Directory -Force -Path $path | Out-Null
    New-Item -ItemType File -Path "$path\put_here" | Out-Null
}

# Download files
Invoke-WebRequest -Uri "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors?download=true" -OutFile "$HOME\comfyui-models\checkpoints\sd_xl_base_1.0.safetensors"
Invoke-WebRequest -Uri "https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0/resolve/main/sd_xl_refiner_1.0.safetensors?download=true" -OutFile "\comfyui-models\checkpoints\sd_xl_refiner_1.0.safetensors"

# Sync with S3
aws s3 sync "$HOME\comfyui-models" "s3://$bucket/" --region $region

# Clean up
Remove-Item -Recurse -Force "$HOME\comfyui-models"
