# Retrieve all s3-csi-node pod names in the kube-system namespace
$s3CsiPods = kubectl get pods -n kube-system | Select-String -Pattern "s3-csi-node" | ForEach-Object {
    $_.Line.Split(' ')[0]
}

# Check if any s3-csi-node pods were found
if ($s3CsiPods.Count -eq 0) {
    Write-Output "No s3-csi-node pods found in the kube-system namespace."
} else {
    # Delete each s3-csi-node pod
    foreach ($pod in $s3CsiPods) {
        Write-Output "Deleting pod $pod..."
        kubectl delete pod $pod -n kube-system
    }
    Write-Output "All s3-csi-node pods have been deleted. They will restart automatically."
}
