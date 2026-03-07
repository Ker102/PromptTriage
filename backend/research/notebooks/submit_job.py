"""
Submit Study B Training / Benchmark Jobs to Azure ML Compute Cluster.

Uses the Azure ML Python SDK (azure-ai-ml) instead of the CLI extension.
Auto-creates the compute cluster if it doesn't exist (min 0, max 1 nodes).

Usage:
    # First time: login
    az login

    # Submit single model:
    python submit_job.py --model qwen3_8b

    # Submit all 4 models:
    python submit_job.py --model all

    # Custom settings:
    python submit_job.py --model qwen3_14b --epochs 5 --lora-rank 64

    # Submit benchmark job (generates outputs from all adapters):
    python submit_job.py --benchmark

    # Check job status:
    python submit_job.py --status

Prerequisites:
    pip install azure-ai-ml azure-identity
"""
import argparse
import sys
from pathlib import Path
from azure.ai.ml import MLClient, command, Input, Output
from azure.ai.ml.entities import AmlCompute, Environment
from azure.identity import AzureCliCredential, InteractiveBrowserCredential, ChainedTokenCredential

# Resolve paths relative to this script's location
SCRIPT_DIR = Path(__file__).resolve().parent
NOTEBOOKS_DIR = str(SCRIPT_DIR)
TRAINING_DATA_DIR = str(SCRIPT_DIR.parent / "training_data")
CONDA_FILE = str(SCRIPT_DIR / "environment.yml")

# ══════════════════════════════════════════════════════
# CONFIGURE THESE — match your Azure ML workspace
# ══════════════════════════════════════════════════════
SUBSCRIPTION_ID = "2405d969-2c8b-4b70-949e-f250bc25fa9f"
RESOURCE_GROUP = "DefaultResourceGroup-eastus2"
WORKSPACE_NAME = "qwentrain"

CLUSTER_NAME = "gpu-a100"
CLUSTER_VM_SIZE = "Standard_NC24ads_A100_v4"  # A100 80GB
CLUSTER_MIN_NODES = 0     # Scale to zero when idle!
CLUSTER_MAX_NODES = 1
CLUSTER_IDLE_TIMEOUT = 300  # 5 min idle before scale-down

MODELS = ["qwen3_8b", "qwen3_14b", "qwen3_32b", "qwen3_30b_a3b"]


def get_client(args) -> MLClient:
    """Authenticate and return MLClient."""
    import os
    sub = args.subscription or os.environ.get("AZURE_SUBSCRIPTION_ID", SUBSCRIPTION_ID)
    rg = args.resource_group or os.environ.get("AZURE_RESOURCE_GROUP", RESOURCE_GROUP)
    ws = args.workspace or os.environ.get("AZURE_WORKSPACE_NAME", WORKSPACE_NAME)

    if not all([sub, rg, ws]):
        print("❌ Missing Azure config. Provide via CLI flags or environment variables:")
        print("   --subscription <id>  or  AZURE_SUBSCRIPTION_ID")
        print("   --resource-group <name>  or  AZURE_RESOURCE_GROUP")
        print("   --workspace <name>  or  AZURE_WORKSPACE_NAME")
        print()
        print("   Or set them at the top of this script.")
        sys.exit(1)

    # Ensure az CLI is on PATH (Windows installs to a fixed location)
    az_path = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"
    if az_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = az_path + os.pathsep + os.environ.get("PATH", "")

    # Try CLI credential first, fall back to browser login
    try:
        credential = AzureCliCredential()
        credential.get_token("https://management.azure.com/.default")
        print("✅ Authenticated via Azure CLI")
    except Exception:
        print("⚠️  Azure CLI auth failed — opening browser login...")
        credential = InteractiveBrowserCredential()

    client = MLClient(credential, sub, rg, ws)
    print(f"✅ Connected to workspace: {client.workspace_name}")
    return client


def ensure_cluster(client: MLClient):
    """Create compute cluster if it doesn't exist."""
    try:
        cluster = client.compute.get(CLUSTER_NAME)
        print(f"✅ Cluster '{CLUSTER_NAME}' exists (state: {cluster.provisioning_state})")
    except Exception:
        print(f"Creating cluster '{CLUSTER_NAME}'...")
        print(f"  VM: {CLUSTER_VM_SIZE}")
        print(f"  Nodes: {CLUSTER_MIN_NODES}-{CLUSTER_MAX_NODES} (auto-scale to zero)")
        cluster = AmlCompute(
            name=CLUSTER_NAME,
            type="amlcompute",
            size=CLUSTER_VM_SIZE,
            min_instances=CLUSTER_MIN_NODES,
            max_instances=CLUSTER_MAX_NODES,
            idle_time_before_scale_down=CLUSTER_IDLE_TIMEOUT,
        )
        client.compute.begin_create_or_update(cluster).result()
        print(f"✅ Cluster '{CLUSTER_NAME}' created")


def submit_training_job(client: MLClient, model_key: str, epochs: int, lora_rank: int, lr: float, early_stopping: int = 0):
    """Submit a single training job to the compute cluster."""
    from datetime import datetime

    job_name = f"study-b-{model_key}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Define environment from conda file
    env = Environment(
        name="unsloth-training",
        image="mcr.microsoft.com/azureml/curated/acft-hf-nlp-gpu:latest",
        conda_file=CONDA_FILE,
    )

    # Build the command
    job = command(
        display_name=f"Study B: {model_key}",
        experiment_name="prompttriage-study-b",
        description=f"QLoRA fine-tuning {model_key} for Dense vs MoE benchmark",
        compute=CLUSTER_NAME,
        environment=env,
        code=NOTEBOOKS_DIR,
        command=(
            f"export CURRENT_MODEL={model_key} "
            f"TRAIN_EPOCHS={epochs} "
            f"TRAIN_LORA_RANK={lora_rank} "
            f"TRAIN_LR={lr} "
            f"EARLY_STOPPING_PATIENCE={early_stopping} "
            f"TRAINING_DATA_DIR=${{{{inputs.training_data}}}} "
            f"OUTPUT_BASE_DIR=${{{{outputs.model_output}}}} && "
            f"python study_b_cluster.py"
        ),
        inputs={
            "training_data": Input(type="uri_folder", path=TRAINING_DATA_DIR),
        },
        outputs={
            "model_output": Output(type="uri_folder"),
        },
        tags={
            "study": "B",
            "model": model_key,
            "framework": "unsloth",
        },
    )
    job.name = job_name

    created_job = client.jobs.create_or_update(job)
    print(f"✅ Job submitted: {job_name}")
    print(f"   Studio URL: {created_job.studio_url}")
    return created_job


# ── Known completed training jobs (adapter outputs) ──
TRAINING_JOB_IDS = {
    "qwen3_8b": "study-b-qwen3_8b-20260306-112218",
    "qwen3_14b": "study-b-qwen3_14b-20260306-120736",
    "qwen3_32b": "study-b-qwen3_32b-20260306-120822",
    "qwen3_30b_a3b": "study-b-qwen3_30b_a3b-20260306-121107",
}


def submit_benchmark_job(client: MLClient):
    """Submit benchmark job that generates outputs from all fine-tuned adapters."""
    from datetime import datetime

    job_name = f"study-b-benchmark-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    env = Environment(
        name="unsloth-training",
        image="mcr.microsoft.com/azureml/curated/acft-hf-nlp-gpu:latest",
        conda_file=CONDA_FILE,
    )

    # Build inputs — point to the adapter subfolder in each job's blob output
    # Azure ML stores job outputs at: azureml/<job_name>/model_output/
    # The adapter is in the "adapter" subfolder within model_output
    inputs = {}
    for model_key, job_id in TRAINING_JOB_IDS.items():
        adapter_uri = (
            f"azureml://datastores/workspaceblobstore/paths/"
            f"azureml/{job_id}/model_output/adapter"
        )
        inputs[model_key] = Input(type="uri_folder", path=adapter_uri)

    # Symlink each input to a consistent layout for the benchmark script
    # ADAPTER_BASE/<model_key>/adapter_config.json etc.
    setup_cmds = []
    for model_key in TRAINING_JOB_IDS:
        setup_cmds.append(
            f"mkdir -p /mnt/adapters/{model_key} && "
            f"ln -sf ${{{{inputs.{model_key}}}}}/* /mnt/adapters/{model_key}/"
        )

    setup_cmd = " && ".join(setup_cmds)

    job = command(
        display_name="Study B: Benchmark (all models)",
        experiment_name="prompttriage-study-b",
        description="Generate system prompts from all 4 fine-tuned QLoRA adapters for benchmarking",
        compute=CLUSTER_NAME,
        environment=env,
        code=NOTEBOOKS_DIR,
        command=(
            f"{setup_cmd} && "
            f"export ADAPTER_BASE=/mnt/adapters "
            f"OUTPUT_DIR=${{{{outputs.benchmark_output}}}} && "
            f"python study_b_benchmark.py"
        ),
        inputs=inputs,
        outputs={
            "benchmark_output": Output(type="uri_folder"),
        },
        tags={
            "study": "B",
            "phase": "benchmark",
            "framework": "unsloth",
        },
    )
    job.name = job_name

    created_job = client.jobs.create_or_update(job)
    print(f"✅ Benchmark job submitted: {job_name}")
    print(f"   Studio URL: {created_job.studio_url}")
    return created_job


def check_status(client: MLClient):
    """List recent Study B jobs."""
    print("\n📊 Recent Study B jobs:")
    print(f"{'Name':<45} {'Status':<15} {'Model':<15}")
    print("─" * 75)

    jobs = client.jobs.list(max_results=20)
    for job in jobs:
        # Filter to our Study B jobs by experiment name or job name prefix
        exp = getattr(job, 'experiment_name', '')
        is_study_b = exp == 'prompttriage-study-b' or (job.name and job.name.startswith('study-b-'))
        if not is_study_b:
            continue
        model_tag = job.tags.get("model", "?") if job.tags else "?"
        print(f"{job.name:<45} {job.status:<15} {model_tag:<15}")


def stream_logs(client: MLClient, job_name: str):
    """Stream logs from a running job."""
    print(f"\n📋 Streaming logs for: {job_name}")
    print("─" * 60)
    client.jobs.stream(job_name)


def main():
    parser = argparse.ArgumentParser(description="Submit Study B training/benchmark jobs to Azure ML")
    parser.add_argument("--model", default="qwen3_8b",
                        help="Model to train: qwen3_8b, qwen3_14b, qwen3_32b, qwen3_30b_a3b, or 'all'")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lora-rank", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.0002)
    parser.add_argument("--benchmark", action="store_true",
                        help="Submit benchmark job instead of training")
    parser.add_argument("--retrain-moe", action="store_true",
                        help="Retrain only qwen3_30b_a3b with early stopping (patience=2)")
    parser.add_argument("--early-stopping", type=int, default=0,
                        help="Early stopping patience (0=disabled)")
    parser.add_argument("--status", action="store_true", help="Check job status instead of submitting")
    parser.add_argument("--logs", type=str, help="Stream logs for a specific job name")
    parser.add_argument("--subscription", type=str, help="Azure subscription ID")
    parser.add_argument("--resource-group", type=str, help="Azure resource group")
    parser.add_argument("--workspace", type=str, help="Azure ML workspace name")
    args = parser.parse_args()

    client = get_client(args)

    if args.status:
        check_status(client)
        return

    if args.logs:
        stream_logs(client, args.logs)
        return

    # Ensure cluster exists
    ensure_cluster(client)

    # Benchmark mode
    if args.benchmark:
        submit_benchmark_job(client)
        return

    # Retrain MoE mode
    if args.retrain_moe:
        print("\n🔄 Retraining qwen3_30b_a3b with early stopping...")
        submit_training_job(
            client, "qwen3_30b_a3b",
            epochs=args.epochs,
            lora_rank=args.lora_rank,
            lr=args.lr,
            early_stopping=2,  # patience=2: stop after 2 evals without improvement
        )
        return

    # Submit job(s)
    models = MODELS if args.model == "all" else [args.model]
    if args.model != "all" and args.model not in MODELS:
        print(f"❌ Unknown model: {args.model}")
        print(f"   Available: {', '.join(MODELS)}")
        sys.exit(1)

    for model_key in models:
        submit_training_job(client, model_key, args.epochs, args.lora_rank, args.lr, args.early_stopping)

    print(f"\n{'═' * 60}")
    print(f"  {len(models)} job(s) submitted!")
    print(f"  Check status: python submit_job.py --status")
    print(f"  Stream logs:  python submit_job.py --logs <job-name>")
    print(f"{'═' * 60}")


if __name__ == "__main__":
    main()
