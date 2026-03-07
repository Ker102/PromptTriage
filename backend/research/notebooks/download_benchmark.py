"""Download benchmark outputs from the latest job."""
import os
import json
os.environ['PATH'] = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin' + os.pathsep + os.environ.get('PATH', '')

from azure.ai.ml import MLClient
from azure.identity import AzureCliCredential

def main():
    c = MLClient(AzureCliCredential(), '2405d969-2c8b-4b70-949e-f250bc25fa9f', 'DefaultResourceGroup-eastus2', 'qwentrain')
    
    # Find the latest benchmark job
    benchmark_job = None
    for j in c.jobs.list(max_results=20):
        if j.name and j.name.startswith('study-b-benchmark'):
            benchmark_job = j
            break
            
    if not benchmark_job:
        print("No benchmark jobs found.")
        return
        
    print(f"Downloading from job: {benchmark_job.name}")
    
    # Download the named output "benchmark_output"
    c.jobs.download(name=benchmark_job.name, download_path=".", output_name="benchmark_output")
    print("Download complete. Check benchmark_output/benchmark_outputs.json")

if __name__ == "__main__":
    main()
