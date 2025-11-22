# GitHub Repository Setup Instructions

## Step 1: Create New GitHub Repository

1. Go to https://github.com/new
2. Repository name: `pdf-chat-gemini`
3. Description: `Intelligent PDF document analysis using Google Gemini AI with File Search capabilities`
4. Set to **Public**
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 2: Push Your Code

The repository is already set up locally. Just run:

```bash
git push -u origin main
```

If you get an authentication error, you may need to:
- Use a Personal Access Token instead of password
- Or set up SSH keys (recommended)

### Using Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Copy the token
4. When pushing, use the token as password

### Using SSH (Recommended)

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
# Then update remote:
git remote set-url origin git@github.com:holys519/pdf-chat-gemini.git
git push -u origin main
```

## Step 3: Verify

After pushing, your repository should be live at:
https://github.com/holys519/pdf-chat-gemini

## Step 4: Add Topics (Optional)

On GitHub repository page:
1. Click "About" gear icon
2. Add topics: `gemini-ai`, `pdf-analysis`, `streamlit`, `python`, `document-search`, `ai-assistant`
3. Save

## Step 5: Add Screenshot (Optional)

1. Take a screenshot of the app running
2. Save as `docs/screenshot.png`
3. Commit and push:
```bash
mkdir docs
# Add your screenshot to docs/screenshot.png
git add docs/screenshot.png
git commit -m "Add application screenshot"
git push
```

## Repository Settings Recommendations

### General
- Enable "Issues" for bug tracking
- Enable "Discussions" for Q&A
- Consider enabling "Sponsorships" if you want

### Branches
- Set `main` as default branch
- Consider adding branch protection rules

### Pages (Optional)
- You can enable GitHub Pages to host documentation
- Source: Deploy from a branch → `main` → `/docs`

## Next Steps

1. Add repository description on GitHub
2. Add website: Your deployed app URL (if deployed)
3. Star your own repo to make it easier to find
4. Share the repository link

Your repository is ready to go! 🚀
