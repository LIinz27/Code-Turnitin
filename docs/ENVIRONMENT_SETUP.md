# Environment Setup Guide

## 🔐 Environment Variables Configuration

### 1. Create Environment File
```bash
# Copy template to actual environment file
cp config/.env.template config/.env
```

### 2. Configure GitHub Token
1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select permissions:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories only)
4. Copy the generated token
5. Add to `config/.env`:
   ```
   GITHUB_TOKEN=ghp_your_actual_token_here
   ```

### 3. Verify Setup
```bash
# Test if token is working
python -c "
import os
from src.scrapers.github_scraper import search_github_repositories
print('Token loaded:', 'GITHUB_TOKEN' in os.environ)
print('Rate limit should be 5000/hour if token is valid')
"
```

## ⚠️ Security Notes

- **Never commit `.env` files** - Contains sensitive tokens
- **Use `.env.template`** - For sharing configuration structure
- **Rotate tokens regularly** - GitHub recommends periodic token rotation
- **Minimum permissions** - Only grant necessary repository access

## 🚀 Quick Start

1. `cp config/.env.template config/.env`
2. Edit `config/.env` with your GitHub token
3. Run `python app.py`
4. Access http://127.0.0.1:5000

## 🔍 Troubleshooting

**Rate Limit Issues:**
- Check if token is loaded: Look for "Loaded GITHUB_TOKEN" in console
- Verify token permissions in GitHub settings
- Ensure token isn't expired

**File Not Found:**
- Ensure `config/.env` exists (not `.env.template`)
- Check file permissions and location
