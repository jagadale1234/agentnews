# AgentNews Cloud Deployment Guide

## 🚀 Cloud Deployment Options

### Option 1: GitHub Actions + Railway/Heroku + PostgreSQL

#### Step 1: Set up Cloud Database
**Railway (Recommended)**
1. Go to [Railway.app](https://railway.app)
2. Create a new project
3. Add PostgreSQL service
4. Copy the DATABASE_URL from the database service

**Heroku Postgres**
1. Create Heroku app: `heroku create your-agentnews-app`
2. Add PostgreSQL: `heroku addons:create heroku-postgresql:hobby-dev`
3. Get DATABASE_URL: `heroku config:get DATABASE_URL`

#### Step 2: Configure GitHub Secrets
In your GitHub repository, go to Settings → Secrets and variables → Actions

Add these secrets:
```
GMAIL_USER = your-email@gmail.com
GMAIL_APP_PASSWORD = your-16-char-app-password
DATABASE_URL = postgresql://user:pass@host:port/db
NEWSLETTER_BASE_URL = https://your-domain.com
```

#### Step 3: Deploy Web Interface
**Railway Deployment:**
1. Connect your GitHub repo to Railway
2. Set environment variables in Railway dashboard
3. Deploy the web interface

**Heroku Deployment:**
```bash
# Add Procfile
echo "web: python web_interface.py" > Procfile

# Deploy
git add .
git commit -m "Add cloud deployment"
git push heroku main
```

#### Step 4: GitHub Actions Automation
The newsletter will now run automatically every Monday at 9 AM UTC!

### Option 2: Simple VPS Deployment

#### Step 1: Set up VPS (DigitalOcean, Linode, etc.)
```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip postgresql postgresql-contrib

# Clone your repo
git clone https://github.com/yourusername/agentnews.git
cd agentnews

# Install Python dependencies
pip3 install -r requirements.txt
```

#### Step 2: Set up PostgreSQL
```bash
sudo -u postgres psql
CREATE DATABASE agentnews;
CREATE USER agentnews_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE agentnews TO agentnews_user;
\q
```

#### Step 3: Configure Environment
```bash
# Create .env file
cat > .env << EOF
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
DATABASE_URL=postgresql://agentnews_user:your_password@localhost/agentnews
NEWSLETTER_BASE_URL=https://your-domain.com
EOF
```

#### Step 4: Set up Cron Job
```bash
# Edit crontab
crontab -e

# Add this line (runs every Monday at 9 AM)
0 9 * * 1 cd /path/to/agentnews && python3 agent_news_cloud.py
```

#### Step 5: Deploy Web Interface
```bash
# Install nginx
sudo apt install nginx

# Configure nginx (create /etc/nginx/sites-available/agentnews)
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/agentnews /etc/nginx/sites-enabled/
sudo nginx -s reload

# Run web interface with systemd
sudo tee /etc/systemd/system/agentnews-web.service > /dev/null <<EOF
[Unit]
Description=AgentNews Web Interface
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/agentnews
Environment=PATH=/usr/bin
ExecStart=/usr/bin/python3 web_interface.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable agentnews-web
sudo systemctl start agentnews-web
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password

# Database (choose one)
DATABASE_URL=postgresql://user:pass@host:port/db  # For cloud
# OR it will use SQLite locally if not set

# Optional
NEWSLETTER_BASE_URL=https://your-domain.com  # For unsubscribe links
FLASK_SECRET_KEY=your-secret-key-for-web-sessions
```

### Gmail App Password Setup
1. Enable 2-factor authentication in your Google account
2. Go to Google Account → Security → App passwords
3. Generate an app password for "Mail"
4. Use this 16-character password (not your regular password)

## 📊 Monitoring

### Check Newsletter Status
```bash
# View logs
tail -f agent_news.log

# Check database
python3 -c "from agent_news_cloud import DatabaseManager; db = DatabaseManager(); print(f'Subscribers: {db.get_subscriber_count()}')"
```

### Health Check Endpoint
```bash
curl https://your-domain.com/health
```

## 🔐 Security Best Practices

1. **Environment Variables**: Never commit secrets to git
2. **Database**: Use connection pooling for high traffic
3. **Web Interface**: Use HTTPS in production
4. **Tokens**: Unsubscribe tokens are unique and secure
5. **Rate Limiting**: Consider adding rate limiting to web endpoints

## 📈 Scaling

### For High Volume (1000+ subscribers)
1. Use connection pooling for database
2. Add Redis for caching
3. Use Celery for background tasks
4. Consider email service like SendGrid instead of Gmail

### Monitoring & Analytics
1. Add Google Analytics to web interface
2. Track open rates with pixel tracking
3. Monitor bounce rates and unsubscribes
4. Set up alerts for failed deliveries

## 🛠️ Troubleshooting

### Common Issues
1. **Gmail Blocks**: Use App Password, not regular password
2. **Database Connection**: Check DATABASE_URL format
3. **Cron Not Running**: Check cron logs: `grep CRON /var/log/syslog`
4. **Web Interface Down**: Check systemd status: `systemctl status agentnews-web`

### Debug Commands
```bash
# Test newsletter manually
python3 agent_news_cloud.py

# Test web interface locally
python3 web_interface.py

# Check database connection
python3 -c "from agent_news_cloud import DatabaseManager; DatabaseManager()"
```
