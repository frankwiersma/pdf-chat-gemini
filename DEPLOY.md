# Deployment Guide

## GitHub Setup

### 1. Create GitHub Repository

```bash
# Go to GitHub and create a new repository named: pdf-chat-gemini
# Do NOT initialize with README, .gitignore, or license

# Then run these commands:
git remote add origin https://github.com/YOUR_USERNAME/pdf-chat-gemini.git
git branch -M main
git push -u origin main
```

### 2. Update README

Edit `README.md` line 29 to use your GitHub username:
```bash
git clone https://github.com/YOUR_USERNAME/pdf-chat-gemini.git
```

## Docker Deployment

### Build Image

```bash
docker build -t pdf-chat-gemini .
```

### Run Container

```bash
docker run -d -p 8501:8501 --name pdf-chat pdf-chat-gemini
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8501:8501"
    restart: unless-stopped
```

Run with: `docker-compose up -d`

## Cloud Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to https://share.streamlit.io/
3. Connect repository
4. Deploy

### Heroku

```bash
# Install Heroku CLI
heroku login
heroku create your-app-name

# Create Procfile
echo "web: streamlit run src/app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

git add Procfile
git commit -m "Add Heroku Procfile"
git push heroku main
```

### AWS EC2

```bash
# SSH into EC2 instance
ssh -i your-key.pem ec2-user@your-instance

# Clone repository
git clone https://github.com/YOUR_USERNAME/pdf-chat-gemini.git
cd pdf-chat-gemini

# Install dependencies
pip install -r requirements.txt

# Run with nohup
nohup streamlit run src/app.py --server.port=8501 --server.address=0.0.0.0 &
```

### Google Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/pdf-chat-gemini

# Deploy
gcloud run deploy pdf-chat-gemini \
  --image gcr.io/PROJECT_ID/pdf-chat-gemini \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Environment Variables

For production deployments, never hardcode API keys. Use environment variables:

```bash
# Set environment variable
export GEMINI_API_KEY=your_api_key_here

# Or use .env file (add to .gitignore!)
echo "GEMINI_API_KEY=your_key" > .env
```

Update `src/app.py` to read from environment if needed.

## Security Checklist

- [ ] API keys not committed to repository
- [ ] .env files in .gitignore
- [ ] HTTPS enabled for production
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Secrets managed securely
- [ ] Dependencies up to date
- [ ] Security headers set

## Monitoring

### Health Check Endpoint

Streamlit provides: `http://your-app:8501/_stcore/health`

### Logging

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Troubleshooting

**Port conflicts**
```bash
# Kill process on port 8501
lsof -ti:8501 | xargs kill -9
```

**Permission issues**
```bash
chmod +x src/app.py
```

**Module not found**
```bash
pip install -r requirements.txt --upgrade
```
