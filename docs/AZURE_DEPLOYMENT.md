# Azure Deployment Guide

This guide documents the deployment process for the Sharedo DOCX to HTML Converter Service to Azure Container Apps in the Docspective resource group.

## Architecture Overview

The service is deployed as a containerized application on Azure Container Apps with the following components:

- **Azure Container Apps**: Serverless container hosting with auto-scaling
- **Azure Container Registry**: Container image storage
- **Log Analytics Workspace**: Centralized logging
- **Application Insights**: Application performance monitoring
- **Azure Key Vault**: Secure storage for secrets (production)

## Prerequisites

1. **Azure CLI**: Install from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
2. **Docker**: Install from https://docs.docker.com/get-docker/
3. **Azure Subscription**: Access to the Docspective resource group
4. **Git**: For version control

## Environments

We support three environments:

| Environment | Purpose | Scaling | API Key | URL |
|------------|---------|---------|---------|-----|
| **dev** | Development and testing | 1-3 replicas | Disabled | TBD |
| **test** | Integration testing | 1-5 replicas | Enabled | TBD |
| **prod** | Production | 2-10 replicas | Required | TBD |

## Deployment Methods

### Method 1: GitHub Actions (Automated CI/CD)

The recommended approach for production deployments.

#### Setup GitHub Secrets

In your GitHub repository settings, add these secrets:

```yaml
AZURE_CLIENT_ID: <service-principal-client-id>
AZURE_TENANT_ID: <azure-tenant-id>
AZURE_SUBSCRIPTION_ID: <azure-subscription-id>
```

#### Trigger Deployment

1. **Manual Deployment**:
   - Go to Actions tab in GitHub
   - Select "Deploy to Azure Container Apps"
   - Click "Run workflow"
   - Select environment (dev/test/prod)

2. **Automatic Deployment**:
   - Push to `develop` branch → deploys to `dev`
   - Push to `main` branch → deploys to `prod`

### Method 2: Local Script Deployment

For development and testing purposes.

#### 1. Login to Azure

```bash
az login
az account set --subscription <subscription-id>
```

#### 2. Make Script Executable

```bash
chmod +x scripts/deploy.sh
```

#### 3. Deploy to Environment

```bash
# Deploy to development
./scripts/deploy.sh dev

# Deploy to test
./scripts/deploy.sh test

# Deploy to production (requires additional secrets)
./scripts/deploy.sh prod
```

### Method 3: Direct Bicep Deployment

For advanced users who want full control.

#### 1. Build and Push Docker Image

```bash
# Build image
docker build -t docspectiveacr.azurecr.io/sharedo-docx-converter:latest .

# Login to ACR
az acr login --name docspectiveacr

# Push image
docker push docspectiveacr.azurecr.io/sharedo-docx-converter:latest
```

#### 2. Deploy with Bicep

```bash
# Deploy to dev environment
az deployment group create \
  --resource-group Docspective \
  --template-file azure/main.bicep \
  --parameters @azure/parameters-dev.json \
  --parameters containerImage=docspectiveacr.azurecr.io/sharedo-docx-converter:latest

# Deploy to production (with Key Vault references)
az deployment group create \
  --resource-group Docspective \
  --template-file azure/main.bicep \
  --parameters @azure/parameters-prod.json \
  --parameters containerImage=docspectiveacr.azurecr.io/sharedo-docx-converter:latest
```

## Configuration

### Environment Variables

All configuration is managed through Bicep parameters and environment variables:

| Variable | Description | Dev | Test | Prod |
|----------|------------|-----|------|------|
| `APP_ENV` | Application environment | development | testing | production |
| `LOG_LEVEL` | Logging verbosity | DEBUG | INFO | INFO |
| `MAX_FILE_SIZE` | Max upload size (bytes) | 10MB | 15MB | 20MB |
| `API_KEY_ENABLED` | Require API authentication | false | true | true |
| `RATE_LIMIT_REQUESTS` | Requests per minute | 100 | 500 | 1000 |

### Secrets Management

#### Development/Test
- Secrets are passed as parameters in the deployment
- Stored in Container App secrets

#### Production
- Secrets are stored in Azure Key Vault
- Referenced in `parameters-prod.json` using Key Vault references
- Managed Identity for secure access

Example Key Vault reference:
```json
"apiKey": {
  "reference": {
    "keyVault": {
      "id": "/subscriptions/.../providers/Microsoft.KeyVault/vaults/docspective-kv"
    },
    "secretName": "docx-converter-api-key"
  }
}
```

## Monitoring and Diagnostics

### Application Insights

View application performance and errors:

```bash
# Get Application Insights connection string
az deployment group show \
  --resource-group Docspective \
  --name <deployment-name> \
  --query properties.outputs.appInsightsConnectionString.value
```

### Container App Logs

Stream real-time logs:

```bash
az containerapp logs show \
  --name sharedo-docx-converter-<env> \
  --resource-group Docspective \
  --follow
```

### Health Checks

Verify deployment health:

```bash
# Check health endpoint
curl https://<app-url>/health

# Check metrics
curl https://<app-url>/metrics

# View Swagger documentation
open https://<app-url>/docs
```

## Scaling Configuration

Container Apps automatically scale based on HTTP traffic:

| Environment | Min Replicas | Max Replicas | Concurrent Requests |
|------------|--------------|--------------|---------------------|
| dev | 1 | 3 | 50 |
| test | 1 | 5 | 50 |
| prod | 2 | 10 | 50 |

Manual scaling:

```bash
az containerapp update \
  --name sharedo-docx-converter-<env> \
  --resource-group Docspective \
  --min-replicas 2 \
  --max-replicas 10
```

## Troubleshooting

### Common Issues

#### 1. Deployment Fails

```bash
# Check deployment status
az deployment group list \
  --resource-group Docspective \
  --query "[?contains(name, 'docx-converter')]"

# View deployment errors
az deployment group show \
  --resource-group Docspective \
  --name <deployment-name> \
  --query properties.error
```

#### 2. Container Fails to Start

```bash
# Check container status
az containerapp show \
  --name sharedo-docx-converter-<env> \
  --resource-group Docspective \
  --query properties.provisioningState

# View container logs
az containerapp logs show \
  --name sharedo-docx-converter-<env> \
  --resource-group Docspective \
  --tail 100
```

#### 3. Image Pull Errors

```bash
# Verify ACR credentials
az acr credential show --name docspectiveacr

# Test image pull
docker pull docspectiveacr.azurecr.io/sharedo-docx-converter:latest
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
az containerapp update \
  --name sharedo-docx-converter-<env> \
  --resource-group Docspective \
  --set-env-vars DEBUG=true LOG_LEVEL=DEBUG
```

## Rollback Procedure

If deployment fails or issues are detected:

### Quick Rollback

```bash
# List revisions
az containerapp revision list \
  --name sharedo-docx-converter-<env> \
  --resource-group Docspective

# Activate previous revision
az containerapp revision activate \
  --name sharedo-docx-converter-<env> \
  --resource-group Docspective \
  --revision <previous-revision-name>
```

### Full Rollback with Bicep

```bash
# Redeploy with previous image tag
az deployment group create \
  --resource-group Docspective \
  --template-file azure/main.bicep \
  --parameters @azure/parameters-<env>.json \
  --parameters containerImage=docspectiveacr.azurecr.io/sharedo-docx-converter:<previous-tag>
```

## Cost Optimization

### Recommendations

1. **Use Consumption Plan**: Container Apps charges only for actual usage
2. **Configure Auto-scaling**: Set appropriate min/max replicas
3. **Enable Application Insights Sampling**: Reduce telemetry costs
4. **Set Log Retention**: Configure appropriate retention periods

### Cost Monitoring

```bash
# View current costs
az consumption usage list \
  --resource-group Docspective \
  --query "[?contains(instanceName, 'docx-converter')]"
```

## Security Best Practices

1. **API Keys**: Always use API key authentication in production
2. **Network Security**: Configure network restrictions if needed
3. **Managed Identity**: Use for Azure service authentication
4. **Key Vault**: Store all secrets in Azure Key Vault
5. **Container Scanning**: Enable vulnerability scanning in ACR

```bash
# Enable ACR vulnerability scanning
az acr update --name docspectiveacr --sku Standard
```

## Maintenance

### Update Application

```bash
# Build and push new version
docker build -t docspectiveacr.azurecr.io/sharedo-docx-converter:v2.0.0 .
docker push docspectiveacr.azurecr.io/sharedo-docx-converter:v2.0.0

# Deploy update
az containerapp update \
  --name sharedo-docx-converter-<env> \
  --resource-group Docspective \
  --image docspectiveacr.azurecr.io/sharedo-docx-converter:v2.0.0
```

### Certificate Renewal

Container Apps automatically manages TLS certificates.

### Backup and Recovery

Application is stateless - no data backup required. Configuration is stored in:
- Git repository (code and Bicep templates)
- Azure Key Vault (secrets)
- Azure Resource Manager (infrastructure state)

## Support and Contacts

- **GitHub Issues**: https://github.com/Alterspective-io/sharedo-docx-converter/issues
- **Email**: support@alterspective.io
- **Azure Portal**: https://portal.azure.com

## Appendix: Quick Commands

```bash
# View app URL
az containerapp show -n sharedo-docx-converter-<env> -g Docspective --query properties.configuration.ingress.fqdn -o tsv

# Stream logs
az containerapp logs show -n sharedo-docx-converter-<env> -g Docspective --follow

# Restart app
az containerapp revision restart -n sharedo-docx-converter-<env> -g Docspective --revision <revision-name>

# Scale app
az containerapp update -n sharedo-docx-converter-<env> -g Docspective --min-replicas 2 --max-replicas 10

# Update environment variable
az containerapp update -n sharedo-docx-converter-<env> -g Docspective --set-env-vars KEY=value
```