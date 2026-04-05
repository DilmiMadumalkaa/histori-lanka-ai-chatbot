# Azure Deployment Setup For RAG (Step 9 + Step 10)

This guide configures Azure so the chatbot can run:
- Step 9: GPT call with user query + RAG context + instructions
- Step 10: Response quality check and improvement suggestions

## 1. Prerequisites

- Active Azure subscription
- Azure OpenAI resource already created in an allowed region
- Access to Azure AI Foundry or Azure OpenAI Studio

## 2. Create required deployments

Open your Azure OpenAI resource and go to Deployments.

Create embedding deployment:
- Model: text-embedding-3-large
- Deployment name: embed-3-large

Create chat deployment:
- Model: choose an available chat model in your resource (for example gpt-4.1-mini)
- Deployment name: use the exact name you will place in .env

If deployment creation fails with policy errors, switch to an allowed region/resource context first.

## 3. Configure .env

Set one consistent Azure block only.

Required keys:
- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_API_VERSION
- AZURE_OPENAI_EMBEDDING_API_VERSION
- AZURE_OPENAI_EMBEDDING_DEPLOYMENT
- AZURE_OPENAI_CHAT_DEPLOYMENT

Recommended values:
- AZURE_OPENAI_API_VERSION=2024-12-01-preview
- AZURE_OPENAI_EMBEDDING_API_VERSION=2024-02-01
- AZURE_OPENAI_EMBEDDING_DEPLOYMENT=embed-3-large

Notes:
- Endpoint must be base URL only, for example https://your-resource.openai.azure.com/
- Do not keep duplicate AZURE_OPENAI_* keys in .env
- Chat deployment name must exactly match the deployment in Azure

## 4. Run Step 9 + Step 10 locally

From project root:

```powershell
.\venv\Scripts\python.exe scripts\rag_pipeline\step9_step10_runner.py --query "Tell me about Sigiriya" --style informative
```

Expected behavior:
- Embedding call returns HTTP 200
- GPT chat call returns HTTP 200
- Script prints response quality score and improvement suggestions

## 5. Run API after successful Step 9/10

```powershell
.\venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Health check:
- GET http://127.0.0.1:8000/api/health should return status ok

Chat check:
- POST http://127.0.0.1:8000/api/chat should return status 200

## 6. Troubleshooting

401 PermissionDenied:
- API key and endpoint are from different resources
- Wrong key copied

404 DeploymentNotFound:
- AZURE_OPENAI_CHAT_DEPLOYMENT does not exist in current resource
- Deployment name typo

Policy region error (RequestDisallowedByAzure):
- Deployment is being attempted in blocked region
- Switch Foundry resource/project context to an allowed-region resource

## 7. Security

If keys were exposed in logs or screenshots, rotate them immediately:
- Azure OpenAI keys
- Pinecone API key
