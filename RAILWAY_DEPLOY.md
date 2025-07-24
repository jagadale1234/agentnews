# Railway Deployment Commands

## Install Railway CLI
```bash
npm install -g @railway/cli
```

## Login to Railway
```bash
railway login
```

## Initialize and Deploy
```bash
# In your project directory
cd agentnews
railway init
railway up
```

## Set Environment Variables
```bash
railway variables set GMAIL_USER=jagadaleanish@gmail.com
railway variables set GMAIL_APP_PASSWORD=nnuruzhcpudvuoar
railway variables set DATABASE_URL="postgresql://postgres:zMzsaURtbJgkUKKjxkkUjbIgoPLSMjYl@caboose.proxy.rlwy.net:52771/railway"
railway variables set FLASK_SECRET_KEY=your-super-secret-production-key
```

## View Logs
```bash
railway logs
```

## Open in Browser
```bash
railway open
```
