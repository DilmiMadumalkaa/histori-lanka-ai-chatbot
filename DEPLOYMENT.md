# Free No-Card Hosting (Hugging Face + Vercel)

If Render asks for card verification, use this no-card route:
- Backend API on Hugging Face Spaces (Docker)
- Frontend on Vercel (Vite)

## 1. Push your repo to GitHub

Both platforms deploy directly from GitHub.

## 2. Deploy backend to Hugging Face Spaces

1. Create a new Space at https://huggingface.co/spaces
2. Choose:
   - SDK: Docker
   - Visibility: Public or Private (your choice)
3. Connect/select this repository.
4. Spaces will build using the root Dockerfile.

### Backend Secrets in Space Settings

Go to Space -> Settings -> Variables and secrets.
Add these as Secrets:
- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_CHAT_DEPLOYMENT
- AZURE_OPENAI_GPT_DEPLOYMENT
- AZURE_OPENAI_DEPLOYMENT
- AZURE_OPENAI_EMBEDDING_DEPLOYMENT
- PINECONE_API_KEY

Add these as Variables:
- AZURE_OPENAI_API_VERSION=2024-12-01-preview
- AZURE_OPENAI_EMBEDDING_API_VERSION=2024-02-01
- PINECONE_ENV=us-east-1
- PINECONE_INDEX_NAME=historical-sites-sl

Do not set ALLOWED_ORIGINS yet. Set it after frontend URL is live.

## 3. Deploy frontend to Vercel

1. Open https://vercel.com/new
2. Import this repository.
3. For Root Directory, choose frontend.
4. Add Environment Variable:
   - VITE_API_URL=https://<your-space-subdomain>.hf.space
5. Deploy.

## 4. Set backend CORS for frontend

After Vercel gives your frontend URL:
- Add/update backend variable in Hugging Face Space:
  - ALLOWED_ORIGINS=https://<your-vercel-domain>

If you have multiple domains, use comma-separated URLs.

Then restart/rebuild the Space.

## 5. Verify

- API health:
  - https://<your-space-subdomain>.hf.space/api/health
- Frontend chat:
  - open your Vercel URL and send a prompt

## 6. If you need fully local free hosting

You can also keep backend local and expose it with Cloudflare Tunnel (no card), then point Vercel VITE_API_URL to that tunnel URL.
