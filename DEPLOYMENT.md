# Kubernetes Deployment Guide

This guide covers deploying the chatroom microservice application to Kubernetes clusters, with specific instructions for AWS EKS. The same Kubernetes manifests work on other platforms (AKS, GKE, minikube) with minimal modifications.

## 🏗️ Architecture Overview

The application consists of 6 microservices deployed to Kubernetes:
- **Frontend**: Nginx-served React app (Deployment + Service)
- **Chat Backend**: FastAPI WebSocket server (Deployment + Service)
- **Auth Service**: Flask authentication API (Deployment + Service)
- **PostgreSQL**: User authentication database (Deployment + Service + PersistentVolume)
- **MongoDB**: Message and room storage (Deployment + Service + PersistentVolume)
- **Redis**: Pub/Sub for distributed messaging (Deployment + Service)
- **Ingress**: NGINX Ingress Controller for routing

## 📋 Prerequisites

### Required Tools
- **kubectl** - [Install Guide](https://kubernetes.io/docs/tasks/tools/)
- **Git** - To clone the repository

### For AWS EKS (Recommended)
- **AWS CLI** - [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **eksctl** - [Install Guide](https://eksctl.io/installation/)

### For Other Platforms
- **Azure AKS**: Azure CLI and az aks install-cli
- **Google GKE**: gcloud CLI
- **Local Testing**: minikube or Docker Desktop with Kubernetes enabled

---

## 🚀 Quick Deploy (Existing Cluster)

If you already have a Kubernetes cluster configured:

```bash
# Verify cluster connection
kubectl get nodes

# Deploy all services
kubectl apply -f kubernetes/

# Wait for pods to be ready
kubectl get pods --watch

# Get application URL
kubectl get ingress main-ingress
```

**Your application will be available at the Ingress URL shown.**

---

## 📦 Detailed Deployment Steps

### Step 1: Choose Your Platform

<details>
<summary><b>AWS EKS Deployment</b></summary>

#### 1.1 Configure AWS CLI

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

#### 1.2 Create EKS Cluster

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

#### 1.3 Configure kubectl

```powershell
# Update kubeconfig to connect to your cluster
aws eks update-kubeconfig --region us-west-1 --name k8s-chatroom

# Verify connection
kubectl get nodes
```

</details>

<details>
<summary><b>Local Deployment (minikube/Docker Desktop)</b></summary>

```bash
# Start minikube (if using minikube)
minikube start --cpus=4 --memory=8192

# Or enable Kubernetes in Docker Desktop settings

# Verify cluster is running
kubectl get nodes
```

</details>

---

### Step 2: Install NGINX Ingress Controller

```bash
# For AWS EKS
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/aws/deploy.yaml

# For other cloud providers or local
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for ingress controller to be ready (may take 2-3 minutes)
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s

# Verify installation
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

---

### Step 3: Clone Repository and Review Configuration

```bash
# Clone repository if not already done
git clone <your-repo-url>
cd Chatroom-Microservice

# Review Kubernetes manifests
ls kubernetes/

# IMPORTANT: Review and update secrets in kubernetes/secret.yaml
# Change default passwords before deploying to production!
```

**⚠️ Security Note**: The `kubernetes/secret.yaml` file contains base64-encoded credentials. For production, use stronger passwords and consider using tools like:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Kubernetes Sealed Secrets

---

### Step 4: Deploy Secrets

```bash
# Apply Kubernetes secrets
kubectl apply -f kubernetes/secret.yaml

# Verify secrets created
kubectl get secrets
```

---

### Step 5: Deploy Databases

```bash
# Deploy PostgreSQL (Auth database with persistent storage)
kubectl apply -f kubernetes/volume-auth-db.yaml
kubectl apply -f kubernetes/deploy-auth-db.yaml
kubectl apply -f kubernetes/service-db.yaml

# Deploy MongoDB (Message and room storage)
kubectl apply -f kubernetes/deploy-db-mongo.yaml
kubectl apply -f kubernetes/service-db-mongo.yaml

# Deploy Redis (Pub/Sub for distributed messaging)
kubectl apply -f kubernetes/deploy-db-redis.yaml
kubectl apply -f kubernetes/service-db-redis.yaml

# Wait for databases to be ready (may take 2-3 minutes)
kubectl wait --for=condition=ready pod -l run=postgres --timeout=300s
kubectl wait --for=condition=ready pod -l run=mongo --timeout=300s
kubectl wait --for=condition=ready pod -l run=redis --timeout=300s

# Verify all database pods are running
kubectl get pods -l 'run in (postgres,mongo,redis)'
```

---

### Step 6: Deploy Application Services

```bash
# Deploy Auth Service (Flask authentication API)
kubectl apply -f kubernetes/deploy-auth.yaml
kubectl apply -f kubernetes/service-auth.yaml

# Deploy Chat Backend (FastAPI WebSocket server)
kubectl apply -f kubernetes/deploy-chat.yaml
kubectl apply -f kubernetes/service-chat.yaml

# Deploy Frontend (React + Nginx)
kubectl apply -f kubernetes/deploy-frontend.yaml
kubectl apply -f kubernetes/service-frontend.yaml

# Wait for application pods to be ready
kubectl wait --for=condition=ready pod -l run=auth --timeout=180s
kubectl wait --for=condition=ready pod -l run=chat --timeout=180s
kubectl wait --for=condition=ready pod -l run=frontend --timeout=180s

# Verify all application pods are running
kubectl get pods
```

**Expected output**: You should see 6 pods running (postgres, mongo, redis, auth, chat, frontend)

---

### Step 7: Deploy Ingress

```bash
# Apply ingress configuration
kubectl apply -f kubernetes/deploy-ingress.yaml

# Wait for ingress to get an external address (may take 2-3 minutes)
kubectl get ingress main-ingress --watch

# Press Ctrl+C once you see an ADDRESS appear in the output
```

---

### Step 8: Initialize Database with Sample Users

```bash
# Get the Load Balancer URL
LB_URL=$(kubectl get ingress main-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Load Balancer URL: $LB_URL"

# Initialize the auth database with sample users
curl "http://$LB_URL/generate_db"

# Expected response:
# {"message":"Database initialized successfully","users_created":5}
```

**Sample users created**:
- alice / pass123
- bob / qwerty123
- charlie / hello123
- dave / abc123def
- emma / secret123

---

### Step 9: Verify Deployment

```bash
# Check all pods are running
kubectl get pods

# Expected output - all pods should show STATUS: Running and READY: 1/1
# NAME                        READY   STATUS    RESTARTS   AGE
# auth-xxxxx                  1/1     Running   0          5m
# chat-xxxxx                  1/1     Running   0          5m
# frontend-xxxxx              1/1     Running   0          5m
# mongo-xxxxx                 1/1     Running   0          7m
# postgres-xxxxx              1/1     Running   0          7m
# redis-xxxxx                 1/1     Running   0          7m

# Check all services
kubectl get svc

# Check ingress and get public URL
kubectl get ingress main-ingress

# Test individual services
kubectl get pods -l run=auth
kubectl get pods -l run=chat
kubectl get pods -l run=frontend
```

---

### Step 10: Access Your Application

```bash
# Get the application URL
APP_URL=$(kubectl get ingress main-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Your chatroom is available at: http://$APP_URL"

# Open in browser
# Windows PowerShell: Start-Process "http://$APP_URL"
# macOS: open "http://$APP_URL"
# Linux: xdg-open "http://$APP_URL"
```

**🎉 Your application is now deployed!**

Visit the URL in your browser to:
- Chat as a guest immediately
- Register a new account
- Login with sample users

---

## 🛠️ Management Commands

### Viewing Logs
```bash
# View logs for specific services
kubectl logs -l run=auth        # Auth service logs
kubectl logs -l run=chat        # Chat backend logs
kubectl logs -l run=frontend    # Frontend logs

# Follow logs in real-time
kubectl logs -f -l run=auth

# View logs for a specific pod
kubectl get pods                 # Get pod names
kubectl logs <pod-name>

# View last 100 lines
kubectl logs --tail=100 -l run=chat

# View logs from all pods of a service
kubectl logs -l run=chat --all-containers=true
```

### Scaling Deployments
```bash
# Scale up for more traffic
kubectl scale deployment auth --replicas=3
kubectl scale deployment chat --replicas=3
kubectl scale deployment frontend --replicas=2

# Scale down to save resources
kubectl scale deployment chat --replicas=1

# Check current replicas
kubectl get deployments
kubectl get pods
```

**Note**: Chat backend supports horizontal scaling via Redis Pub/Sub!

### Updating Deployments
```bash
# After pushing new Docker images, restart deployments
kubectl rollout restart deployment/auth
kubectl rollout restart deployment/chat
kubectl rollout restart deployment/frontend

# Check rollout status
kubectl rollout status deployment/auth
kubectl rollout status deployment/chat

# View rollout history
kubectl rollout history deployment/chat

# Rollback to previous version
kubectl rollout undo deployment/chat
```

### Troubleshooting
```bash
# Describe a pod for detailed info and events
kubectl describe pod <pod-name>

# Check pod resource usage (requires metrics-server)
kubectl top pods
kubectl top nodes

# Check ingress configuration
kubectl describe ingress main-ingress

# View all resources in current namespace
kubectl get all

# Check pod status and restarts
kubectl get pods --watch

# Execute commands inside a pod
kubectl exec -it <pod-name> -- /bin/sh
kubectl exec -it <pod-name> -- env

# Port forward for local debugging
kubectl port-forward svc/service-auth 5000:5000
kubectl port-forward svc/service-chat 8000:8000
```

### Database Management
```bash
# Connect to PostgreSQL
kubectl exec -it <postgres-pod-name> -- psql -U chatuser -d chatroom

# Connect to MongoDB
kubectl exec -it <mongo-pod-name> -- mongosh chatroom

# Connect to Redis
kubectl exec -it <redis-pod-name> -- redis-cli

# Backup PostgreSQL database
kubectl exec <postgres-pod-name> -- pg_dump -U chatuser chatroom > backup.sql
```

---

## 💰 Cost Optimization

### Pause Cluster (AWS EKS)

Save costs by scaling down when not in use:

```bash
# Scale down all node groups to 0
eksctl scale nodegroup \
  --cluster k8s-chatroom \
  --region us-west-1 \
  --name ng-m7i \
  --nodes 0 \
  --nodes-min 0 \
  --nodes-max 4

# Verify nodes are scaled down
kubectl get nodes
```

**Note**: EKS control plane continues to incur charges (~$0.10/hour)

### Resume Cluster

```bash
# Scale node group back to 2 nodes
eksctl scale nodegroup \
  --cluster k8s-chatroom \
  --region us-west-1 \
  --name ng-m7i \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 4

# Update kubeconfig
aws eks update-kubeconfig --region us-west-1 --name k8s-chatroom

# Wait for nodes to be ready
kubectl get nodes --watch

# Verify all pods restart successfully
kubectl get pods --watch
```

---

## 🗑️ Cleanup

### Delete All Application Resources
```bash
# Delete all Kubernetes resources (keeps cluster)
kubectl delete -f kubernetes/

# Or delete individually
kubectl delete ingress main-ingress
kubectl delete deployment auth chat frontend postgres mongo redis
kubectl delete service service-auth service-chat service-frontend service-db service-db-mongo service-db-redis
kubectl delete pvc postgres-pvc
kubectl delete secret app-secrets
```

### Delete Entire Cluster (AWS EKS)
```bash
# WARNING: This deletes everything including the cluster

# Delete the EKS cluster (takes ~10-15 minutes)
eksctl delete cluster --name k8s-chatroom --region us-west-1

# Verify cluster is deleted
eksctl get cluster --region us-west-1

# Check AWS Console for any lingering resources:
# - Load Balancers
# - EBS Volumes
# - VPC (if created by eksctl)
```

### Delete Local Cluster (minikube)
```bash
minikube delete
```

---

## 💵 Cost Estimates (AWS EKS)

### Monthly Costs (24/7 operation)
- **EKS Control Plane**: ~$0.10/hour = **$73/month**
- **EC2 Nodes** (2x m7i-flex.large): ~$0.08/hour × 2 = **$115/month**
- **Load Balancer** (ALB): ~$0.0225/hour + data transfer = **$16-30/month**
- **EBS Volumes** (databases): ~$0.10/GB-month = **$10-20/month**

**Total estimated cost**: ~$200-250/month

### Cost Optimization Tips
- ✅ Scale to 0 nodes when not in use (save ~$115/month on compute)
- ✅ Use smaller instance types for development (t3.medium ~$30/month)
- ✅ Delete cluster completely when done with project
- ✅ Use spot instances for non-critical workloads
- ✅ Set up auto-scaling to scale down during low traffic

---

## ⚠️ Production Considerations

### Security
1. **Secrets Management**: 
   - Use AWS Secrets Manager, HashiCorp Vault, or Sealed Secrets
   - Never commit real credentials to git
   - Rotate secrets regularly

2. **Network Security**:
   - Configure network policies to restrict pod-to-pod traffic
   - Use AWS Security Groups and NACLs
   - Enable VPC Flow Logs

3. **HTTPS/TLS**:
   - Install cert-manager for automatic SSL certificates
   - Use Let's Encrypt or AWS Certificate Manager
   - Enforce HTTPS-only traffic

### Data Persistence
- **Current setup**: Uses PersistentVolumeClaims for PostgreSQL
- **Production recommendation**:
  - Use managed databases (RDS for PostgreSQL, DocumentDB for MongoDB)
  - Set up automated backups
  - Configure replication for high availability
  - Use ElastiCache for Redis

### Monitoring & Logging
- Install Prometheus + Grafana for metrics
- Use CloudWatch for logs and alarms
- Set up alerts for pod failures, high CPU, memory issues
- Monitor application-level metrics (message latency, WebSocket connections)

### Domain & DNS
- Register a custom domain
- Use Route53 or your DNS provider to point to the Load Balancer
- Configure DNS failover for high availability

### High Availability
- Run multiple replicas: `kubectl scale deployment chat --replicas=3`
- Spread pods across availability zones
- Configure pod anti-affinity rules
- Set up health checks and readiness probes (already configured)

---

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [eksctl Documentation](https://eksctl.io/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)

---

## 🆘 Common Issues

### Pods not starting
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```
Check for: Image pull errors, insufficient resources, config issues

### Ingress not getting external IP
- Wait 3-5 minutes for cloud provider to provision load balancer
- Check ingress controller: `kubectl get pods -n ingress-nginx`
- Verify cloud provider supports LoadBalancer service type

### WebSocket connections failing
- Ensure ingress has WebSocket annotations (already configured)
- Check backend logs: `kubectl logs -l run=chat`
- Verify Redis is running: `kubectl get pods -l run=redis`

### Database connection errors
- Check database pods: `kubectl get pods -l 'run in (postgres,mongo,redis)'`
- Verify secrets are applied: `kubectl get secrets`
- Check service endpoints: `kubectl get endpoints`

---

**Need help?** Check the logs first: `kubectl logs <pod-name>`
