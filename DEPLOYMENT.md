# Deploy Historical Sites Chatbot on Render

This repo is configured to deploy as two Render services:
- FastAPI backend (Python web service)
- React frontend (static site)

## 1. Push code to GitHub

Render deploys from GitHub, so push your current branch first.

## 2. Create Render services from blueprint

1. In Render dashboard, click New + then Blueprint.
2. Select your GitHub repository.
3. Render reads render.yaml and creates:
   - historical-sites-chatbot-api
   - historical-sites-chatbot-frontend

## 3. Configure backend environment variables

Set these values in the backend service:
- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_CHAT_DEPLOYMENT (use your fine-tuned deployment, e.g. historilanka-ft-chat)
- AZURE_OPENAI_GPT_DEPLOYMENT (same as above)
- AZURE_OPENAI_DEPLOYMENT (same as above)
- AZURE_OPENAI_EMBEDDING_DEPLOYMENT
- PINECONE_API_KEY

Defaults already set by render.yaml:
- AZURE_OPENAI_API_VERSION=2024-02-01
- AZURE_OPENAI_EMBEDDING_API_VERSION=2024-02-01
- PINECONE_INDEX_NAME=historical-sites-sl
- PINECONE_ENV=us-east-1

## 4. Connect frontend to backend

After backend is live, set frontend variable:
- VITE_API_URL=https://<your-backend>.onrender.com

Redeploy frontend after saving this value.

## 5. Set backend CORS for frontend URL

After frontend is live, set backend variable:
- ALLOWED_ORIGINS=https://<your-frontend>.onrender.com

For multiple domains, use comma-separated values.

## 6. Verify

- Backend health should return status ok:
  - https://<your-backend>.onrender.com/api/health
- Open frontend and send a test prompt.

## Notes

- Free Render instances may sleep when idle.
- Keep secrets only in Render environment variables.
