# AgentNews - Automated AI Newsletter

A simple Python script that scrapes AI agent news and sends automated newsletters to subscribers.

## Features

- 🔍 **Web Scraping**: Automatically scrapes the latest AI agent news from aiagentsdirectory.com
- 📧 **Email Automation**: Sends formatted newsletters via Gmail SMTP
- 📋 **Subscriber Management**: Reads email addresses from a CSV file
- 📊 **Logging**: Comprehensive logging for monitoring and debugging
- 🛡️ **Error Handling**: Robust error handling and fallback mechanisms

## Requirements

- Python 3.7+
- Gmail account with App Password enabled
- Internet connection for web scraping

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Gmail App Password:**
   - Go to your Google Account settings
   - Enable 2-factor authentication
   - Generate an App Password for "Mail"
   - Save this password (you'll need it for the environment variables)

3. **Set environment variables:**
   ```bash
   export GMAIL_USER="your-email@gmail.com"
   export GMAIL_APP_PASSWORD="your-app-password"
   ```
   
   Or create a `.env` file:
   ```
   GMAIL_USER=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-app-password
   ```

4. **Add subscribers:**
   Edit `subscribers.csv` and add email addresses, one per line:
   ```
   subscriber1@example.com
   subscriber2@example.com
   user@company.org
   ```

## Usage

Run the newsletter automation:

```bash
python agent_news.py
```

The script will:
1. Scrape the latest AI agent news from aiagentsdirectory.com
2. Format a newsletter with the top 5 articles
3. Send the newsletter to all subscribers in `subscribers.csv`
4. Log all activities to `agent_news.log`

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
