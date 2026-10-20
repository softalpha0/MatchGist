// Touchline on Azure Container Apps, with the language agents on Microsoft Foundry.
// Deploy with `azd up` (see README) or `az deployment group create -f infra/main.bicep`.
targetScope = 'resourceGroup'

@description('Base name for resources')
param environmentName string

@description('Azure region')
param location string = resourceGroup().location

@description('Foundry project endpoint, e.g. https://<resource>.services.ai.azure.com/api/projects/<project>. Leave empty to run the agents on the offline backend.')
param foundryProjectEndpoint string = ''

@description('Model deployment name in the Foundry project, e.g. gpt-4.1-mini')
param foundryModel string = ''

@description('Resource ID of the Foundry (AI Services) account, used to grant the app identity access. Optional.')
param foundryAccountId string = ''

@description('Container image. azd overrides this on deploy.')
param image string = 'mcr.microsoft.com/k8se/quickstart:latest'

var token = uniqueString(subscription().id, resourceGroup().id, environmentName)
var tags = { 'azd-env-name': environmentName }

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${token}'
  location: location
  tags: tags
  properties: { sku: { name: 'PerGB2018' }, retentionInDays: 30 }
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'cr${token}'
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: false }
}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${token}'
  location: location
  tags: tags
}

// AcrPull for the app identity
resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, identity.id, 'acrpull')
  scope: registry
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-${token}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-touchline-${token}'
  location: location
  tags: union(tags, { 'azd-service-name': 'web' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  dependsOn: [acrPull]
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        stickySessions: { affinity: 'sticky' }
      }
      registries: [
        { server: registry.properties.loginServer, identity: identity.id }
      ]
    }
    template: {
      containers: [
        {
          name: 'web'
          image: image
          resources: { cpu: json('1.0'), memory: '2Gi' }
          env: [
            { name: 'FOUNDRY_PROJECT_ENDPOINT', value: foundryProjectEndpoint }
            { name: 'FOUNDRY_MODEL', value: foundryModel }
            { name: 'AZURE_CLIENT_ID', value: identity.properties.clientId }
            { name: 'TOUCHLINE_LLM_BUDGET', value: '120' }
            { name: 'TOUCHLINE_MAX_SESSIONS', value: '40' }
          ]
          probes: [
            { type: 'Liveness', httpGet: { path: '/api/health', port: 8000 }, periodSeconds: 30 }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          { name: 'http', http: { metadata: { concurrentRequests: '30' } } }
        ]
      }
    }
  }
}

// Let the app identity call the Foundry project (Azure AI User role), when the account is given.
resource foundryAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = if (!empty(foundryAccountId)) {
  name: empty(foundryAccountId) ? 'unused' : last(split(foundryAccountId, '/'))
}

resource foundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(foundryAccountId)) {
  name: guid(foundryAccountId, identity.id, 'azure-ai-user')
  scope: foundryAccount
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '53ca6127-db72-4b80-b1b0-d745d6d5456d')
  }
}

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = registry.properties.loginServer
output SERVICE_WEB_URI string = 'https://${app.properties.configuration.ingress.fqdn}'
