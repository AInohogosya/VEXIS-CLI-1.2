# Deployment Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Deployment Prerequisites](#deployment-prerequisites)
3. [Deployment Strategies](#deployment-strategies)
4. [Local Development Deployment](#local-development-deployment)
5. [Production Deployment](#production-deployment)
6. [Docker Deployment](#docker-deployment)
7. [Kubernetes Deployment](#kubernetes-deployment)
8. [Cloud Deployment](#cloud-deployment)
9. [Scaling and High Availability](#scaling-and-high-availability)
10. [Backup and Recovery](#backup-and-recovery)
11. [Monitoring and Maintenance](#monitoring-and-maintenance)
12. [Security Considerations](#security-considerations)
13. [Troubleshooting](#troubleshooting)

## Introduction

Deploying the 6-Phase Architecture system requires careful planning and execution to ensure optimal performance, security, and reliability. This guide provides comprehensive instructions for deploying the system in various environments, from local development to enterprise production.

### Deployment Objectives

- **Zero Downtime**: Minimize service interruptions during deployment
- **High Availability**: Ensure system availability and reliability
- **Security**: Implement robust security measures
- **Scalability**: Support horizontal and vertical scaling
- **Observability**: Comprehensive monitoring and logging
- **Disaster Recovery**: Implement backup and recovery procedures

## Deployment Prerequisites

### System Requirements

#### Minimum Requirements

- **CPU**: 2 cores
- **Memory**: 4 GB RAM
- **Storage**: 20 GB free space
- **Network**: 1 Gbps
- **Operating System**: Linux, macOS, or Windows

#### Recommended Requirements

- **CPU**: 8+ cores
- **Memory**: 16 GB RAM (32 GB recommended)
- **Storage**: 100 GB SSD (200 GB recommended)
- **Network**: 10 Gbps with low latency
- **Operating System**: Linux (Ubuntu 20.04+ or equivalent)

### Software Prerequisites

- **Python**: 3.8 or higher
- **Docker**: 20.10 or higher (optional)
- **Kubernetes**: 1.24 or higher (optional)
- **PostgreSQL**: 14 or higher (optional)
- **Redis**: 6.2 or higher (optional)
- **Nginx**: 1.18 or higher (optional)

### Network Requirements

#### Ports

| Port | Protocol | Service | Description |
|------|----------|---------|-------------|
| 80 | TCP | HTTP | Web interface (optional) |
| 443 | TCP | HTTPS | Secure web interface (optional) |
| 5432 | TCP | PostgreSQL | Database connection |
| 6379 | TCP | Redis | Cache and session storage |
| 8000 | TCP | API | REST API endpoint |
| 9090 | TCP | Prometheus | Monitoring endpoint |
| 3000 | TCP | Grafana | Dashboard (optional) |

#### Firewall Rules

- Allow inbound traffic on required ports
- Restrict access to management interfaces
- Implement VPN or bastion host for secure access
- Use security groups or firewall rules for network segmentation

## Deployment Strategies

### Deployment Options

#### Local Development

- **Use Case**: Development, testing, and demonstration
- **Environment**: Single machine, local network
- **Scale**: Single instance
- **Persistence**: Local storage

#### Production Deployment

- **Use Case**: Production workloads and enterprise deployment
- **Environment**: Data center or cloud infrastructure
- **Scale**: Clustered deployment with load balancing
- **Persistence**: Distributed storage with backup

#### Hybrid Deployment

- **Use Case**: Mixed on-premises and cloud deployment
- **Environment**: Multi-cloud or hybrid cloud
- **Scale**: Distributed deployment with federation
- **Persistence**: Multi-region storage with replication

### Deployment Patterns

#### Rolling Deployment

- **Description**: Gradual replacement of instances with new version
- **Advantages**: Zero downtime, gradual rollout
- **Disadvantages**: Longer deployment time, rollback complexity

#### Blue-Green Deployment

- **Description**: Parallel environments with traffic switching
- **Advantages**: Zero downtime, instant rollback
- **Disadvantages**: Resource intensive, complex routing

#### Canary Deployment

- **Description**: Gradual traffic shifting to new version
- **Advantages**: Risk reduction, real-time monitoring
- **Disadvantages**: Complex routing, monitoring requirements

## Local Development Deployment

### Quick Start

```bash
# Clone the repository
git clone https://github.com/AInohogosya/VEXIS-CLI-3.git
cd VEXIS-CLI-3

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
python3 init_config.py --default

# Start the development server
python3 run.py --dev
```

### Development Configuration

```yaml
# config-development.yaml
development:
  api:
    preferred_provider: "localhost"
    local_endpoint: "http://localhost:11434"
    timeout: 60

  engine:
    max_iterations: 100
    enable_phase_logging: true
    auto_recovery: false

  database:
    host: "localhost"
    port: 5432
    name: "vexis_dev"
    username: "vexis"
    password: "dev_password"

  redis:
    host: "localhost"
    port: 6379
    password: ""

  monitoring:
    enabled: false

  logging:
    level: "DEBUG"
    file: "vexis_dev.log"
```

### Local Database Setup

```bash
# Install PostgreSQL
sudo apt-get install postgresql  # Ubuntu/Debian
brew install postgresql          # macOS

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE vexiscore_dev;"
sudo -u postgres psql -c "CREATE USER vexis WITH PASSWORD 'dev_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE vexiscore_dev TO vexis;"

# Initialize database schema
python3 manage.py migrate
```

## Production Deployment

### Production Configuration

```yaml
# config-production.yaml
production:
  api:
    preferred_provider: "groq"
    local_endpoint: "http://localhost:11434"
    timeout: 180
    max_retries: 3
    auto_fallback: true

  engine:
    phase_timeout: 3600
    task_timeout: 7200
    max_iterations: 500
    enable_phase_logging: false
    auto_recovery: true

  database:
    host: "db.vexis.example.com"
    port: 5432
    name: "vexis_prod"
    username: "vexis_prod"
    password: "${DB_PASSWORD}"
    ssl_mode: "require"

  redis:
    host: "redis.vexis.example.com"
    port: 6379
    password: "${REDIS_PASSWORD}"

  security:
    encryption_enabled: true
    api_key_rotation: "30d"
    audit_logging: true
    compliance_level: "enterprise"

  monitoring:
    enabled: true
    sampling_rate: 1.0
    alert_thresholds:
      latency_p95: 10000
      error_rate: 0.01
      throughput: 50

  logging:
    level: "INFO"
    file: "/var/log/vexis/vexis.log"
    max_file_size: 104857600  # 100MB
    retention_days: 30
```

### Production Database Setup

```bash
# Install and configure PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Configure PostgreSQL for production
sudo -u postgres psql -c "CREATE DATABASE vexiscore_prod;"
sudo -u postgres psql -c "CREATE USER vexis_prod WITH PASSWORD 'strong_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE vexiscore_prod TO vexis_prod;"

# Configure SSL for PostgreSQL
sudo -u postgres psql -c "ALTER USER vexis_prod SET ssl = on;"

# Initialize production database
python3 manage.py migrate --config production.yaml
```

### Systemd Service Configuration

```ini
# /etc/systemd/system/vexis.service
[Unit]
Description=VEXIS-CLI 6-Phase Architecture System
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=vexis
Group=vexis
WorkingDirectory=/opt/vexis
Environment="PATH=/opt/vexis/venv/bin"
Environment="CONFIG_FILE=/opt/vexis/config/production.yaml"
ExecStart=/opt/vexis/venv/bin/python3 /opt/vexis/run.py --config /opt/vexis/config/production.yaml
Restart=on-failure
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=vexis

[Install]
WantedBy=multi-user.target
```

### Service Management

```bash
# Enable and start the service
sudo systemctl enable vexiscore
sudo systemctl start vexiscore

# Check service status
sudo systemctl status vexiscore

# View logs
sudo journalctl -u vexiscore -f

# Restart the service
sudo systemctl restart vexiscore

# Stop the service
sudo systemctl stop vexiscore
```

## Docker Deployment

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  # VEXIS Core Service
  vexiscore:
    image: vexiscore:latest
    container_name: vexiscore
    restart: unless-stopped
    environment:
      - CONFIG_FILE=/config/production.yaml
    volumes:
      - ./config:/config
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - vexiscore-network

  # PostgreSQL Database
  postgres:
    image: postgres:14
    container_name: vexiscore-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: vexiscore_prod
      POSTGRES_USER: vexiscore_prod
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - vexiscore-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U vexiscore_prod"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: vexiscore-redis
    restart: unless-stopped
    environment:
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - vexiscore-network
    command: redis-server --requirepass ${REDIS_PASSWORD}

  # Grafana Dashboard
  grafana:
    image: grafana/grafana:8.5.7
    container_name: vexiscore-grafana
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    depends_on:
      - vexiscore
    networks:
      - vexiscore-network

  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: vexiscore-prometheus
    restart: unless-stopped
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - vexiscore-network

networks:
  vexiscore-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  grafana_data:
  prometheus_data:
```

### Docker Deployment Commands

```bash
# Build and start services
docker-compose up -d

# View running services
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild after changes
docker-compose build
docker-compose up -d

# Execute database migrations
docker-compose run --rm vexiscore python3 manage.py migrate
```

## Kubernetes Deployment

### Kubernetes manifests

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vexiscore
  namespace: vexiscore
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vexiscore
  template:
    metadata:
      labels:
        app: vexiscore
    spec:
      containers:
      - name: vexiscore
        image: vexiscore:latest
        ports:
        - containerPort: 8000
        env:
        - name: CONFIG_FILE
          value: /config/production.yaml
        volumeMounts:
        - name: config-volume
          mountPath: /config
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: vexiscore-service
  namespace: vexiscore
spec:
  selector:
    app: vexiscore
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

```yaml
# config-map.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vexiscore-config
  namespace: vexiscore
data:
  production.yaml: |
    api:
      preferred_provider: "groq"
      timeout: 180
    engine:
      phase_timeout: 3600
      task_timeout: 7200
    security:
      encryption_enabled: true
```

```yaml
# persistent-volume.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: vexiscore-pv
  namespace: vexiscore
spec:
  storageClassName: standard
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteMany
  nfs:
    path: /exports/vexis
    server: nfs-server.example.com
```

### Kubernetes Deployment Commands

```bash
# Create namespace
kubectl create namespace vexiscore

# Apply configuration
kubectl apply -f config-map.yaml
kubectl apply -f persistent-volume.yaml

# Deploy application
kubectl apply -f deployment.yaml

# Verify deployment
kubectl get pods -n vexiscore
kubectl get svc -n vexiscore

# View logs
kubectl logs -f deployment/vexis -n vexiscore

# Scale deployment
kubectl scale deployment vexiscore --replicas=5 -n vexiscore

# Update deployment
kubectl set image deployment/vexis vexiscore=vexis:2.1.0 -n vexiscore
```

## Cloud Deployment

### AWS Deployment

#### AWS Architecture

```
VPC (Virtual Private Cloud)
├── Public Subnet
│   ├── Load Balancer (ALB)
│   └── NAT Gateway
└── Private Subnet
    ├── ECS Cluster (VEXIS Core)
    ├── RDS PostgreSQL
    └── ElastiCache Redis
```

#### AWS CloudFormation Template

```yaml
# aws-deployment.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: VEXIS 6-Phase Architecture Deployment on AWS

Parameters:
  EnvironmentName:
    Type: String
    Default: vexiscore
    Description: Environment name

Resources:
  # VPC
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsSupport: true
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Ref EnvironmentName

  # Public Subnet
  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      MapPublicIpOnLaunch: true

  # Private Subnet
  PrivateSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24

  # Internet Gateway
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties: {}

  # Attach Internet Gateway to VPC
  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Ref EnvironmentName

  # ECS Service
  ECSService:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref ECSTaskDefinition
      DesiredCount: 3
      LoadBalancer:
        Type: ApplicationLoadBalancer
        SecurityGroup: !Ref LoadBalancerSecurityGroup
        Subnet: !Ref PublicSubnet
        Listener:
          Port: 80
          Protocol: HTTP

  # ECS Task Definition
  ECSTaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      ContainerDefinitions:
        - Name: vexiscore
          Image: !Ref ContainerImage
          Memory: 2048
          Cpu: 1024
          Environment:
            - Name: CONFIG_FILE
              Value: /config/production.yaml
          MountPoints:
            - SourceVolume: config
              ContainerPath: /config
```

#### AWS Deployment Commands

```bash
# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file aws-deployment.yaml \
  --stack-name vexiscore \
  --parameter-overrides EnvironmentName=production \
  --capabilities CAPABILITY_IAM

# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name vexiscore

# Update stack
aws cloudformation deploy \
  --template-file aws-deployment.yaml \
  --stack-name vexiscore \
  --parameter-overrides EnvironmentName=production \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset
```

### Azure Deployment

#### Azure Architecture

```
Resource Group
├── Virtual Network
│   ├── Subnet (VEXIS Core)
│   ├── Subnet (Database)
│   └── Subnet (Cache)
├── Azure Kubernetes Service (AKS)
├── Azure Database for PostgreSQL
└── Azure Cache for Redis
```

#### Azure Resource Manager Template

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environmentName": {
      "type": "String",
      "defaultValue": "vexis-prod"
    }
  },
  "variables": {
    "vnetAddressPrefix": "10.0.0.0/16",
    "subnetCorePrefix": "10.0.1.0/24",
    "subnetDbPrefix": "10.0.2.0/24",
    "subnetCachePrefix": "10.0.3.0/24"
  },
  "resources": [
    {
      "type": "Microsoft.Resources/resourceGroups",
      "apiVersion": "2021-01-01",
      "name": "[parameters('environmentName')]",
      "location": "[resourceGroup().location]"
    },
    {
      "type": "Microsoft.Network/virtualNetworks",
      "apiVersion": "2021-03-15",
      "name": "[concat(parameters('environmentName'), '-vnet')]",
      "location": "[resourceGroup().location]",
      "dependsOn": [
        "[resourceId('Microsoft.Resources/resourceGroups/', parameters('environmentName'))]"
      ],
      "properties": {
        "addressSpace": {
          "addressPrefixes": [
            "[variables('vnetAddressPrefix')]"
          ]
        },
        "subnets": [
          {
            "name": "core-subnet",
            "properties": {
              "addressPrefix": "[variables('subnetCorePrefix')]",
              "privateLinkServiceNetworkPolicies": "Disabled"
            }
          },
          {
            "name": "db-subnet",
            "properties": {
              "addressPrefix": "[variables('subnetDbPrefix')]"
            }
          },
          {
            "name": "cache-subnet",
            "properties": {
              "addressPrefix": "[variables('subnetCachePrefix')]"
            }
          }
        ]
      }
    }
  ]
}
```

#### Azure Deployment Commands

```bash
# Deploy Azure resources
az deployment group create \
  --resource-group vexiscore-prod \
  --template-file azure-deployment.json \
  --parameters environmentName=vexis-prod

# Get deployment outputs
az deployment group show \
  --resource-group vexiscore-prod \
  --name deployment

# Update deployment
az deployment group create \
  --resource-group vexiscore-prod \
  --template-file azure-deployment.json \
  --parameters environmentName=vexis-prod
```

## Scaling and High Availability

### Horizontal Scaling

```yaml
# Horizontal Pod Autoscaler (Kubernetes)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vexiscore-hpa
  namespace: vexiscore
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vexiscore
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

### Load Balancing

```nginx
# Nginx load balancer configuration
upstream vexiscore_backend {
  least_conn;
  server vexiscore-1:8000 weight=1 max_fails=3 fail_timeout=30s;
  server vexiscore-2:8000 weight=1 max_fails=3 fail_timeout=30s;
  server vexiscore-3:8000 weight=1 max_fails=3 fail_timeout=30s;
}

server {
  listen 80;
  server_name api.vexis.example.com;

  location / {
    proxy_pass http://vexis_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

### Health Checks and Self-Healing

```yaml
# Kubernetes health checks
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2

startupProbe:
  httpGet:
    path: /startup
    port: 8000
  initialDelaySeconds: 60
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 30
```

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL database backup
pg_dump -h localhost -p 5432 -U vexis_prod -d vexiscore_prod \
  --format=c --file=vexis_backup_$(date +%Y%m%d).dump

# Compressed backup
pg_dump -h localhost -p 5432 -U vexis_prod -d vexiscore_prod \
  --format=c --file=vexis_backup.dump | gzip > vexiscore_backup_$(date +%Y%m%d).dump.gz

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/vexis"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/vexis_backup_$DATE.dump"

pg_dump -h localhost -p 5432 -U vexis_prod -d vexiscore_prod \
  --format=c --file=$BACKUP_FILE

# Upload to cloud storage
aws s3 cp $BACKUP_FILE s3://vexis-backups/$BACKUP_FILE

# Clean up old backups (older than 30 days)
find $BACKUP_DIR -name "*.dump" -mtime +30 -delete
```

### Redis Backup

```bash
# Redis RDB backup
redis-cli -h localhost -p 6379 -a $REDIS_PASSWORD \
  --rdb /backups/redis/redis_backup_$DATE.rdb

# Automated Redis backup script
#!/bin/bash
BACKUP_DIR="/backups/redis"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/redis_backup_$DATE.rdb"

redis-cli -h localhost -p 6379 -a $REDIS_PASSWORD \
  --rdb $BACKUP_FILE

# Upload to cloud storage
aws s3 cp $BACKUP_FILE s3://vexis-backups/redis/$BACKUP_FILE

# Clean up old backups (older than 7 days)
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
```

### Disaster Recovery

```yaml
# Kubernetes disaster recovery configuration
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: vexiscore-pdb
  namespace: vexiscore
spec:
  minAvailable: 2  # Ensure at least 2 pods are available during disruptions
  selector:
    matchLabels:
      app: vexiscore
```

```yaml
# Multi-region deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vexiscore-region-2
  namespace: vexiscore-region-2
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vexiscore
      region: region-2
  template:
    metadata:
      labels:
        app: vexiscore
        region: region-2
    spec:
      containers:
      - name: vexiscore
        image: vexiscore:latest
        env:
        - name: REGION
          value: "region-2"
        - name: DATABASE_HOST
          value: "postgres-region-2"
```

## Monitoring and Maintenance

### Health Checks

```bash
# Health check endpoints
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8000/ready
curl -X GET http://localhost:8000/live

# Health check response
{
  "status": "healthy",
  "timestamp": "2026-05-24T22:00:00Z",
  "components": {
    "database": {
      "status": "connected",
      "connection_time": 12
    },
    "redis": {
      "status": "connected",
      "memory_usage": 2048
    },
    "api": {
      "status": "operational",
      "version": "2.1.0"
    }
  }
}
```

### Performance Monitoring

```bash
# Prometheus metrics endpoint
curl http://localhost:9090/metrics

# Example metrics
# HELP vexiscore_active_tasks Total number of active tasks
# TYPE vexiscore_active_tasks gauge
vexis_active_tasks 5.0
# HELP vexiscore_task_duration_seconds Task duration in seconds
# TYPE vexiscore_task_duration_seconds histogram
vexis_task_duration_seconds{le="60"} 100.0
vexis_task_duration_seconds{le="300"} 250.0
vexis_task_duration_seconds{le="600"} 300.0
```

### Log Management

```bash
# Structured logging format
{
  "timestamp": "2026-05-24T22:30:00Z",
  "level": "INFO",
  "service": "vexis-core",
  "phase": "phase3",
  "task_id": "task_123",
  "message": "Task completed successfully",
  "duration": 120.5,
  "result": {
    "backup_size": "10GB",
    "encryption_applied": true
  }
}

# Log rotation configuration
/var/log/vexis/vexis.log {
  daily
  rotate 30
  compress
  delaycompress
  notifempty
  missingok
  copytruncate
}
```

## Security Considerations

### Network Security

```yaml
# Network policies (Kubernetes)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: vexiscore-network-policy
  namespace: vexiscore
spec:
  podSelector:
    matchLabels:
      app: vexiscore
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
      - ipBlock:
          cidr: 10.0.0.0/16
      - namespaceSelector:
          matchLabels:
            name: monitoring
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
      - ipBlock:
          cidr: 10.0.0.0/16
    ports:
    - protocol: TCP
      port: 5432
    - protocol: TCP
      port: 6379
```

### Secrets Management

```yaml
# Secrets management (Kubernetes)
apiVersion: v1
kind: Secret
metadata:
  name: vexiscore-secrets
  namespace: vexiscore
type: Opaque
data:
  db-password: cGFzc3dvcmQxMjM=  # base64 encoded
  redis-password: cGFzc3dvcmQxMjM=  # base64 encoded
  api-key: cGFzc3dvcmQxMjM=  # base64 encoded
```

### Security Hardening

```bash
# Security hardening script
#!/bin/bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install security tools
sudo apt-get install -y fail2ban ufw

# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Install SSL certificate (Let's Encrypt)
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.vexis.example.com

# Configure fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Troubleshooting

### Common Deployment Issues

#### Database Connection Issues

**Error**: `Connection refused for database host`

**Solution**:
1. Verify database service is running
2. Check network connectivity
3. Verify database credentials

```bash
# Check database service status
sudo systemctl status postgresql

# Test database connectivity
nc -zv localhost 5432

# Verify database credentials
python3 manage.py check_db_connection --config production.yaml
```

#### Redis Connection Issues

**Error**: `Redis connection failed`

**Solution**:
1. Verify Redis service is running
2. Check Redis password configuration
3. Verify network connectivity

```bash
# Check Redis service status
sudo systemctl status redis

# Test Redis connectivity
redis-cli -h localhost -p 6379 ping

# Verify Redis configuration
redis-cli -h localhost -p 6379 info | grep -E "connected_clients|used_memory"
```

#### API Authentication Issues

**Error**: `401 Unauthorized - Invalid API key`

**Solution**:
1. Verify API key is correct
2. Check API key permissions
3. Verify authentication headers

```bash
# Verify API key
echo $AI_AGENT_API_KEY | wc -c  # Check key length

# Test API authentication
curl -X GET https://api.vexis.example.com/v2/health \
  -H "Authorization: Bearer YOUR_API_KEY"

# Check API key permissions
python3 manage.py list_api_keys --config production.yaml
```

#### Performance Issues

**Error**: `High latency or timeout errors`

**Solution**:
1. Monitor system resources
2. Optimize database queries
3. Scale resources

```bash
# Monitor system resources
htop
nmon
glances

# Monitor database performance
pg_stat_statements
pgBadger

# Optimize database queries
EXPLAIN ANALYZE SELECT * FROM tasks WHERE status = 'running';
```

### Log Analysis

```bash
# View recent logs
sudo journalctl -u vexiscore -n 50 --no-pager

# Follow logs in real-time
sudo journalctl -u vexiscore -f

# Filter logs by error level
sudo journalctl -u vexiscore -p err -n 100

# Search for specific patterns
sudo journalctl -u vexiscore | grep -i "phase.*failed"
sudo journalctl -u vexiscore | grep -i "timeout"
```

### Debugging Tools

```bash
# Network debugging
netstat -tuln | grep :8000
ss -ltn | grep :8000
curl -v http://localhost:8000/health

# Process debugging
ps aux | grep vexiscore
top -p $(pgrep -f vexiscore)

# Resource monitoring
htop
nmon
glances
dstat

# Database debugging
psql -h localhost -p 5432 -U vexis_prod -d vexiscore_prod
redis-cli -h localhost -p 6379 info
```

---

**Deployment Version**: 2.1.0  
**Last Updated**: 2026-05-24  
**Next Steps**: After deployment, configure monitoring, set up backup procedures, and perform security hardening