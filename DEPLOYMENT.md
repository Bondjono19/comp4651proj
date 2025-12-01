# Step-by-Step Guide: Deploying Chatroom Microservice to AWS EKS

## Prerequisites

Install the following tools:
- **AWS CLI** - [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **eksctl** - [Install Guide](https://eksctl.io/installation/)
- **kubectl** - [Install Guide](https://kubernetes.io/docs/tasks/tools/)
- **Docker** (optional, for local testing)

---

## Step 1: Configure AWS CLI

```powershell
# Configure AWS credentials
aws configure

# Enter when prompted:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-west-1)
# - Default output format (json)

# Verify credentials
aws sts get-caller-identity
```

---

## Step 2: Create EKS Cluster

```powershell
# Create EKS cluster with eksctl (takes ~15-20 minutes)
eksctl create cluster `
  --name k8s-chatroom `
  --region us-west-1 `
  --nodegroup-name ng-m7i `
  --node-type m7i-flex.large `
  --nodes 2 `
  --nodes-min 2 `
  --nodes-max 4 `
  --managed

# Output will show cluster creation progress
```

---

## Step 3: Configure kubectl

```powershell
# Update kubeconfig to connect to your cluster
aws eks update-kubeconfig --region us-west-1 --name k8s-chatroom

# Verify connection
kubectl get nodes

# Expected output:
# NAME                                          STATUS   ROLES    AGE   VERSION
# ip-192-168-x-x.us-west-1.compute.internal    Ready    <none>   1m    v1.32.x
```

---

## Step 4: Install NGINX Ingress Controller

```powershell
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/aws/deploy.yaml

# Wait for ingress controller to be ready (may take 2-3 minutes)
kubectl wait --namespace ingress-nginx `
  --for=condition=ready pod `
  --selector=app.kubernetes.io/component=controller `
  --timeout=300s

# Verify installation
kubectl get pods -n ingress-nginx
```

---

## Step 5: Deploy Secrets

```powershell
# Navigate to project directory
cd <Project Directory>

# Apply Kubernetes secrets
kubectl apply -f kubernetes/secret.yaml

# Verify secrets created
kubectl get secrets
```

---

## Step 6: Deploy Databases

```powershell
# Deploy PostgreSQL (Auth database)
kubectl apply -f kubernetes/volume-auth-db.yaml
kubectl apply -f kubernetes/deploy-auth-db.yaml
kubectl apply -f kubernetes/service-db.yaml

# Deploy MongoDB (Chat database)
kubectl apply -f kubernetes/deploy-db-mongo.yaml
kubectl apply -f kubernetes/service-db-mongo.yaml

# Deploy Redis (Session cache)
kubectl apply -f kubernetes/deploy-db-redis.yaml
kubectl apply -f kubernetes/service-db-redis.yaml

# Wait for databases to be ready (may take 2-3 minutes)
kubectl wait --for=condition=ready pod -l run=postgres --timeout=180s
kubectl wait --for=condition=ready pod -l run=mongo --timeout=180s
kubectl wait --for=condition=ready pod -l run=redis --timeout=180s

# Verify all database pods are running
kubectl get pods -l 'run in (postgres,mongo,redis)'
```

---

## Step 7: Deploy Application Services

```powershell
# Deploy Auth Service
kubectl apply -f kubernetes/deploy-auth.yaml
kubectl apply -f kubernetes/service-auth.yaml

# Deploy Chat Service
kubectl apply -f kubernetes/deploy-chat.yaml
kubectl apply -f kubernetes/service-chat.yaml

# Deploy Frontend Service
kubectl apply -f kubernetes/deploy-frontend.yaml
kubectl apply -f kubernetes/service-frontend.yaml

# Wait for application pods to be ready
kubectl wait --for=condition=ready pod -l run=auth --timeout=120s
kubectl wait --for=condition=ready pod -l run=chat --timeout=120s
kubectl wait --for=condition=ready pod -l run=frontend --timeout=120s

# Verify all application pods are running
kubectl get pods
```

---

## Step 8: Deploy Ingress

```powershell
# Apply ingress configuration
kubectl apply -f kubernetes/deploy-ingress.yaml

# Wait for ingress to get an external address (may take 2-3 minutes)
kubectl get ingress main-ingress --watch

# Press Ctrl+C once you see an ADDRESS appear
```

---

## Step 9: Initialize Auth Database

```powershell
# Get the Load Balancer URL
$LB_URL = kubectl get ingress main-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
echo "Load Balancer URL: $LB_URL"

# Initialize the auth database tables
curl "http://$LB_URL/generate_db"

# Expected response:
# {"message":"Database initialized successfully"}
```

---

## Step 10: Verify Deployment

```powershell
# Check all pods are running
kubectl get pods

# Expected output - all pods should show STATUS: Running
# NAME                        READY   STATUS    RESTARTS   AGE
# auth-xxxxx                  1/1     Running   0          5m
# chat-xxxxx                  1/1     Running   0          5m
# frontend-xxxxx              1/1     Running   0          5m
# mongo-xxxxx                 1/1     Running   0          7m
# postgres-xxxxx              1/1     Running   0          7m
# redis-xxxxx                 1/1     Running   0          7m

# Check services
kubectl get svc

# Check ingress and get public URL
kubectl get ingress main-ingress

# Get just the URL
kubectl get ingress main-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

---

## Step 11: Access Your Application

```powershell
# Get the application URL
$APP_URL = kubectl get ingress main-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
echo "Your chatroom is available at: http://$APP_URL"

# Open in browser (Windows)
Start-Process "http://$APP_URL"
```

---

## Useful Management Commands

### View Logs
```powershell
# View logs for specific services
kubectl logs -l run=auth
kubectl logs -l run=chat
kubectl logs -l run=frontend

# Follow logs in real-time
kubectl logs -f -l run=auth

# View logs for a specific pod
kubectl logs <pod-name>
```

### Scale Deployments
```powershell
# Scale up/down replicas
kubectl scale deployment auth --replicas=3
kubectl scale deployment chat --replicas=3
kubectl scale deployment frontend --replicas=3

# Check current replicas
kubectl get deployments
```

### Update Deployments
```powershell
# After pushing new Docker images, restart deployments
kubectl rollout restart deployment/auth
kubectl rollout restart deployment/chat
kubectl rollout restart deployment/frontend

# Check rollout status
kubectl rollout status deployment/auth
```

### Troubleshooting
```powershell
# Describe a pod for detailed info
kubectl describe pod <pod-name>

# Get pod resource usage
kubectl top pods

# Get node resource usage
kubectl top nodes

# Check ingress details
kubectl describe ingress main-ingress

# View all resources
kubectl get all
```

---

## Pause/Resume Cluster (Save Costs)

### Pause (Scale to 0 nodes)
```powershell
# Scale down all node groups to 0
eksctl scale nodegroup --cluster k8s-chatroom --region us-west-1 --name ng-m7i --nodes 0 --nodes-min 0 --nodes-max 4

# Verify nodes are gone
kubectl get nodes
```

### Resume (Scale back up)
```powershell
# Scale node group back to 2 nodes
eksctl scale nodegroup --cluster k8s-chatroom --region us-west-1 --name ng-m7i --nodes 2 --nodes-min 2 --nodes-max 4

# Update kubeconfig
aws eks update-kubeconfig --region us-west-1 --name k8s-chatroom

# Wait for nodes to be ready
kubectl get nodes --watch

# Verify all pods restart successfully
kubectl get pods
```

---

## Complete Cleanup (Delete Everything)

```powershell
# WARNING: This deletes the entire cluster and all data

# Delete the cluster (takes ~10-15 minutes)
eksctl delete cluster --name k8s-chatroom --region us-west-1

# Verify cluster is deleted
eksctl get cluster --region us-west-1

# Clean up any lingering load balancers in AWS Console if needed
```

---

## Cost Considerations

- **EKS Control Plane**: ~$0.10/hour ($73/month)
- **EC2 Nodes**: m7i-flex.large = ~$0.08/hour per node
- **Load Balancer**: ~$0.0225/hour + data transfer
- **EBS Volumes**: ~$0.10/GB-month

**Estimated monthly cost for 2 nodes running 24/7**: ~$200-250/month

**To minimize costs**:
- Scale to 0 nodes when not in use
- Delete cluster when done with project
- Use smaller instance types for testing

---

## Important Notes

1. **Container Images**: Ensure your Docker images in `ghcr.io/bondjono19/*` are publicly accessible or configure image pull secrets

2. **Persistent Data**: Database data is stored in pods - will be lost if pods are deleted. Consider adding PersistentVolumeClaims for production

3. **Security**: Update secrets in `kubernetes/secret.yaml` with strong passwords for production use

4. **Domain Name**: For production, map a custom domain to the load balancer URL using Route53 or your DNS provider

5. **HTTPS**: Add TLS certificates using cert-manager and Let's Encrypt for production
