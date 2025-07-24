# AgentNews - Automated AI Newsletter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

A simple Python script that scrapes AI agent news and sends automated newsletters to subscribers.

## 🚀 Features

- 🔍 **Web Scraping**: Automatically scrapes the latest AI agent news from aiagentsdirectory.com
- 📧 **Email Automation**: Sends formatted newsletters via Gmail SMTP
- 📋 **Subscriber Management**: Reads email addresses from a CSV file
- 📊 **Logging**: Comprehensive logging for monitoring and debugging
- 🛡️ **Error Handling**: Robust error handling and fallback mechanisms

## 📋 Requirements

- Python 3.7+
- Gmail account with App Password enabled
- Internet connection for web scraping

## 🔧 Quick Start

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

4. **Add subscribers:**
   ```bash
   cp subscribers.example.csv subscribers.csv
   # Edit subscribers.csv with real email addresses
   ```

5. **Send your first newsletter:**
   ```bash
   python agent_news.py
   ```

## Email Format

The newsletter includes:
- **Subject**: "AgentNews Weekly"
- **Content**: Top 5 AI agent news articles with titles and links
- **Unsubscribe**: Instructions to reply with "UNSUBSCRIBE"

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
