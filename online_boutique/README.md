# Online Boutique Multi-Agent System

This is an online boutique application built with a multi-agent architecture using Google ADK agents and MCP (Model Context Protocol).

## Architecture

- **Root Agent**: Online Boutique Coordinator - orchestrates the entire shopping experience
- **Sub-Agents**: Specialized agents for different e-commerce functions via A2A protocol
  - Shipping Service Agent
  - Customer Service Agent  
  - Payment Processor Agent
  - Catalog Service Agent
- **MCP Server**: Provides tools and services for the agents

<img width="1205" height="648" alt="image" src="https://github.com/user-attachments/assets/a05511fa-6ce1-48ca-912a-5519b0c2e531" />

## Deployment

This application is designed to run on Google Kubernetes Engine (GKE) with each component deployed as separate microservices.

### Environment Variables

**Linux:**
```bash
export PROJECT_ID="YourProjectId"
export REGION="us-central1"
export GOOGLE_API_KEY="YourGeminiAPIKey"
export IMAGE_TAG="v1.0.0"
```

**Windows:**
```powershell
$env:PROJECT_ID="gke-hackethon"
$env:REGION="us-central1"
$env:GOOGLE_API_KEY="YourGeminiAPIKey"
$env:IMAGE_TAG="v1.0.0"
```

### GKE Deployment Steps

1. Install GKE auth plugin:
```bash
gcloud components install gke-gcloud-auth-plugin
```

2. Set project configuration:
```bash
gcloud config set project $env:PROJECT_ID
```

3. Enable required services:
```bash
gcloud services enable container.googleapis.com --project=$env:PROJECT_ID
gcloud services enable containerregistry.googleapis.com --project=$env:PROJECT_ID
```

4. Create GKE cluster:
```bash
gcloud container clusters create-auto online-boutique-services --project=$env:PROJECT_ID --region=$env:REGION
```

5. Build and push Docker image:
```bash
cd online_boutique
docker build -t gcr.io/gke-hackethon/online-boutique-service:$env:IMAGE_TAG .
docker push gcr.io/gke-hackethon/online-boutique-service:$env:IMAGE_TAG
```

6. Deploy to Kubernetes:
```powershell
(Get-Content .\gke-deployment.yaml) -replace '\$\{PROJECT_ID\}', $env:PROJECT_ID -replace '\$\{GOOGLE_API_KEY\}', $env:GOOGLE_API_KEY -replace '\$\{IMAGE_TAG\}', $env:IMAGE_TAG | kubectl apply -f -
```
