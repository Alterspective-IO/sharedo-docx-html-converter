# GitHub Secrets Configuration for Azure Deployment

This guide explains how to configure GitHub secrets required for automated deployment to Azure Container Apps.

## Required GitHub Secrets

The following secrets must be configured in your GitHub repository for the deployment workflow to function:

### 1. Azure Service Principal Credentials

These secrets authenticate GitHub Actions with Azure:

| Secret Name | Description | How to Obtain |
|------------|-------------|---------------|
| `AZURE_CLIENT_ID` | Service Principal Application ID | See "Creating Service Principal" section |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | `az account show --query tenantId -o tsv` |
| `AZURE_SUBSCRIPTION_ID` | Azure Subscription ID | `az account show --query id -o tsv` |

### 2. Additional Secrets (Optional)

These may be needed depending on your configuration:

| Secret Name | Description | Required For |
|------------|-------------|--------------|
| `ACR_NAME` | Azure Container Registry name | If different from default |
| `RESOURCE_GROUP` | Azure Resource Group | If different from "Docspective" |

## Step-by-Step Setup

### Step 1: Create Azure Service Principal

```bash
# Create service principal with contributor access to resource group
az ad sp create-for-rbac \
  --name "github-actions-docx-converter" \
  --role contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/Docspective \
  --sdk-auth
```

This command will output JSON like:
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  ...
}
```

### Step 2: Add Secrets to GitHub

1. Navigate to your GitHub repository
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:

#### AZURE_CLIENT_ID
- Name: `AZURE_CLIENT_ID`
- Value: The `clientId` from the JSON output

#### AZURE_TENANT_ID
- Name: `AZURE_TENANT_ID`
- Value: The `tenantId` from the JSON output

#### AZURE_SUBSCRIPTION_ID
- Name: `AZURE_SUBSCRIPTION_ID`
- Value: The `subscriptionId` from the JSON output

### Step 3: Grant ACR Access

The service principal needs access to the Azure Container Registry:

```bash
# Get ACR resource ID
ACR_ID=$(az acr show --name docspectiveacr --query id -o tsv)

# Grant push/pull access to service principal
az role assignment create \
  --assignee <CLIENT_ID> \
  --role "AcrPush" \
  --scope $ACR_ID
```

### Step 4: Verify Configuration

Test the configuration by running the workflow manually:

1. Go to **Actions** tab in GitHub
2. Select "Deploy to Azure Container Apps"
3. Click "Run workflow"
4. Select `dev` environment
5. Monitor the workflow execution

## Environment-Specific Configuration

### Development Environment

No additional secrets required - uses default configuration.

### Testing Environment

Optional secrets:
- `TEST_API_KEY`: API key for test environment authentication

### Production Environment

Required secrets:
- `PROD_API_KEY`: Production API key (store in Azure Key Vault)

## Azure Key Vault Integration (Production)

For production deployments, sensitive values should be stored in Azure Key Vault:

### 1. Create Key Vault Secrets

```bash
# Create API key secret
az keyvault secret set \
  --vault-name docspective-kv \
  --name docx-converter-api-key \
  --value "your-secure-api-key"

# Create Redis password secret (if using Redis)
az keyvault secret set \
  --vault-name docspective-kv \
  --name redis-password \
  --value "your-redis-password"
```

### 2. Grant Service Principal Access

```bash
# Get service principal object ID
SP_OBJECT_ID=$(az ad sp show --id <CLIENT_ID> --query objectId -o tsv)

# Grant secret read permissions
az keyvault set-policy \
  --name docspective-kv \
  --object-id $SP_OBJECT_ID \
  --secret-permissions get list
```

## Troubleshooting

### Authentication Errors

If you see "Authentication failed" errors:

1. Verify service principal credentials:
```bash
az login --service-principal \
  --username <CLIENT_ID> \
  --password <CLIENT_SECRET> \
  --tenant <TENANT_ID>
```

2. Check role assignments:
```bash
az role assignment list --assignee <CLIENT_ID>
```

### Permission Errors

If deployment fails with permission errors:

1. Ensure service principal has Contributor role:
```bash
az role assignment create \
  --assignee <CLIENT_ID> \
  --role Contributor \
  --scope /subscriptions/<SUB_ID>/resourceGroups/Docspective
```

2. Verify ACR permissions:
```bash
az role assignment list \
  --assignee <CLIENT_ID> \
  --scope $(az acr show --name docspectiveacr --query id -o tsv)
```

### Secret Not Found

If workflow fails with "secret not found":

1. Verify secret names match exactly (case-sensitive)
2. Check secret visibility (repository vs environment secrets)
3. Ensure secrets are in the correct scope

## Security Best Practices

1. **Rotate Secrets Regularly**: Update service principal credentials every 90 days
2. **Use Least Privilege**: Grant minimum required permissions
3. **Audit Access**: Review service principal usage regularly
4. **Environment Separation**: Use different service principals for prod/non-prod
5. **Secret Scanning**: Enable GitHub secret scanning

## Quick Reference

### List All Secrets (Azure CLI)

```bash
# Get subscription ID
az account show --query id -o tsv

# Get tenant ID
az account show --query tenantId -o tsv

# Get service principal details
az ad sp list --display-name "github-actions-docx-converter"

# Get ACR login server
az acr show --name docspectiveacr --query loginServer -o tsv
```

### Update Service Principal Password

```bash
# Reset service principal credentials
az ad sp credential reset \
  --name "github-actions-docx-converter" \
  --years 1
```

## Support

If you encounter issues:

1. Check the GitHub Actions logs for detailed error messages
2. Verify all secrets are correctly configured
3. Ensure Azure resources exist and are accessible
4. Contact support@alterspective.io for assistance