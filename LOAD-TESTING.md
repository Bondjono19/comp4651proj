# Load Testing Guide

This document describes how to run the comprehensive load tests for the chatroom microservice application.

## Prerequisites

### Install k6

**Windows (using Chocolatey):**
```powershell
choco install k6
```

**Windows (using Scoop):**
```powershell
scoop install k6
```

**macOS:**
```bash
brew install k6
```

**Linux:**
```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

**Docker:**
```bash
docker pull grafana/k6:latest
```

## Running Load Tests

### Set Your Environment

First, determine your WebSocket endpoint:

**For local Docker Compose:**
```powershell
$env:WS_URL="ws://localhost:8000/ws"
```

**For AWS EKS:**
```powershell
# Get your Ingress URL
kubectl get ingress -n default
# Example: a1b2c3d4.us-east-1.elb.amazonaws.com
$env:WS_URL="ws://your-ingress-url/ws"
```

**For Azure AKS:**
```powershell
# Get your Ingress URL
kubectl get ingress -n default
# Example: 20.xxx.xxx.xxx
$env:WS_URL="ws://your-ingress-url/ws"
```

### Scenario 1: Baseline Performance

Tests single-instance performance with increasing load (50, 100, 200 users).

```powershell
k6 run --env SCENARIO=baseline --env WS_URL=$env:WS_URL load-test-scenarios.js
```

**Expected Duration:** ~10 minutes

**What to monitor:**
- Single pod CPU/Memory usage
- Message latency at different load levels
- Connection success rate

### Scenario 2: Horizontal Scaling

Tests multi-replica performance (200, 500, 1000 users).

**Before running:** Ensure you have multiple replicas:
```powershell
kubectl scale deployment/chat --replicas=2
# Wait for pods to be ready
kubectl get pods -l app=chat
```

```powershell
k6 run --env SCENARIO=scaling --env WS_URL=$env:WS_URL load-test-scenarios.js
```

**Expected Duration:** ~20 minutes

**What to monitor:**
- Load distribution across pods: `kubectl top pods`
- Cross-instance message delivery
- Redis Pub/Sub metrics

**Test different replica counts:**
```powershell
# Test with 4 replicas
kubectl scale deployment/chat --replicas=4
k6 run --env SCENARIO=scaling --env WS_URL=$env:WS_URL load-test-scenarios.js

# Test with 8 replicas
kubectl scale deployment/chat --replicas=8
k6 run --env SCENARIO=scaling --env WS_URL=$env:WS_URL load-test-scenarios.js
```

### Scenario 3: Burst Traffic

Tests autoscaling response to sudden traffic spikes.

**Before running:** Configure HPA:
```powershell
kubectl autoscale deployment chat --cpu-percent=70 --min=2 --max=8
```

```powershell
k6 run --env SCENARIO=burst --env WS_URL=$env:WS_URL load-test-scenarios.js
```

**Expected Duration:** ~7 minutes

**What to monitor:**
- HPA scaling events: `kubectl get hpa -w`
- Pod creation time
- Performance during scale-up
- Error rates during transition

### Scenario 4: Multi-Room Concurrent Activity

Tests multiple chat rooms with concurrent users.

```powershell
k6 run --env SCENARIO=multiroom --env WS_URL=$env:WS_URL load-test-scenarios.js
```

**Expected Duration:** ~5 minutes

**What to monitor:**
- Redis channel metrics
- Per-room message isolation
- MongoDB write patterns
- Cross-room interference (should be none)

### Scenario 5: Long-Duration Stability

Tests connection stability and resource management over time.

```powershell
k6 run --env SCENARIO=stability --env WS_URL=$env:WS_URL load-test-scenarios.js
```

**Expected Duration:** ~30 minutes

**What to monitor:**
- Memory growth over time
- Connection drop rate
- Long-term latency trends
- Resource leaks

## Collecting Metrics

### During Tests

**Monitor Kubernetes resources:**
```powershell
# Watch pod metrics
kubectl top pods -l app=chat

# Watch HPA status
kubectl get hpa -w

# View pod logs
kubectl logs -f deployment/chat

# View all pod resource usage
kubectl top pods --sort-by=cpu
```

**Monitor individual pods:**
```powershell
# Get detailed pod metrics
kubectl describe pod <pod-name>

# View pod events
kubectl get events --sort-by=.metadata.creationTimestamp
```

### After Tests

k6 automatically generates a summary. For detailed analysis:

```powershell
# Run with JSON output
k6 run --env SCENARIO=baseline --env WS_URL=$env:WS_URL --out json=results-baseline.json load-test-scenarios.js

# Run with CSV output
k6 run --env SCENARIO=baseline --env WS_URL=$env:WS_URL --out csv=results-baseline.csv load-test-scenarios.js
```

### Advanced: Prometheus + Grafana Integration

For production-grade monitoring:

```powershell
# Install Prometheus operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack

# Run k6 with Prometheus remote write
k6 run --env SCENARIO=baseline --env WS_URL=$env:WS_URL `
  --out experimental-prometheus-rw `
  load-test-scenarios.js
```

## Interpreting Results

### Key Metrics to Extract

1. **Message Latency (p50, p95, p99)**
   - Target: p95 < 200ms, p99 < 500ms
   - Measure of real-time performance

2. **Connection Success Rate**
   - Target: > 99%
   - Indicates stability

3. **Throughput (messages/second)**
   - Measure of system capacity

4. **Error Rate**
   - Target: < 1%
   - Critical for reliability

5. **Resource Utilization**
   - CPU: Should stay < 80% under normal load
   - Memory: Should be stable (no leaks)

### Example Analysis

```
Scenario: Baseline (200 VUs)
- p95 latency: 145ms ✓ (< 200ms target)
- Success rate: 99.8% ✓ (> 99% target)
- CPU usage: 85% ⚠️ (approaching limit)
- Memory: 620MB ✓ (stable)

Conclusion: Single instance handles 200 users but near capacity.
Recommendation: Scale to 2+ replicas for production.
```

## Troubleshooting

### Connection Refused Errors

```powershell
# Check if service is accessible
kubectl get svc
kubectl port-forward svc/chat-service 8000:8000

# Test locally
curl http://localhost:8000/health
```

### High Error Rates

```powershell
# Check pod logs for errors
kubectl logs -l app=chat --tail=100

# Check pod status
kubectl describe pods -l app=chat
```

### Inconsistent Results

```powershell
# Ensure clean state between tests
kubectl delete pods -l app=chat
kubectl rollout status deployment/chat

# Clear Redis cache
kubectl exec -it deployment/redis -- redis-cli FLUSHALL
```

## Generating Report Data

To populate your report with actual data:

1. Run all 5 scenarios
2. Save outputs to JSON files
3. Extract key metrics:

```powershell
# Run all scenarios and save results
foreach ($scenario in @('baseline', 'scaling', 'burst', 'multiroom', 'stability')) {
    Write-Host "Running scenario: $scenario"
    k6 run --env SCENARIO=$scenario --env WS_URL=$env:WS_URL `
           --out json="results-$scenario.json" `
           load-test-scenarios.js
    
    # Wait between tests
    Start-Sleep -Seconds 60
}
```

4. Analyze results and update report tables with actual measurements

## Cloud-Specific Notes

### AWS EKS

- Use Application Load Balancer for WebSocket support
- Enable sticky sessions if needed
- Monitor ELB metrics in CloudWatch

### Azure AKS

- Use Azure Load Balancer Standard SKU
- Enable session affinity in Ingress if needed
- Monitor metrics in Azure Monitor

## Best Practices

1. **Always warm up** - Run a short test first to warm up caches
2. **Monitor throughout** - Watch Kubernetes metrics during tests
3. **Clean between tests** - Reset state between major test runs
4. **Save raw data** - Keep JSON outputs for detailed analysis
5. **Document environment** - Note replica counts, resource limits, cloud platform
6. **Repeat tests** - Run each scenario 2-3 times for consistency

## Safety Limits

- Don't exceed 2000 VUs without increasing cluster capacity
- Monitor cloud costs during extended testing
- Set up billing alerts before large-scale tests
- Use namespace resource quotas to prevent runaway costs

## Questions?

Check the main README.md or consult the report's experimental methodology section.
