# AgentNews - Automated AI Newsletter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

A simple Python script that scrapes AI agent news and sends automated newsletters to subscribers.

## Features

- **Web Scraping**: Automatically scrapes the latest AI agent news from aiagentsdirectory.com
- **Email Automation**: Sends formatted newsletters via Gmail SMTP
- **Cloud Database**: PostgreSQL/SQLite support for reliable subscriber management
- **Smart Unsubscribe**: Secure token-based unsubscribe system
- **Web Interface**: Professional web-based subscription management
- **Welcome Emails**: Automatic welcome emails with latest news for new subscribers
- **GitHub Actions**: Automated daily newsletter delivery via cloud cron jobs
- **Analytics**: Subscriber tracking and management
- **Security**: Secure token generation and database management
- **Scalable**: Ready for cloud deployment and high volume

## Requirements

- Python 3.7+
- Gmail account with App Password enabled
- Internet connection for web scraping

## Quick Start

### Local Development
1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/agentnews.git
   cd agentnews
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Gmail credentials:**
   ```bash
   python setup.py
   ```

4. **Run locally (uses SQLite database):**
   ```bash
   python agent_news_cloud.py
   ```

5. **Start web interface:**
   ```bash
   python web_interface.py
   ```

### Cloud Deployment
For automated newsletters with GitHub Actions and cloud database:

1. **Set up cloud database** (Railway/Heroku PostgreSQL)
2. **Configure GitHub Secrets** (see DEPLOYMENT.md)
3. **Push to GitHub** - newsletters will run automatically every Monday!

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed cloud setup instructions.

## Email Format

The newsletter includes:
- **Subject**: "AgentNews Weekly"
- **Content**: Top 5 AI agent news articles with titles and links
- **Unsubscribe**: Personalized unsubscribe instructions for each subscriber

## Subscription Management

### Command Line Interface
Use the `unsubscribe_handler.py` script to manage subscribers:

```bash
# Unsubscribe a user
python unsubscribe_handler.py unsubscribe user@example.com

# Subscribe a new user
python unsubscribe_handler.py subscribe newuser@example.com

# List all subscribers
python unsubscribe_handler.py list
```

### Web Interface (Optional)
Start the web interface for browser-based subscription management:

```bash
# Install Flask first
pip install flask

# Start the web server
python web_interface.py
```

Then visit your deployed web interface to manage subscriptions through a web browser.

## File Structure

```
├── agent_news.py          # Main script
├── requirements.txt       # Python dependencies
├── subscribers.csv        # Email addresses (one per line)
├── agent_news.log        # Log file (auto-generated)
└── README.md             # This file
```

## Configuration

You can modify these settings in `agent_news.py`:
- `max_articles`: Number of articles to include (default: 5)
- `csv_file`: Path to subscribers CSV file
- Email subject and formatting

## Security Notes

- **Never commit your Gmail credentials** to version control
- Use environment variables or a secure config file
- Consider using a dedicated email account for newsletters
- The App Password should be treated like a regular password

## Automation

To run automatically, set up a cron job:

```bash
# Run every Monday at 9 AM
0 9 * * 1 /usr/bin/python3 /path/to/agent_news.py
```

## Handling Unsubscribe Requests

The newsletter includes personalized unsubscribe instructions. When users reply with "UNSUBSCRIBE" or follow the unsubscribe instructions, you can:

1. **Manual Processing**: Use the command-line tool to remove subscribers
2. **Web Interface**: Let users unsubscribe themselves via the web interface
3. **Email Processing**: Check your email for unsubscribe requests and process them manually

Example unsubscribe workflow:
1. User receives newsletter with personalized unsubscribe instructions
2. User replies with "UNSUBSCRIBE" or emails you directly
3. You run: `python unsubscribe_handler.py unsubscribe user@example.com`
4. User is automatically removed from the subscriber list

## Troubleshooting

**Common Issues:**

1. **Gmail Authentication Error**
   - Ensure 2FA is enabled on your Gmail account
   - Use App Password, not your regular password
   - Check that environment variables are set correctly

2. **No Articles Found**
   - Check internet connection
   - The website structure may have changed
   - Check logs for specific error messages

3. **No Subscribers**
   - Ensure `subscribers.csv` exists and has valid email addresses
   - Check file permissions

4. **Email Sending Fails**
   - Verify Gmail credentials
   - Check if Gmail is blocking the login attempt
   - Ensure recipients' email addresses are valid

## License

This project is open source and available under the MIT License.
