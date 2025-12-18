# Deployment Options

## Fly.io vs AWS

### Can Fly.io Host This Setup?

**Short answer:** Yes, but with some considerations.

**Fly.io strengths:**
- ✅ Excellent Docker support
- ✅ Supports multi-service deployments (via `fly.toml` with multiple apps)
- ✅ Built-in PostgreSQL service (Fly Postgres)
- ✅ Free tier available for small apps
- ✅ Simpler than AWS for basic deployments
- ✅ Automatic HTTPS

**Fly.io considerations for this project:**
- Your `docker-compose.yml` won't work directly - Fly uses `fly.toml` instead
- You'll need to convert to either:
  1. Two separate Fly apps (one for the API, one for the database)
  2. Use Fly's managed Postgres with AGE extension (may require custom setup)
- The AGE extension might need manual installation on Fly Postgres
- Volume persistence for the database
- Multi-region deployment requires extra configuration

### Recommended Approach for Fly.io

1. **Use Fly Postgres** for the database:
   ```bash
   # Create a Postgres cluster with AGE extension
   fly postgres create
   ```
   - Then manually install AGE extension via psql

2. **Deploy the API app**:
   ```bash
   # Create and deploy the API
   fly launch
   ```

3. **Connect them**:
   - Attach the Postgres to your API app
   - Set environment variables for connection

### AWS Deployment

**AWS strengths:**
- ✅ More mature and feature-rich
- ✅ Better for production-scale applications
- ✅ More database options (RDS, Aurora)
- ✅ ECS/EKS for container orchestration
- ✅ VPC for network isolation

**AWS considerations:**
- More complex setup
- Higher cost (no generous free tier for databases)
- Steeper learning curve
- More configuration required

### Recommended Deployment Strategy

**For Development/Demo (Fly.io):**
```
1. Deploy PostgreSQL with AGE as a Fly app
2. Deploy the API as a separate Fly app
3. Connect via internal networking
```

**For Production (AWS):**
```
1. Use RDS PostgreSQL with AGE extension
2. Deploy API via ECS Fargate or EKS
3. Use ALB for load balancing
4. CloudFront for CDN (if needed)
```

## Fly.io Deployment Guide

### Prerequisites

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login to Fly.io
fly auth login
```

### Step 1: Create Postgres Database

```bash
# Create a new Postgres app
fly postgres create \
  --name hiv-controversy-db \
  --region sjc \
  --vm-size shared-cpu-1x \
  --volume-size 10

# Connect and install AGE extension
fly postgres connect -a hiv-controversy-db

# In psql:
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
SELECT create_graph('medical_literature_graph');
\q
```

### Step 2: Create API App Configuration

Create `fly.toml`:

```toml
app = "hiv-controversy-api"
primary_region = "sjc"

[build]
  dockerfile = "Dockerfile"

[env]
  AGE_DB = "hiv_controversy"
  AGE_USER = "postgres"
  PYTHONUNBUFFERED = "1"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  memory = '1gb'
  cpu_kind = 'shared'
  cpus = 1

[[mounts]]
  source = "output_data"
  destination = "/app/output"
```

### Step 3: Create Dockerfile for API

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY query_api.py .
COPY static/ ./static/

# Expose port
EXPOSE 8000

# Run API server
CMD ["uvicorn", "query_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 4: Deploy

```bash
# Attach database to API app
fly postgres attach --app hiv-controversy-api hiv-controversy-db

# Create volume for data
fly volumes create output_data --size 1 --region sjc

# Deploy
fly deploy

# Check status
fly status

# View logs
fly logs

# Open in browser
fly open
```

### Step 5: Load Data

```bash
# SSH into the app
fly ssh console -a hiv-controversy-api

# Run the pipeline stages
python run_pipeline.py 1-6
```

## AWS Deployment Guide

### Option 1: ECS Fargate (Recommended)

1. **Create RDS PostgreSQL instance** with AGE extension
2. **Build and push Docker image** to ECR
3. **Create ECS cluster** and task definition
4. **Deploy as ECS service** with ALB
5. **Configure environment variables** for database connection

### Option 2: EC2 with Docker Compose

1. **Launch EC2 instance** (t3.medium or larger)
2. **Install Docker and Docker Compose**
3. **Clone repository**
4. **Run `docker-compose up -d`**
5. **Configure security groups** for ports 8000 and 5432

### Option 3: Elastic Beanstalk

1. **Create Elastic Beanstalk application**
2. **Upload Docker configuration**
3. **Configure RDS database**
4. **Deploy and configure environment**

## Cost Comparison

### Fly.io (Estimated Monthly Cost)

- **Development/Demo:**
  - Shared CPU (256MB): Free
  - Postgres (shared-cpu-1x, 10GB): ~$15/month
  - **Total: ~$15/month**

- **Production:**
  - Dedicated CPU (1GB RAM): ~$19/month
  - Postgres (dedicated-cpu-1x, 50GB): ~$80/month
  - **Total: ~$99/month**

### AWS (Estimated Monthly Cost)

- **Development:**
  - t3.small EC2: ~$15/month
  - RDS db.t3.micro: ~$15/month
  - **Total: ~$30/month**

- **Production:**
  - ECS Fargate (0.5 vCPU, 1GB): ~$15/month
  - RDS db.t3.small: ~$30/month
  - ALB: ~$20/month
  - **Total: ~$65/month**

## Recommendation

**For this project, I recommend Fly.io for the following reasons:**

1. **Simpler deployment** - Less configuration required
2. **Better developer experience** - Easy CLI, good documentation
3. **Cheaper for small scale** - Free tier available
4. **Good Docker support** - Works well with your existing setup
5. **Faster to get running** - Can be deployed in minutes

**However, migrate to AWS if you need:**
- High availability across multiple regions
- Advanced networking (VPCs, private subnets)
- Integration with other AWS services
- Enterprise support
- Compliance requirements (HIPAA, SOC 2, etc.)

## Next Steps

1. Choose your deployment platform
2. Follow the relevant guide above
3. Test the deployment
4. Set up monitoring and logging
5. Configure backups
6. Set up CI/CD pipeline (optional)
