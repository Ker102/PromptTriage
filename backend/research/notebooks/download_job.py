from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential, AzureCliCredential, ChainedTokenCredential
import os

credential = ChainedTokenCredential(AzureCliCredential(), DefaultAzureCredential())
ml_client = MLClient(credential, '2405d969-2c8b-4b70-949e-f250bc25fa9f', 'DefaultResourceGroup-eastus2', 'qwentrain')

job_name = 'study-a-rag-benchmark-20260315-223434'
print(f"Downloading outputs for Job: {job_name}")
ml_client.jobs.download(name=job_name, download_path='named-outputs/study_a', output_name='study_a_output')
print("Download complete.")
