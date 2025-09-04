# --- PASTE THIS ENTIRE SCRIPT INTO Fix-Firewall.ps1 ---

# 1. DEFINE YOUR CLUSTER AND REGION VARIABLES
$CLUSTER_NAME = "online-boutique-services"
$GKE_REGION = "us-central1"

# 2. FIND THE NODE POOL NAME
Write-Host "Finding node pool in region: $GKE_REGION..."
$NODE_POOL_NAME = gcloud container node-pools list --cluster=$CLUSTER_NAME --region=$GKE_REGION --format="value(name)"
Write-Host "Found node pool name: $NODE_POOL_NAME"

# 3. FIND THE INSTANCE GROUP AND THE REAL VM NAME
Write-Host "Finding instance group for node pool: $NODE_POOL_NAME..."
$INSTANCE_GROUP_URL = gcloud container node-pools describe $NODE_POOL_NAME --cluster=$CLUSTER_NAME --region=$GKE_REGION --format="value(instanceGroupUrls[0])"
$MIG_NAME = $INSTANCE_GROUP_URL.Split('/')[-1]

# We need to find which zone the managed instance group is in
$MIG_ZONE = gcloud compute instance-groups managed describe $MIG_NAME --region=$GKE_REGION --format="value(zone)"

$INSTANCE_URL = gcloud compute instance-groups managed list-instances $MIG_NAME --zone=$MIG_ZONE --format="value(instance)"
$INSTANCE_NAME = $INSTANCE_URL.Split('/')[-1]
Write-Host "Successfully found the correct GCE instance name: $INSTANCE_NAME"

# 4. GET THE NETWORK TAG
Write-Host "Finding network tag for instance: $INSTANCE_NAME..."
$NODE_TAG = gcloud compute instances describe $INSTANCE_NAME --zone=$MIG_ZONE --format='get(tags.items[0])'
Write-Host "Successfully found the node's network tag: $NODE_TAG"

# 5. CREATE THE FIREWALL RULE (FINAL COMMAND)
Write-Host "Creating firewall rule 'gke-allow-health-checks'..."
gcloud compute firewall-rules create gke-allow-health-checks `
    --network=default `
    --action=ALLOW `
    --direction=INGRESS `
    --source-ranges="130.211.0.0/22,35.191.0.0/16" `
    --target-tags="$NODE_TAG" `
    --rules=tcp

Write-Host "SUCCESS! Firewall rule created. Please wait 2-5 minutes for the load balancer to become healthy."