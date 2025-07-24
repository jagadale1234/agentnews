# AgentNews Cloud Setup Checklist

## ✅ Pre-requisites Completed
- [x] Railway PostgreSQL database created
- [x] Gmail App Password generated
- [x] All code files created

## 🔐 GitHub Secrets Setup
Go to: `https://github.com/jagadale1234/agentnews/settings/secrets/actions`

Add these secrets:
- [ ] `GMAIL_USER` = `jagadaleanish@gmail.com`
- [ ] `GMAIL_APP_PASSWORD` = `nnuruzhcpudvuoar`
- [ ] `DATABASE_URL` = `postgresql://postgres:zMzsaURtbJgkUKKjxkkUjbIgoPLSMjYl@caboose.proxy.rlwy.net:52771/railway`
- [ ] `NEWSLETTER_BASE_URL` = `https://your-app-name.up.railway.app` (update after deployment)
- [ ] `FLASK_SECRET_KEY` = `your-super-secret-production-key`

## 🚀 Railway Deployment
1. [ ] Go to [railway.app](https://railway.app)
2. [ ] Sign in with GitHub
3. [ ] Create "New Project" → "Deploy from GitHub repo"
4. [ ] Select your `agentnews` repository
5. [ ] Add environment variables in Railway dashboard
6. [ ] Wait for deployment to complete
7. [ ] Copy your Railway app URL
8. [ ] Update `NEWSLETTER_BASE_URL` GitHub secret with Railway URL

## 🧪 Testing
1. [ ] Test web interface: Visit your Railway URL
2. [ ] Subscribe with test email via web interface
3. [ ] Test GitHub Actions: Go to Actions tab → "AgentNews Weekly Newsletter" → "Run workflow"
4. [ ] Check that newsletter was sent successfully
5. [ ] Test unsubscribe link in received email

## 🔄 Automation Verification
- [ ] GitHub Actions workflow runs every Monday at 9 AM UTC
- [ ] Newsletter is sent to all active subscribers
- [ ] Unsubscribe links work correctly
- [ ] Database is updated properly

## 🎉 Go Live!
Once all items are checked:
- [ ] Add real subscribers via web interface
- [ ] Monitor GitHub Actions runs
- [ ] Check Railway app logs if needed
- [ ] Your automated newsletter is now live!

## 📞 Support URLs
- GitHub Repository: https://github.com/jagadale1234/agentnews
- Railway Dashboard: https://railway.app/dashboard
- GitHub Actions: https://github.com/jagadale1234/agentnews/actions
- Railway Logs: Available in Railway dashboard
