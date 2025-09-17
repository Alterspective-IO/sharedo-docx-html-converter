// Main Bicep template for Sharedo DOCX to HTML Converter Service
// This template creates all required infrastructure including ACR, Container Apps, and monitoring

@description('Base name for the application')
param appName string = 'sharedo-docx-converter'

@description('Environment name (dev, test, prod)')
@allowed(['dev', 'test', 'prod'])
param environment string

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Azure Container Registry name')
param acrName string

@description('Resource group where ACR exists (if different from deployment RG)')
param acrResourceGroup string = resourceGroup().name

@description('ACR SKU')
@allowed(['Basic', 'Standard', 'Premium'])
param acrSku string = 'Basic'

@description('Container image with tag')
param containerImage string = ''

@description('CPU allocation (e.g., 0.25, 0.5, 1.0)')
param cpu string = '0.5'

@description('Memory allocation (e.g., 0.5Gi, 1.0Gi, 2.0Gi)')
param memory string = '1.0Gi'

@description('Minimum number of replicas')
@minValue(0)
@maxValue(30)
param minReplicas int = 1

@description('Maximum number of replicas')
@minValue(1)
@maxValue(30)
param maxReplicas int = 3

@description('Log Analytics retention in days')
@minValue(30)
@maxValue(730)
param logRetentionDays int = 30

@description('Enable Application Insights')
param enableAppInsights bool = true

@description('Create new ACR or use existing')
param createAcr bool = false

// ============ Application Configuration ============
@description('Application host')
param appHost string = '0.0.0.0'

@description('Application port')
param appPort string = '8000'

@description('Application environment')
param appEnv string = environment == 'prod' ? 'production' : 'development'

@description('Enable debug mode')
param debugMode string = 'false'

// API Settings
@description('API prefix')
param apiPrefix string = '/api/v1'

@description('API title')
param apiTitle string = 'Sharedo DOCX to HTML Converter'

@description('API version')
param apiVersion string = '1.0.0'

// File Upload Settings
@description('Maximum file size in bytes (10MB default)')
param maxFileSize string = '10485760'

@description('Allowed file extensions')
param allowedExtensions string = '.docx'

@description('Upload timeout in seconds')
param uploadTimeout string = '30'

// Conversion Settings
@description('Maximum worker threads')
param maxWorkers string = '4'

@description('Conversion timeout in seconds')
param conversionTimeout string = '60'

@description('Confidence threshold for auto-approval')
param confidenceThreshold string = '90'

// Logging
@description('Log level')
param logLevel string = 'INFO'

@description('Log format')
param logFormat string = 'json'

// Security
@description('CORS origins')
param corsOrigins string = '*'

@description('Enable API key authentication')
param apiKeyEnabled string = 'false'

@secure()
@description('API key for authentication')
param apiKey string = ''

// Redis (optional)
@description('Enable Redis caching')
param enableRedis bool = false

@description('Redis host')
param redisHost string = ''

@description('Redis port')
param redisPort string = '6379'

@secure()
@description('Redis password')
param redisPassword string = ''

// Metrics
@description('Enable metrics collection')
param metricsEnabled string = 'true'

@description('Metrics retention days')
param metricsRetentionDays string = '7'

// Rate Limiting
@description('Enable rate limiting')
param rateLimitEnabled string = 'true'

@description('Rate limit requests per period')
param rateLimitRequests string = '100'

@description('Rate limit period in seconds')
param rateLimitPeriod string = '60'

// ============ Variables ============
var acrLoginServer = createAcr ? containerRegistry.properties.loginServer : '${acrName}.azurecr.io'
var containerAppName = '${appName}-${environment}'
var containerEnvName = '${appName}-${environment}-env'
var logAnalyticsName = '${appName}-${environment}-law'
var appInsightsName = '${appName}-${environment}-ai'

// ============ Resources ============

// Azure Container Registry (optional - only create if needed)
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = if (createAcr) {
  name: acrName
  location: location
  sku: {
    name: acrSku
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
  }
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    retentionInDays: logRetentionDays
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    sku: {
      name: 'PerGB2018'
    }
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = if (enableAppInsights) {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Container Apps Environment
resource containerEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// Get existing ACR credentials if not creating new
resource existingAcr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = if (!createAcr) {
  name: acrName
  scope: resourceGroup(acrResourceGroup)
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: int(appPort)
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
        corsPolicy: {
          allowedOrigins: split(corsOrigins, ',')
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          maxAge: 86400
        }
      }
      registries: createAcr ? [
        {
          server: acrLoginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ] : [
        {
          server: acrLoginServer
          username: existingAcr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: concat([
        {
          name: 'acr-password'
          value: createAcr ? containerRegistry.listCredentials().passwords[0].value : existingAcr.listCredentials().passwords[0].value
        }
      ], apiKeyEnabled == 'true' && apiKey != '' ? [
        {
          name: 'api-key'
          value: apiKey
        }
      ] : [], enableRedis && redisPassword != '' ? [
        {
          name: 'redis-password'
          value: redisPassword
        }
      ] : [])
      activeRevisionsMode: 'Single'
      maxInactiveRevisions: 5
    }
    template: {
      containers: [
        {
          name: 'converter'
          image: containerImage != '' ? containerImage : '${acrLoginServer}/${appName}:latest'
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: concat([
            // Application Settings
            { name: 'APP_HOST', value: appHost }
            { name: 'APP_PORT', value: appPort }
            { name: 'APP_ENV', value: appEnv }
            { name: 'DEBUG', value: debugMode }
            
            // API Settings
            { name: 'API_PREFIX', value: apiPrefix }
            { name: 'API_TITLE', value: apiTitle }
            { name: 'API_VERSION', value: apiVersion }
            
            // File Upload Settings
            { name: 'MAX_FILE_SIZE', value: maxFileSize }
            { name: 'ALLOWED_EXTENSIONS', value: allowedExtensions }
            { name: 'UPLOAD_TIMEOUT', value: uploadTimeout }
            
            // Conversion Settings
            { name: 'MAX_WORKERS', value: maxWorkers }
            { name: 'CONVERSION_TIMEOUT', value: conversionTimeout }
            { name: 'CONFIDENCE_THRESHOLD', value: confidenceThreshold }
            
            // Logging
            { name: 'LOG_LEVEL', value: logLevel }
            { name: 'LOG_FORMAT', value: logFormat }
            
            // Security
            { name: 'CORS_ORIGINS', value: corsOrigins }
            { name: 'API_KEY_ENABLED', value: apiKeyEnabled }
          ], apiKeyEnabled == 'true' ? [
            { name: 'API_KEY', secretRef: 'api-key' }
          ] : [], enableRedis ? [
            // Redis Configuration (optional)
            { name: 'REDIS_ENABLED', value: 'true' }
            { name: 'REDIS_HOST', value: redisHost }
            { name: 'REDIS_PORT', value: redisPort }
            { name: 'REDIS_PASSWORD', secretRef: 'redis-password' }
          ] : [
            { name: 'REDIS_ENABLED', value: 'false' }
          ], [
            // Metrics
            { name: 'METRICS_ENABLED', value: metricsEnabled }
            { name: 'METRICS_RETENTION_DAYS', value: metricsRetentionDays }
            
            // Rate Limiting
            { name: 'RATE_LIMIT_ENABLED', value: rateLimitEnabled }
            { name: 'RATE_LIMIT_REQUESTS', value: rateLimitRequests }
            { name: 'RATE_LIMIT_PERIOD', value: rateLimitPeriod }
          ], enableAppInsights ? [
            // Application Insights (optional)
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
          ] : [])
          volumeMounts: [
            {
              volumeName: 'temp-storage'
              mountPath: '/tmp'
            }
          ]
        }
      ]
      volumes: [
        {
          name: 'temp-storage'
          storageType: 'EmptyDir'
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// ============ Outputs ============
output containerAppName string = containerApp.name
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output acrLoginServer string = acrLoginServer
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId
output appInsightsConnectionString string = enableAppInsights ? appInsights.properties.ConnectionString : ''
output appInsightsInstrumentationKey string = enableAppInsights ? appInsights.properties.InstrumentationKey : ''
output containerEnvironmentId string = containerEnvironment.id