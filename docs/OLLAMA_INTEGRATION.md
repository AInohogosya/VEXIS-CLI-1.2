# Ollama Integration Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Ollama Overview](#ollama-overview)
3. [Installation](#installation)
4. [Model Management](#model-management)
5. [Configuration](#configuration)
6. [API Integration](#api-integration)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Advanced Usage](#advanced-usage)

## Introduction

Ollama is a powerful local AI platform that enables you to run state-of-the-art language models on your own hardware. This guide provides comprehensive information for integrating Ollama with the 6-Phase Architecture system, allowing you to leverage local AI models for enhanced privacy, speed, and cost-effectiveness.

### Benefits of Ollama Integration

- **Privacy**: Keep sensitive data on-premises
- **Speed**: Low-latency responses without network dependencies
- **Cost**: No per-request API costs
- **Control**: Full control over model selection and configuration
- **Reliability**: No external service dependencies

## Ollama Overview

### Key Features

- **Local Execution**: Run AI models entirely on your hardware
- **Multiple Models**: Support for various model architectures
- **GPU Acceleration**: Optimized for NVIDIA GPUs
- **REST API**: Simple HTTP API for model interaction
- **Model Management**: Easy model installation and updates

### Supported Models

| Model | Size | Provider | Best For |
|-------|------|----------|----------|
| `llama-4-scout-17b` | 17B | Meta | Balanced performance |
| `llama-4-7b` | 7B | Meta | Fast inference |
| `deepseek-r1` | 7B | DeepSeek | Reasoning tasks |
| `qwen2.5-3b` | 3B | Alibaba | Lightweight applications |
| `mistral-7b` | 7B | Mistral | Creative tasks |

## Installation

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Docker**: 20.10 or higher (recommended)
- **GPU**: NVIDIA GPU with CUDA support (optional but recommended)
- **Memory**: 8GB minimum, 16GB recommended
- **Storage**: 20GB free space per model

### Installation Methods

#### macOS (Homebrew)

```bash
# Install Ollama via Homebrew
brew install ollama

# Start Ollama service
ollama serve

# Verify installation
ollama --version
```

#### Linux

```bash
# Install via script
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl start ollama

# Enable automatic startup
sudo systemctl enable ollama

# Verify installation
ollama --version
```

#### Windows

```powershell
# Download installer from https://ollama.ai/download
# Run the installer
# Start Ollama from Start menu
```

### Docker Installation

```bash
# Run Ollama in Docker
docker run -d -p 11434:11434 --name ollama ollama/ollama:latest

# Verify installation
curl http://localhost:11434/api/tags
```

## Model Management

### Installing Models

```bash
# List available models
ollama list --available

# Install a model
ollama pull llama-4-scout-17b

# Install with custom parameters
ollama pull llama-4-scout-17b:n-gpu-layers=49,num-contexts=4

# Install multiple models
ollama pull llama-4-7b
ollama pull deepseek-r1
ollama pull qwen2.5:3b
```

### Managing Models

```bash
# List installed models
ollama list

# Show model details
ollama show llama-4-scout-17b

# Run model directly
ollama run llama-4-scout-17b "Hello, how are you?"

# Remove model
ollama rm llama-4-scout-17b

# Update model
ollama pull llama-4-scout-17b
```

### Model Optimization

```bash
# Quantize model for faster inference
ollama quantize llama-4-scout-17b

# Prune model to reduce size
ollama prune llama-4-scout-17b

# Create model variants
ollama create my-llama-4-scout-17b --base llama-4-scout-17b --param n-gpu-layers=32
```

## Configuration

### Basic Configuration

```yaml
# config.yaml
api:
  preferred_provider: "ollama"  # Use Ollama as primary provider
  local_endpoint: "http://localhost:11434"  # Ollama API endpoint
  local_model: "llama-4-scout-17b"  # Default model
  timeout: 120  # Request timeout in seconds
  max_retries: 3  # Maximum retry attempts

engine:
  phase_timeout: 1800  # Timeout per phase (seconds)
  task_timeout: 7200  # Total task timeout (seconds)
  max_iterations: 500  # Maximum iterations per phase

security:
  encryption_enabled: true  # Enable data encryption
  api_key_rotation: "30d"  # API key rotation period

monitoring:
  enabled: true  # Enable monitoring
  sampling_rate: 1.0  # Data sampling rate
```

### Environment Variables

```bash
# Set Ollama-specific environment variables
export OLLAMA_ENDPOINT="http://localhost:11434"
export OLLAMA_MODEL="llama-4-scout-17b"
export OLLAMA_TIMEOUT="120"

# Set API keys for cloud fallback
export GROQ_API_KEY="your_groq_api_key"
export GOOGLE_API_KEY="your_google_api_key"

# Enable automatic failover
export AI_AGENT_AUTO_FALLBACK="true"
```

### Advanced Configuration

```yaml
# Advanced Ollama configuration
ollama:
  endpoint: "http://localhost:11434"
  model: "llama-4-scout-17b"
  timeout: 180
  max_retries: 5
  batch_size: 4  # Number of requests to process in parallel
  temperature: 0.7  # Creativity vs. determinism
  top_p: 0.95  # Nucleus sampling threshold
  max_tokens: 4096  # Maximum response length
  streaming: true  # Enable streaming responses
  
  # Model-specific configurations
  models:
    llama-4-scout-17b:
      n-gpu-layers: 49
      num-contexts: 4
      quantization: "q4_0"
      
    deepseek-r1:
      n-gpu-layers: 32
      num-contexts: 2
      temperature: 0.8
      
    qwen2.5:3b:
      n-gpu-layers: 16
      num-contexts: 1
```

## API Integration

### REST API Endpoints

```http
# Get available models
GET http://localhost:11434/api/tags

# Generate response from model
POST http://localhost:11434/api/generate
Content-Type: application/json

{
  "model": "llama-4-scout-17b",
  "prompt": "Hello, how are you?",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.95,
    "max_tokens": 4096
  }
}

# Stream response from model
POST http://localhost:11434/api/generate
Content-Type: application/json

{
  "model": "llama-4-scout-17b",
  "prompt": "Hello, how are you?",
  "stream": true,
  "options": {
    "temperature": 0.7,
    "top_p": 0.95,
    "max_tokens": 4096
  }
}

# Get model details
GET http://localhost:11434/api/models/{model_name}
```

### Python Integration

```python
import requests
import json

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, endpoint: str = "http://localhost:11434", model: str = "llama-4-scout-17b"):
        self.endpoint = endpoint
        self.model = model
        
    def generate(self, prompt: str, stream: bool = False, **options) -> Dict[str, Any]:
        """Generate response from model."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": options
        }
        
        response = requests.post(
            f"{self.endpoint}/api/generate",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Ollama API error: {response.text}")
    
    def stream_generate(self, prompt: str, **options) -> Iterator[str]:
        """Stream response from model."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": options
        }
        
        response = requests.post(
            f"{self.endpoint}/api/generate",
            json=payload,
            timeout=180,
            stream=True
        )
        
        if response.status_code == 200:
            for chunk in response.iter_lines():
                if chunk:
                    yield chunk.decode("utf-8")
        else:
            raise Exception(f"Ollama streaming error: {response.text}")

# Usage example
ollama = OllamaClient(model="llama-4-scout-17b")
response = ollama.generate("Hello, how are you?")
print(response["generated"])
```

### Integration with 6-Phase Architecture

```python
# app/providers/ollama.py
from app.providers.base import BaseProvider
from app.utils.logging import get_logger

logger = get_logger(__name__)

class OllamaProvider(BaseProvider):
    """Ollama provider implementation."""
    
    def __init__(self, endpoint: str, model: str, **kwargs):
        self.endpoint = endpoint
        self.model = model
        self.client = self._create_client()
        self.logger = logger
        
    def _create_client(self):
        """Create Ollama client."""
        return OllamaClient(endpoint=self.endpoint, model=self.model)
    
    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command using Ollama."""
        try:
            prompt = self._format_prompt(command, **kwargs)
            response = self.client.generate(
                prompt=prompt,
                stream=False,
                **self._get_options(**kwargs)
            )
            
            return {
                "success": True,
                "result": response.get("generated", ""),
                "confidence": response.get("confidence", 0.0),
                "provider": "ollama",
                "model": self.model
            }
            
        except Exception as e:
            self.logger.error(f"Ollama execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": "ollama"
            }
    
    def stream_execute(self, command: str, **kwargs) -> Iterator[str]:
        """Stream execution using Ollama."""
        try:
            prompt = self._format_prompt(command, **kwargs)
            stream = self.client.stream_generate(
                prompt=prompt,
                **self._get_options(**kwargs)
            )
            
            for chunk in stream:
                yield chunk
                
        except Exception as e:
            self.logger.error(f"Ollama stream execution failed: {str(e)}")
            yield f"Error: {str(e)}"
    
    def _format_prompt(self, command: str, **kwargs) -> str:
        """Format command into prompt."""
        prompt = f"""
        You are an AI assistant helping with {kwargs.get('task_type', 'automation')}.
        
        Command: {command}
        
        Provide a detailed response with step-by-step instructions.
        """
        return prompt
    
    def _get_options(self, **kwargs) -> Dict[str, Any]:
        """Get model options from parameters."""
        return {
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.95),
            "max_tokens": kwargs.get("max_tokens", 4096)
        }
```

## Performance Optimization

### Hardware Optimization

#### GPU Acceleration

```bash
# Check GPU compatibility
nvidia-smi

# Install CUDA if needed
# Download from https://developer.nvidia.com/cuda-downloads

# Verify CUDA installation
nvcc --version

# Install cuDNN for additional acceleration
# Download from https://developer.nvidia.com/cudnn
```

#### CPU Optimization

```bash
# Set CPU affinity for Ollama process
taskset -c 0-3 ollama serve  # Use cores 0-3

# Adjust process priority
nice -n 10 ollama serve  # Lower priority

# Limit memory usage
ulimit -v 8000000  # Limit to 8GB
```

### Model Optimization

#### Quantization

```bash
# Quantize model to reduce size and increase speed
ollama quantize llama-4-scout-17b

# Quantize with specific format
ollama quantize llama-4-scout-17b --format q4_0

# Create quantized model variant
ollama create llama-4-scout-17b-q4 --base llama-4-scout-17b --quantize
```

#### Pruning

```bash
# Prune model to remove redundant parameters
ollama prune llama-4-scout-17b

# Prune with specific parameters
ollama prune llama-4-scout-17b --threshold 0.01
```

#### Model Selection

```bash
# Choose appropriate model for task
if task_complexity == "high":
    model = "llama-4-scout-17b"  # 17B parameters for complex tasks
elif task_complexity == "medium":
    model = "llama-4-7b"  # 7B parameters for balanced performance
else:
    model = "qwen2.5:3b"  # 3B parameters for fast, simple tasks
```

### System Configuration

```bash
# Optimize system for AI workloads
sudo sysctl -w vm.swappiness=10          # Reduce swapping
sudo sysctl -w vm.vfs_cache_pressure=50  # Reduce cache pressure
sudo sysctl -w net.core.somaxconn=1024   # Increase connection backlog

# Configure huge pages for better performance
sudo sysctl -w vm.nr_hugepages=128

# Optimize CPU governor
echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Configure GPU settings
nvidia-smi -l 1  # Monitor GPU usage every second
```

### Application Optimization

```python
# app/utils/performance.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator

class PerformanceOptimizer:
    """Optimize performance for Ollama integration."""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.loop = asyncio.get_event_loop()
        
    def batch_process(self, prompts: List[str], model: str, **options) -> List[Dict[str, Any]]:
        """Process multiple prompts in parallel."""
        tasks = [
            self._process_prompt(prompt, model, **options)
            for prompt in prompts
        ]
        
        return list(self.loop.run_in_executor(self.executor, tasks))
    
    def stream_with_buffering(self, prompt: str, buffer_size: int = 10) -> Iterator[str]:
        """Stream responses with buffering."""
        buffer = []
        stream = ollama.stream_generate(prompt)
        
        for chunk in stream:
            buffer.append(chunk)
            if len(buffer) >= buffer_size:
                yield "".join(buffer)
                buffer = []
        
        if buffer:
            yield "".join(buffer)
    
    def cache_responses(self, ttl: int = 3600):
        """Cache responses to avoid duplicate processing."""
        from app.utils.cache import cache_result
        
        @cache_result(ttl=ttl)
        def cached_generate(prompt: str):
            return ollama.generate(prompt)
        
        return cached_generate
```

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Ollama Service Not Starting

**Symptoms**:
- `ollama serve` command fails
- Connection refused errors
- Service crashes immediately

**Solutions**:

1. **Check System Requirements**
   ```bash
   # Verify Docker is running (if using Docker)
   docker ps
   
   # Check system resources
   free -h
   df -h
   nvidia-smi  # If using GPU
   ```

2. **Review Logs**
   ```bash
   # Check Ollama logs
   journalctl -u ollama -n 50
   
   # Check Docker logs (if using Docker)
   docker logs ollama
   ```

3. **Reinstall Ollama**
   ```bash
   # Uninstall Ollama
   brew uninstall ollama  # macOS
   sudo apt-get remove ollama  # Ubuntu
   
   # Reinstall Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

#### Issue 2: Model Download Failures

**Symptoms**:
- `ollama pull` command fails
- Network connection errors
- Model files incomplete

**Solutions**:

1. **Check Internet Connection**
   ```bash
   # Test internet connectivity
   ping -c 3 google.com
   
   # Check network proxy if needed
   export HTTP_PROXY=http://proxy.example.com:8080
   export HTTPS_PROXY=http://proxy.example.com:8080
   ```

2. **Verify Disk Space**
   ```bash
   # Check available disk space
   df -h
   
   # Free up space if needed
   sudo apt-get clean
   rm -rf ~/.cache/ollama
   ```

3. **Retry Model Download**
   ```bash
   # Retry with verbose output
   ollama pull llama-4-scout-17b --verbose
   
   # Download specific model version
   ollama pull llama-4-scout-17b@latest
   ```

#### Issue 3: Slow Inference Performance

**Symptoms**:
- High latency responses
- GPU not being utilized
- CPU bottleneck

**Solutions**:

1. **Check Hardware Utilization**
   ```bash
   # Monitor GPU usage
   nvidia-smi -l 1
   
   # Monitor CPU usage
   top -o %CPU
   htop
   
   # Monitor memory usage
   free -h
   ```

2. **Optimize Model Configuration**
   ```bash
   # Adjust model parameters for better performance
   ollama create optimized-llama-4-scout-17b \
     --base llama-4-scout-17b \
     --param n-gpu-layers=32 \
     --param num-contexts=2 \
     --quantize
   ```

3. **Scale Resources**
   ```bash
   # Increase CPU cores
   taskset -c 0-7 ollama serve  # Use 8 cores
   
   # Adjust process priority
   nice -n -10 ollama serve  # Higher priority
   ```

#### Issue 4: API Connection Issues

**Symptoms**:
- Connection refused to http://localhost:11434
- API request timeouts
- Authentication failures

**Solutions**:

1. **Verify Ollama Service Status**
   ```bash
   # Check if Ollama is running
   systemctl status ollama
   
   # Start Ollama if not running
   sudo systemctl start ollama
   
   # Enable automatic startup
   sudo systemctl enable ollama
   ```

2. **Check API Endpoint**
   ```bash
   # Test API connectivity
   curl http://localhost:11434/api/tags
   
   # Check if endpoint is correct
   grep OLLAMA_ENDPOINT .env
   ```

3. **Review Firewall Settings**
   ```bash
   # Check if port 11434 is blocked
   sudo ufw status
   sudo iptables -L -n | grep 11434
   
   # Allow traffic on port 11434
   sudo ufw allow 11434/tcp
   ```

#### Issue 5: Model Compatibility Issues

**Symptoms**:
- Model not found errors
- Incompatible model format
- Execution failures with specific models

**Solutions**:

1. **Check Installed Models**
   ```bash
   # List installed models
   ollama list
   
   # Verify model exists
   ollama show llama-4-scout-17b
   ```

2. **Update Model Format**
   ```bash
   # Update model to latest format
   ollama pull llama-4-scout-17b
   
   # Convert model format if needed
   ollama convert llama-4-scout-17b --to gguf
   ```

3. **Check Model Requirements**
   ```bash
   # Verify model requirements
   ollama show llama-4-scout-17b | grep -E "parameters|size|requirements"
   
   # Ensure sufficient resources
   free -h  # Memory
   nvidia-smi  # GPU
   ```

### Debugging Commands

```bash
# Check Ollama version
ollama --version

# Check service status
systemctl status ollama

# View logs
journalctl -u ollama -n 100
journalctl -u ollama -f

# Test API connectivity
curl http://localhost:11434/api/tags
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-4-scout-17b","prompt":"Hello"}'

# Check resource usage
top -p $(pgrep -f ollama)
nvidia-smi -q -i 0
```

## Best Practices

### Model Selection

```python
# Choose appropriate model based on task requirements
def select_model(task_type: str, complexity: str) -> str:
    """
    Select optimal model for task.
    
    Args:
        task_type: Type of task (reasoning, creative, analytical, etc.)
        complexity: Task complexity (simple, medium, complex)
    
    Returns:
        Model name to use
    """
    if task_type == "reasoning" and complexity == "complex":
        return "deepseek-r1"  # Best for complex reasoning
    elif task_type == "creative" and complexity == "medium":
        return "llama-4-scout-17b"  # Balanced for creative tasks
    elif task_type == "analytical" and complexity == "high":
        return "llama-4-7b"  # Good for analysis
    else:
        return "qwen2.5:3b"  # Default for simple tasks

# Usage
model = select_model("reasoning", "complex")
```

### Performance Monitoring

```python
# Monitor Ollama performance metrics
class OllamaMonitor:
    """Monitor Ollama performance metrics."""
    
    def __init__(self):
        self.metrics = {
            "response_time": [],
            "token_count": [],
            "gpu_usage": [],
            "memory_usage": []
        }
    
    def collect_metrics(self, response: Dict[str, Any]):
        """Collect performance metrics from response."""
        self.metrics["response_time"].append(response.get("latency", 0))
        self.metrics["token_count"].append(len(response.get("generated", "").split()))
        
        # GPU and memory monitoring
        self._collect_hardware_metrics()
    
    def get_average_response_time(self) -> float:
        """Get average response time."""
        if self.metrics["response_time"]:
            return sum(self.metrics["response_time"]) / len(self.metrics["response_time"])
        return 0.0
    
    def get_throughput(self) -> float:
        """Get tokens per second."""
        if self.metrics["response_time"] and self.metrics["token_count"]:
            total_time = sum(self.metrics["response_time"])
            total_tokens = sum(self.metrics["token_count"])
            return total_tokens / total_time if total_time > 0 else 0
        return 0.0
```

### Resource Management

```python
# Manage system resources for Ollama
class ResourceManager:
    """Manage system resources for Ollama."""
    
    def __init__(self):
        self.cpu_cores = 4
        self.memory_gb = 8
        self.gpu_enabled = self._check_gpu()
        
    def _check_gpu(self) -> bool:
        """Check if GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def optimize_for_ollama(self):
        """Optimize system for Ollama execution."""
        if self.gpu_enabled:
            self._optimize_gpu()
        else:
            self._optimize_cpu()
        
        self._configure_ollama()
    
    def _optimize_gpu(self):
        """Optimize GPU settings."""
        # Set GPU memory allocation
        import torch
        torch.cuda.set_device(0)
        
        # Configure CUDA settings
        import os
        os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    
    def _optimize_cpu(self):
        """Optimize CPU settings."""
        import multiprocessing
        
        # Set CPU affinity
        multiprocessing.set_start_method("spawn")
        
        # Limit CPU usage
        import signal
        signal.signal(signal.SIGXCPU, signal.SIG_IGN)
    
    def _configure_ollama(self):
        """Configure Ollama for optimal performance."""
        import subprocess
        
        # Set CPU affinity for Ollama
        subprocess.run([
            "taskset", "-c", "0-3", 
            "ollama", "serve"
        ])
        
        # Adjust process priority
        subprocess.run([
            "renice", "-n", "-1",
            "-p", str(subprocess.check_output(["pgrep", "ollama"])).strip()
        ])
```

### Security Considerations

```python
# Secure Ollama integration
class OllamaSecurity:
    """Security considerations for Ollama integration."""
    
    def __init__(self):
        self.endpoint = "http://localhost:11434"
        self.model_cache = {}
        
    def sanitize_input(self, prompt: str) -> str:
        """Sanitize user input before sending to Ollama."""
        import re
        
        # Remove potentially harmful content
        harmful_patterns = [
            r"exec.*?system",
            r"delete.*?files",
            r"rm.*?rf",
            r"wget.*?malicious",
            r"curl.*?malicious"
        ]
        
        for pattern in harmful_patterns:
            prompt = re.sub(pattern, "", prompt, flags=re.IGNORECASE)
        
        return prompt
    
    def validate_model(self, model: str) -> bool:
        """Validate model is safe and approved."""
        approved_models = [
            "llama-4-scout-17b",
            "llama-4-7b",
            "deepseek-r1",
            "qwen2.5:3b"
        ]
        
        return model in approved_models
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data before processing."""
        from cryptography.fernet import Fernet
        
        # Generate key if not exists
        try:
            with open("ollama.key", "r") as key_file:
                key = key_file.read()
        except FileNotFoundError:
            key = Fernet.generate_key().decode()
            with open("ollama.key", "w") as key_file:
                key_file.write(key)
        
        cipher = Fernet(key.encode())
        return cipher.encrypt(data.encode()).decode()
    
    def monitor_for_malicious_use(self, prompt: str) -> bool:
        """Monitor for potentially malicious use."""
        malicious_patterns = [
            "how to hack",
            "how to create malware",
            "how to bypass security",
            "how to DDoS",
            "how to crack passwords"
        ]
        
        for pattern in malicious_patterns:
            if pattern.lower() in prompt.lower():
                return True
        
        return False
```

## Advanced Usage

### Custom Model Creation

```bash
# Create custom model based on existing model
ollama create my-model --base llama-4-scout-17b

# Add custom parameters
ollama create my-model \
  --base llama-4-scout-17b \
  --param n-gpu-layers=32 \
  --param num-contexts=2 \
  --quantize

# Create model from custom LoRA
ollama create my-lora-model \
  --base llama-4-scout-17b \
  --lora path/to/my-lora.safetensors
```

### Model Fine-Tuning

```python
# Fine-tune model with custom dataset
import torch
from transformers import LoraConfig, Trainer, TrainingArguments
from datasets import load_dataset

def fine_tune_model():
    """Fine-tune Ollama model with custom data."""
    # Load base model
    model_name = "llama-4-scout-17b"
    
    # Load dataset
    dataset = load_dataset("path/to/dataset")
    
    # Configure LoRA
    lora_config = LoraConfig(
        task_type="CAUSAL_LM",
        r=int(8),  # Rank
        lora_alpha=int(32),  # alpha
        target_modules=["q_proj", "v_proj", "out_proj"],
        lora_dropout=0.05
    )
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir="./results",
        overwrite_output_dir=True,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=10,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        push_to_hub=True
    )
    
    # Train model
    trainer = Trainer(
        model=model,
        lora_config=lora_config,
        args=training_args,
        train_dataset=dataset,
        eval_dataset=dataset
    )
    
    trainer.train()
    
    # Save fine-tuned model
    trainer.save_model("./fine-tuned-model")
    
    return "./fine-tuned-model"
```

### Distributed Ollama

```python
# Distributed Ollama setup with multiple nodes
class DistributedOllama:
    """Distributed Ollama setup for high availability."""
    
    def __init__(self, nodes: List[str]):
        self.nodes = nodes
        self.current_node = 0
        
    def get_endpoint(self) -> str:
        """Get Ollama endpoint with load balancing."""
        node = self.nodes[self.current_node]
        self.current_node = (self.current_node + 1) % len(self.nodes)
        return f"http://{node}:11434"
    
    def execute_with_failover(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command with failover support."""
        for node in self.nodes:
            try:
                client = OllamaClient(endpoint=f"http://{node}:11434")
                response = client.generate(command, **kwargs)
                return response
            except Exception as e:
                print(f"Node {node} failed: {str(e)}")
                continue
        
        raise Exception("All Ollama nodes failed")
    
    def monitor_node_health(self):
        """Monitor health of all Ollama nodes."""
        import requests
        
        health_status = {}
        for node in self.nodes:
            try:
                response = requests.get(
                    f"http://{node}:11434/api/health",
                    timeout=5
                )
                health_status[node] = response.status_code == 200
            except:
                health_status[node] = False
        
        return health_status
```

### Model Serving with API

```python
# Create REST API for serving Ollama models
from fastapi import FastAPI, HTTPException
from typing import List

app = FastAPI(title="Ollama Model Serving API")

# Model registry
models = {
    "llama-4-scout-17b": {
        "endpoint": "http://localhost:11434",
        "parameters": {"n-gpu-layers": 49, "num-contexts": 4}
    },
    "llama-4-7b": {
        "endpoint": "http://localhost:11434",
        "parameters": {"n-gpu-layers": 32, "num-contexts": 2}
    }
}

@app.post("/generate")
async def generate_response(
    model: str = "llama-4-scout-17b",
    prompt: str,
    stream: bool = False,
    temperature: float = 0.7,
    top_p: float = 0.95,
    max_tokens: int = 4096
):
    """Generate response from specified model."""
    if model not in models:
        raise HTTPException(status_code=400, detail="Model not available")
    
    model_config = models[model]
    
    # Create Ollama client
    client = OllamaClient(
        endpoint=model_config["endpoint"],
        model=model
    )
    
    # Generate response
    if stream:
        # Streaming response
        response_stream = client.stream_generate(
            prompt=prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens
        )
        return StreamingResponse(
            content=response_stream,
            media_type="text/event-stream"
        )
    else:
        # Single response
        response = client.generate(
            prompt=prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens
        )
        return response

@app.get("/models")
async def list_models():
    """List available models."""
    return {
        "models": list(models.keys()),
        "total": len(models)
    }

@app.get("/models/{model_name}")
async def get_model_details(model_name: str):
    """Get details about specific model."""
    if model_name not in models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "model": model_name,
        "endpoint": models[model_name]["endpoint"],
        "parameters": models[model_name]["parameters"]
    }
```

## Migration from Cloud Providers

### Benefits of Migration

- **Cost Savings**: Eliminate per-request API costs
- **Performance**: Lower latency with local execution
- **Privacy**: Keep sensitive data on-premises
- **Control**: Full control over model selection and configuration

### Migration Steps

1. **Set Up Ollama Environment**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Start Ollama service
   ollama serve
   
   # Install required models
   ollama pull llama-4-scout-17b
   ollama pull deepseek-r1
   ```

2. **Update Configuration**
   ```yaml
   # Update config.yaml
   api:
     preferred_provider: "ollama"  # Switch to Ollama
     local_endpoint: "http://localhost:11434"
     local_model: "llama-4-scout-17b"
   ```

3. **Test Integration**
   ```python
   # Test Ollama integration
   ollama = OllamaClient(model="llama-4-scout-17b")
   response = ollama.generate("Test prompt")
   print(response)
   ```

4. **Gradual Rollout**
   - Start with non-critical workloads
   - Monitor performance and quality
   - Gradually increase usage

5. **Optimize and Scale**
   ```bash
   # Optimize model performance
   ollama quantize llama-4-scout-17b
   
   # Set up monitoring
   python3 manage.py setup_ollama_monitoring
   ```

### Comparison with Cloud Providers

| Aspect | Cloud Providers | Ollama |
|--------|----------------|--------|
| **Cost** | $0.01-0.10 per 1K tokens | $0.000 (hardware cost only) |
| **Latency** | 100-500ms | 10-100ms |
| **Privacy** | Data sent to cloud | Data stays local |
| **Setup** | Quick API setup | Requires hardware setup |
| **Scalability** | Automatic scaling | Manual scaling |
| **Maintenance** | Fully managed | Self-managed |

## Conclusion

Integrating Ollama with the 6-Phase Architecture provides a powerful, private, and cost-effective AI solution. By following this guide, you can successfully set up, configure, and optimize Ollama for your specific use cases. Remember to:

- Start with appropriate hardware requirements
- Choose the right models for your tasks
- Optimize performance through quantization and configuration
- Monitor system resources and adjust as needed
- Implement security best practices
- Gradually scale usage as you gain experience

With proper implementation, Ollama can significantly enhance your AI capabilities while reducing costs and improving data privacy.

---

**Ollama Integration Version**: 2.1.0  
**Last Updated**: 2026-05-24  
**Next Steps**: After integration, monitor performance, optimize configurations, and explore advanced features like custom model training and distributed deployment