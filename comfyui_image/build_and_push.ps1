param (
    [string]$Region
)

if (-not $Region) {
    Write-Output "Usage: .\build_and_push.ps1 -Region <aws-region>"
    exit 1
}

# Get AWS Account ID
$AccountId = (aws sts get-caller-identity --query "Account" --output text)

Write-Output "AccountID: $AccountId, Region: $Region"

# Build the Docker image
docker build --platform="linux/amd64" . -t comfyui-images --no-cache

# Tag the Docker image
$repositoryUri = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/comfyui-images:latest"
docker tag comfyui-images:latest $repositoryUri

# Log in to ECR
$loginPassword = aws ecr get-login-password --region $Region
$loginCommand = "docker login --username AWS --password $loginPassword $repositoryUri"
Invoke-Expression $loginCommand

# Push the Docker image to ECR
docker push $repositoryUri

# Clean up dangling images
docker images | Where-Object { $_.Repository -eq "<none>" } | ForEach-Object { docker rmi -f $_.ID }
