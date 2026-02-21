# AKS Patterns

---

## Workload Identity (replaces AAD Pod Identity)

Azure Workload Identity uses OIDC federation — Kubernetes service account tokens are exchanged for Azure access tokens without long-lived secrets or in-cluster agents.

**AAD Pod Identity is deprecated.** Migrate to Workload Identity.

### Setup

```bash
# 1. Enable OIDC issuer and Workload Identity on the cluster
az aks update \
  --name <cluster> \
  --resource-group <rg> \
  --enable-oidc-issuer \
  --enable-workload-identity

OIDC_ISSUER=$(az aks show --name <cluster> -g <rg> \
  --query "oidcIssuerProfile.issuerUrl" -o tsv)

# 2. Create managed identity for the workload
az identity create --name <workload-identity> --resource-group <rg>
CLIENT_ID=$(az identity show --name <workload-identity> -g <rg> --query clientId -o tsv)
PRINCIPAL_ID=$(az identity show --name <workload-identity> -g <rg> --query principalId -o tsv)

# 3. Create federated credential
az identity federated-credential create \
  --name <federated-cred-name> \
  --identity-name <workload-identity> \
  --resource-group <rg> \
  --issuer "$OIDC_ISSUER" \
  --subject "system:serviceaccount:<k8s-namespace>:<k8s-service-account>" \
  --audience api://AzureADTokenExchange

# 4. Assign Azure roles to the managed identity (e.g., Key Vault access)
az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope $(az keyvault show --name <vault> -g <rg> --query id -o tsv)
```

### Kubernetes Objects

```yaml
# Service account — annotated with managed identity client ID
apiVersion: v1
kind: ServiceAccount
metadata:
  name: <k8s-service-account>
  namespace: <k8s-namespace>
  annotations:
    azure.workload.identity/client-id: "<client-id>"
---
# Pod — labeled to use Workload Identity
apiVersion: v1
kind: Pod
metadata:
  name: myapp
  namespace: <k8s-namespace>
  labels:
    azure.workload.identity/use: "true"
spec:
  serviceAccountName: <k8s-service-account>
  containers:
    - name: myapp
      image: myapp:latest
      # AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_FEDERATED_TOKEN_FILE
      # are injected automatically by the webhook
```

The `DefaultAzureCredential` in the application code picks up the injected environment variables automatically via `WorkloadIdentityCredential`.

---

## ACR Integration

Attach an Azure Container Registry to AKS so nodes can pull images without explicit credentials.

```bash
# Attach ACR — grants AcrPull to the kubelet managed identity
az aks update \
  --name <cluster> \
  --resource-group <rg> \
  --attach-acr <registry-name>

# Detach
az aks update --name <cluster> --resource-group <rg> --detach-acr <registry-name>

# Verify attachment
az aks check-acr \
  --name <cluster> \
  --resource-group <rg> \
  --acr <registry-name>.azurecr.io
```

### Build and Push Images

```bash
# Build and push directly with ACR Tasks (no local Docker required)
az acr build \
  --registry <registry-name> \
  --image myapp:$(git rev-parse --short HEAD) \
  .

# Geo-replication — replicate registry to multiple regions
az acr replication create \
  --registry <registry-name> \
  --location westeurope
```

---

## KEDA (Event-Driven Autoscaling)

KEDA scales Deployments based on external event sources (Service Bus queue depth, Event Hubs lag, HTTP request rate, etc.).

### Install KEDA via Helm

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace
```

### ScaledObject: Azure Service Bus

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: myapp-scaler
  namespace: <k8s-namespace>
spec:
  scaleTargetRef:
    name: myapp-deployment
  minReplicaCount: 0      # Scale to zero when queue is empty
  maxReplicaCount: 20
  pollingInterval: 15
  cooldownPeriod: 60
  triggers:
    - type: azure-servicebus
      metadata:
        queueName: <queue-name>
        namespace: <servicebus-namespace>
        messageCount: "5"    # Scale up when queue depth > 5 per replica
      authenticationRef:
        name: keda-servicebus-auth
---
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: keda-servicebus-auth
  namespace: <k8s-namespace>
spec:
  podIdentity:
    provider: azure-workload  # Use Workload Identity — no secrets
```

---

## Cluster Configuration Best Practices

```bash
# Enable cluster autoscaler
az aks update \
  --name <cluster> \
  --resource-group <rg> \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 10

# Enable Azure CNI Overlay (preferred networking for large clusters)
# Set at cluster creation time only — cannot change after creation

# Enable Azure Monitor / Container Insights
az aks enable-addons \
  --addons monitoring \
  --name <cluster> \
  --resource-group <rg> \
  --workspace-resource-id <log-analytics-workspace-id>

# Get credentials to kubectl
az aks get-credentials --name <cluster> --resource-group <rg>

# Upgrade cluster
az aks upgrade --name <cluster> --resource-group <rg> --kubernetes-version 1.29
```

---

## AKS MCP Server

The `aks-mcp` server provides Kubernetes operations on AKS for AI agents (MIT license, GA Aug 2025).

```bash
npm install -g @azure/aks-mcp
npx @azure/aks-mcp
```

Compatible with Claude, Cursor, and GitHub Copilot. Use for AI-assisted cluster diagnostics, workload inspection, and configuration review.

**Note:** The main Azure MCP Server has an `aks` namespace, but `aks-mcp` provides deeper Kubernetes-native operations (pod logs, events, resource inspection) that the Azure control plane API does not expose.

---

## Anti-Patterns

- **AAD Pod Identity** — deprecated; use Workload Identity.
- **`imagePullSecrets` with ACR credentials in manifests** — attach the ACR to the cluster instead so the kubelet pulls credentials automatically.
- **Running privileged containers** (`securityContext.privileged: true`) — use more targeted capabilities (`NET_ADMIN`, `SYS_TIME`) if truly needed.
- **Unset resource requests and limits** — without these, the scheduler cannot make informed decisions; unbounded containers starve neighbors.
- **Not using node selectors or taints/tolerations for specialized node pools** — GPU or memory-optimized nodes are wasted if any workload can land on them.
- **Single node pool with mixed workloads** — use separate system and user node pools; system pool runs Kubernetes components, user pool runs application workloads.
