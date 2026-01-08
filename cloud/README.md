# Cloud GPU Inference Server Setup

This directory contains scripts to set up a GPU-accelerated Ollama inference server on cloud providers.

**Recommended:** Use **Lambda Labs** for instant GPU access without quota requests.

**Recommended:** Use **Lambda Labs** for instant GPU access without quota requests.

## Lambda Labs Quick Start (Recommended)

### Why Lambda Labs?
- ✅ **Instant access** - No quota requests needed (unlike AWS)
- ✅ **GPU-focused** - Optimized for ML workloads
- ✅ **Competitive pricing** - Often cheaper than AWS spot instances
- ✅ **Pre-configured** - NVIDIA drivers already installed

### 1. Choose Instance Type

For Ollama inference (LLM + embeddings), choose:

**Best Value:** **1x A10 (24 GB PCIe)** - $0.75/hr
- 24GB VRAM (plenty for llama3.1:8b + embeddings)
- 30 vCPUs, 200 GB RAM
- Perfect for inference workloads

**Avoid:**
- ❌ H100 instances ($2.49+/hr) - Overkill for inference, designed for training
- ❌ Multi-GPU instances - You only need 1 GPU for this workload
- ❌ GH200 - ARM64 architecture may have compatibility issues

### 2. Launch and Setup

1. **Sign up:** https://lambdalabs.com/service/gpu-cloud
2. **Launch:** 1x A10 (24 GB PCIe) instance
3. **SSH in** and run setup:

```bash
# Update system
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Run Ollama with GPU support
sudo docker run -d \
  --gpus=all \
  --name ollama \
  -p 11434:11434 \
  -v ollama:/root/.ollama \
  --restart unless-stopped \
  ollama/ollama

# Pull models (takes a few minutes)
sudo docker exec ollama ollama pull llama3.1:8b
sudo docker exec ollama ollama pull nomic-embed-text

# Verify GPU is working
sudo docker exec ollama nvidia-smi
```

### 3. Use from Your Laptop

```bash
# Set remote Ollama server
export OLLAMA_HOST=http://<LAMBDA_IP>:11434

# Test connection
curl $OLLAMA_HOST/api/tags

# Clear any existing entity DB (if you had buggy runs)
rm -rf ./data/entity_db

# Run ingestion with GPU acceleration!
cd ingestion/
docker compose up -d postgres
docker compose run ingest \
  python ingest_papers.py \
  --query "metformin diabetes" \
  --limit 10 \
  --model llama3.1:8b
```

### Performance with A10 GPU
- **Before (laptop CPU):** ~1 paper per 20+ minutes
- **After (A10 GPU):** ~5-10 papers per minute  
- **Speedup:** ~50-100x faster
- **Cost for 100 papers:** ~$1.50 (2 hours @ $0.75/hr)

---

## AWS EC2 Setup (Alternative)

> [!NOTE]
> AWS requires quota increase for GPU instances. New accounts have 0 vCPU limit for G/VT instances.
> Request increase at: https://console.aws.amazon.com/servicequotas/home/services/ec2/quotas

## Quick Start (Manual Setup)

### 1. Launch EC2 Instance

**Via AWS Console:**
1. Go to EC2 → Launch Instance
2. Choose: **Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)**
3. Instance type: **g4dn.xlarge** (T4 GPU, ~$0.50/hr)
   - Or use **Spot Instance** for ~$0.15-0.20/hr
4. Storage: 100 GB
5. Security Group: Allow ports 22 (SSH) and 11434 (Ollama)

### 2. SSH and Run Setup Script

```bash
# Copy setup script to instance
scp ec2-ollama-setup.sh ubuntu@<EC2_IP>:~/

# SSH into instance
ssh ubuntu@<EC2_IP>

# Run setup (takes ~10 minutes)
sudo bash ec2-ollama-setup.sh
```

### 3. Use from Your Laptop

```bash
# Set Ollama host
export OLLAMA_HOST=http://<EC2_PUBLIC_IP>:11434

# Test connection
curl $OLLAMA_HOST/api/tags

# Run ingestion pointing to remote server
cd /home/wware/med-lit-graph
python ingestion/ingest_papers.py \
  --query "metformin diabetes" \
  --limit 10
```

## Automated Setup (Terraform)

If you have Terraform installed:

```bash
cd cloud/

# Initialize
terraform init

# Review plan
terraform plan

# Deploy (creates spot instance by default)
terraform apply

# Get connection info
terraform output ollama_url
terraform output ssh_command

# When done, destroy to stop charges
terraform destroy
```

## Cost Comparison

### Lambda Labs
| Instance Type | GPU | vCPUs | RAM | Price |
|--------------|-----|-------|-----|-------|
| 1x A10 (24GB)| A10 | 30    | 200GB| $0.75/hr ⭐ |
| 1x A100 (40GB)| A100| 30   | 200GB| $1.29/hr |
| 1x H100 (80GB)| H100| 26   | 200GB| $2.49/hr |

### AWS EC2
| Instance Type | GPU | vCPUs | RAM | On-Demand | Spot (typical) |
|--------------|-----|-------|-----|-----------|----------------|
| g4dn.xlarge  | T4  | 4     | 16GB| $0.526/hr | $0.15-0.20/hr |
| g4dn.2xlarge | T4  | 8     | 32GB| $0.752/hr | $0.22-0.28/hr |
| g5.xlarge    | A10G| 4     | 16GB| $1.006/hr | $0.30-0.40/hr |

**Recommendation:** 
- **Best:** Lambda Labs **1x A10** - $0.75/hr (instant access, no quota needed)
- **Alternative:** AWS **g4dn.xlarge spot** - $0.15/hr (requires quota increase)

## Performance Expectations

With GPU acceleration:
- **Embedding generation**: ~50-100x faster than CPU
- **LLM inference**: ~10-30x faster than CPU
- **Expected throughput**: 5-10 papers/minute (vs 1 paper/20+ minutes on CPU)

## Security Notes

> [!WARNING]
> The default security group allows access from anywhere (0.0.0.0/0). For production:
> 1. Restrict to your IP: `cidr_blocks = ["YOUR_IP/32"]`
> 2. Use VPN or SSH tunnel
> 3. Add authentication to Ollama

## Monitoring

Check Ollama logs:
```bash
ssh ubuntu@<EC2_IP>
docker logs -f ollama
```

Check GPU usage:
```bash
ssh ubuntu@<EC2_IP>
nvidia-smi
```

## Optimizing BioBERT Model Loading

The BioBERT embedding model (`microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext`) is ~400MB and takes 5-10 minutes to download/load on first run. To avoid reloading it every time:

### Solution: Cache the HuggingFace Models

Add a volume mount to cache models between container restarts.

**For local development** (in `ingestion/docker-compose.yml`):
```yaml
  ingest:
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
```

**For cloud server**, pre-download the model:
```bash
# On cloud server (Lambda Labs or AWS)
mkdir -p ~/huggingface_cache

# Pre-download BioBERT model
docker run --rm \
  -v ~/huggingface_cache:/root/.cache/huggingface \
  python:3.12-slim \
  bash -c "pip install -q sentence-transformers && python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext')\""
```

Then mount it in docker-compose.yml:
```yaml
  ingest:
    volumes:
      - ~/huggingface_cache:/root/.cache/huggingface
```

### Performance Impact:
- **Without cache**: 5-10 minutes loading time per container start
- **With cache**: ~10-30 seconds loading time
- **Recommendation**: Always cache models in production!

### Alternative: Use a Lighter Embedding Model

If BioBERT is too slow, consider switching to a lighter model in `ingest_papers.py`:

```python
# Option 1: Lighter general-purpose model (~80MB, very fast)
model_name = "sentence-transformers/all-MiniLM-L6-v2"

# Option 2: Nomic embeddings (~140MB, good quality)
model_name = "nomic-embed-text"

# Current: BioBERT (~400MB, best for medical text)
model_name = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
```

Trade-offs:
- **BioBERT**: Best medical domain accuracy, slowest loading
- **Nomic**: Good general embeddings, faster
- **MiniLM**: Fastest, but less medical-specific

## Cleanup

**Important:** Don't forget to terminate the instance when done!

```bash
# Via Terraform
terraform destroy

# Or via AWS Console
# EC2 → Instances → Select instance → Instance State → Terminate

# Via Lambda Labs Console
# Instances → Select instance → Terminate
```
