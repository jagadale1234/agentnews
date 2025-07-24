#!/usr/bin/env python3
"""
Cloud-enabled AgentNews with Database Integration
================================================

Enhanced version with cloud database support for subscriber management.
Supports PostgreSQL (for cloud deployment) and SQLite (for local development).
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import yagmail

# Try to import PostgreSQL support (optional)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("PostgreSQL support not available. Install with: pip install psycopg2-binary")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_news.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles database operations for subscriber management"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.is_postgres = self.database_url and self.database_url.startswith('postgresql')
        
        if self.is_postgres and not POSTGRES_AVAILABLE:
            raise ImportError("PostgreSQL support required but psycopg2 not installed")
        
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        if self.is_postgres:
            return psycopg2.connect(self.database_url)
        else:
            # Use SQLite for local development
            db_path = 'subscribers.db'
            return sqlite3.connect(db_path)
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            if self.is_postgres:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS subscribers (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        unsubscribed_at TIMESTAMP NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        unsubscribe_token VARCHAR(64) UNIQUE
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_subscribers_active ON subscribers(is_active);
                """)
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS subscribers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        unsubscribed_at TIMESTAMP NULL,
                        is_active BOOLEAN DEFAULT 1,
                        unsubscribe_token TEXT UNIQUE
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_subscribers_active ON subscribers(is_active);
                """)
            
            conn.commit()
    
    def add_subscriber(self, email: str) -> tuple:
        """
        Add a new subscriber
        
        Returns:
            (success: bool, message: str, is_new_subscriber: bool)
        """
        import uuid
        unsubscribe_token = str(uuid.uuid4())[:32]
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # First check if subscriber already exists
                if self.is_postgres:
                    cursor.execute("SELECT is_active FROM subscribers WHERE email = %s", (email,))
                else:
                    cursor.execute("SELECT is_active FROM subscribers WHERE email = ?", (email,))
                
                existing = cursor.fetchone()
                is_new_subscriber = existing is None
                
                if self.is_postgres:
                    cursor.execute("""
                        INSERT INTO subscribers (email, unsubscribe_token, is_active)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (email) DO UPDATE SET
                            is_active = %s,
                            unsubscribed_at = NULL,
                            unsubscribe_token = %s
                    """, (email, unsubscribe_token, True, True, unsubscribe_token))
                else:
                    cursor.execute("""
                        INSERT OR REPLACE INTO subscribers (email, unsubscribe_token, is_active, unsubscribed_at)
                        VALUES (?, ?, 1, NULL)
                    """, (email, unsubscribe_token))
                
                conn.commit()
                logger.info(f"Successfully added subscriber: {email} (new: {is_new_subscriber})")
                return True, "Successfully subscribed!", is_new_subscriber
                
        except Exception as e:
            logger.error(f"Error adding subscriber {email}: {e}")
            return False, f"Error: {str(e)}", False
    
    def remove_subscriber(self, email: str) -> tuple:
        """
        Remove/unsubscribe a subscriber
        
        Returns:
            (success: bool, message: str)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.is_postgres:
                    cursor.execute("""
                        UPDATE subscribers 
                        SET is_active = %s, unsubscribed_at = CURRENT_TIMESTAMP
                        WHERE email = %s AND is_active = %s
                    """, (False, email, True))
                else:
                    cursor.execute("""
                        UPDATE subscribers 
                        SET is_active = 0, unsubscribed_at = CURRENT_TIMESTAMP
                        WHERE email = ? AND is_active = 1
                    """, (email,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Successfully unsubscribed: {email}")
                    return True, "Successfully unsubscribed!"
                else:
                    logger.warning(f"Email not found or already unsubscribed: {email}")
                    return False, "Email not found in subscriber list"
                    
        except Exception as e:
            logger.error(f"Error removing subscriber {email}: {e}")
            return False, f"Error: {str(e)}"
    
    def get_active_subscribers(self) -> List[Dict[str, str]]:
        """Get all active subscribers"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.is_postgres:
                    cursor.execute("""
                        SELECT email, unsubscribe_token 
                        FROM subscribers 
                        WHERE is_active = %s
                        ORDER BY subscribed_at DESC
                    """, (True,))
                else:
                    cursor.execute("""
                        SELECT email, unsubscribe_token 
                        FROM subscribers 
                        WHERE is_active = 1
                        ORDER BY subscribed_at DESC
                    """)
                
                results = cursor.fetchall()
                
                if self.is_postgres:
                    return [{'email': row[0], 'unsubscribe_token': row[1]} for row in results]
                else:
                    return [{'email': row[0], 'unsubscribe_token': row[1]} for row in results]
                    
        except Exception as e:
            logger.error(f"Error getting subscribers: {e}")
            return []
    
    def get_subscriber_count(self) -> int:
        """Get count of active subscribers"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.is_postgres:
                    cursor.execute("SELECT COUNT(*) FROM subscribers WHERE is_active = %s", (True,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM subscribers WHERE is_active = 1")
                
                result = cursor.fetchone()
                if result is not None:
                    return result[0]
                else:
                    return 0
                
        except Exception as e:
            logger.error(f"Error getting subscriber count: {e}")
            return 0


class CloudNewsletterEmailer:
    """Enhanced emailer with cloud database integration"""
    
    def __init__(self, gmail_user: str, gmail_password: str, database_url: Optional[str] = None):
        self.gmail_user = gmail_user
        self.gmail_password = gmail_password
        self.db = DatabaseManager(database_url)
    
    def format_newsletter(self, articles: List[Dict[str, str]], subscriber_data: Dict[str, str]) -> str:
        """
        Format articles into newsletter with unsubscribe token
        """
        current_date = datetime.now().strftime("%B %d, %Y")
        email = subscriber_data['email']
        unsubscribe_token = subscriber_data['unsubscribe_token']
        
        # Create unsubscribe URL (you'll need to replace with your actual domain)
        base_url = os.getenv('NEWSLETTER_BASE_URL', 'https://agentnews-production.up.railway.app')
        unsubscribe_url = f"{base_url}/unsubscribe?token={unsubscribe_token}"
        
        email_body = f"""AgentNews Daily - {current_date}
{'=' * 50}

Welcome to today's AgentNews! Here are the top AI agent stories:

"""
        
        for i, article in enumerate(articles, 1):
            email_body += f"{i}. {article['title']}\n"
            email_body += f"   Link: {article['link']}\n"
            email_body += f"   Summary: {article['summary']}\n\n"
        
        email_body += f"""
==================================================

Thanks for reading AgentNews! Stay ahead of the AI agent revolution.

To unsubscribe: Click here: {unsubscribe_url}
Or reply with "UNSUBSCRIBE" to {self.gmail_user}

Best regards,
The AgentNews Team
"""
        
        return email_body
    
    def send_newsletter(self, articles: List[Dict[str, str]]) -> bool:
        """Send newsletter to all active subscribers"""
        if not articles:
            logger.error("No articles to send")
            return False
        
        subscribers = self.db.get_active_subscribers()
        if not subscribers:
            logger.error("No active subscribers found")
            return False
        
        try:
            yag = yagmail.SMTP(self.gmail_user, self.gmail_password)
            subject = "AgentNews Daily"
            
            logger.info(f"Sending newsletter to {len(subscribers)} subscribers")
            
            for subscriber in subscribers:
                try:
                    email_body = self.format_newsletter(articles, subscriber)
                    
                    yag.send(
                        to=subscriber['email'],
                        subject=subject,
                        contents=email_body
                    )
                    logger.info(f"Newsletter sent to {subscriber['email']}")
                    
                except Exception as e:
                    logger.error(f"Failed to send to {subscriber['email']}: {e}")
                    continue
            
            logger.info("Newsletter sending completed!")
            return True
            
        except Exception as e:
            logger.error(f"Error sending newsletter: {e}")
            return False
    
    def send_welcome_email(self, subscriber_email: str) -> bool:
        """Send immediate welcome email with latest news to new subscriber"""
        try:
            # Get the subscriber data
            subscribers = self.db.get_active_subscribers()
            subscriber_data = None
            for sub in subscribers:
                if sub['email'] == subscriber_email:
                    subscriber_data = sub
                    break
            
            if not subscriber_data:
                logger.error(f"Subscriber data not found for {subscriber_email}")
                return False
            
            # Scrape fresh articles for welcome email
            scraper = AgentNewsletterScraper()
            articles = scraper.scrape_latest_news(max_articles=3)  # Send 3 articles for welcome
            
            if not articles:
                logger.warning("No articles available for welcome email, sending welcome message only")
                articles = [{
                    'title': 'Welcome to AgentNews!',
                    'link': 'https://aiagentsdirectory.com',
                    'summary': 'Stay tuned for the latest AI agent news and updates.'
                }]
            
            # Create welcome email content
            email_body = self.format_welcome_email(articles, subscriber_data)
            
            yag = yagmail.SMTP(self.gmail_user, self.gmail_password)
            subject = "Welcome to AgentNews! Here's what's happening in AI Agents"
            
            yag.send(
                to=subscriber_email,
                subject=subject,
                contents=email_body
            )
            
            logger.info(f"Welcome email sent to {subscriber_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {subscriber_email}: {e}")
            return False
    
    def format_welcome_email(self, articles: List[Dict[str, str]], subscriber_data: Dict[str, str]) -> str:
        """Format welcome email with latest news"""
        current_date = datetime.now().strftime("%B %d, %Y")
        email = subscriber_data['email']
        unsubscribe_token = subscriber_data['unsubscribe_token']
        
        base_url = os.getenv('NEWSLETTER_BASE_URL', 'https://agentnews-production.up.railway.app')
        unsubscribe_url = f"{base_url}/unsubscribe?token={unsubscribe_token}"
        
        email_body = f"""Welcome to AgentNews! - {current_date}
{'=' * 50}

Hello and welcome to AgentNews!

Thank you for subscribing to our AI agent newsletter. You'll now receive daily updates about the latest developments in the AI agent space.

Here are some of the latest stories to get you started:

"""
        
        for i, article in enumerate(articles, 1):
            email_body += f"{i}. {article['title']}\n"
            email_body += f"   Link: {article['link']}\n"
            email_body += f"   Summary: {article['summary']}\n\n"
        
        email_body += f"""
==================================================

What to expect:
• Daily newsletter with the latest AI agent news
• Curated articles from top sources
• Updates on new tools, research, and industry trends

Thanks for joining our community of AI agent enthusiasts!

To unsubscribe: Click here: {unsubscribe_url}
Or reply with "UNSUBSCRIBE" to {self.gmail_user}

Best regards,
The AgentNews Team
"""
        
        return email_body


class AgentNewsletterScraper:
    """Scrapes AI agent news from aiagentsdirectory.com"""
    
    def __init__(self):
        self.base_url = "https://aiagentsdirectory.com"
        self.blog_url = f"{self.base_url}/blog"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_latest_news(self, max_articles: int = 5) -> List[Dict[str, str]]:
        """Scrape the latest AI agent news articles"""
        try:
            logger.info(f"Scraping news from {self.blog_url}")
            response = self.session.get(self.blog_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            article_selectors = [
                'a[href*="/blog/"]',
                '.article-link',
                '[data-article]',
                'article a',
            ]
            
            article_links = []
            for selector in article_selectors:
                links = soup.select(selector)
                if links:
                    article_links = links
                    break
            
            if not article_links:
                logger.info("Trying homepage for latest articles section")
                home_response = self.session.get(self.base_url, timeout=10)
                home_response.raise_for_status()
                home_soup = BeautifulSoup(home_response.content, 'html.parser')
                article_links = home_soup.select('a[href*="/blog/"]')
            
            logger.info(f"Found {len(article_links)} potential article links")
            
            seen_links = set()
            for link in article_links[:max_articles * 2]:
                if len(articles) >= max_articles:
                    break
                    
                href = link.get('href', '')
                if not href or href in seen_links:
                    continue
                
                # Ensure href is a string
                if isinstance(href, list):
                    href = href[0] if href else ''
                href = str(href)
                
                if href.startswith('/'):
                    href = self.base_url + href
                elif not href.startswith('http'):
                    continue
                
                seen_links.add(href)
                title = link.get_text(strip=True)
                
                if title and len(title) > 10:
                    articles.append({
                        'title': title,
                        'link': href,
                        'summary': title  # For MVP, use title as summary
                    })
            
            logger.info(f"Successfully scraped {len(articles)} articles")
            return articles[:max_articles]
            
        except Exception as e:
            logger.error(f"Error scraping news: {e}")
            return []


def load_env_file():
    """Load environment variables from .env file"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


def main():
    """Main function for cloud newsletter automation"""
    logger.info("Starting AgentNews cloud automation")
    
    # Load environment variables
    load_env_file()
    
    # Get credentials
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    database_url = os.getenv('DATABASE_URL')
    
    if not gmail_user or not gmail_password:
        logger.error("Gmail credentials not found in environment variables")
        sys.exit(1)
    
    try:
        # Initialize components
        scraper = AgentNewsletterScraper()
        emailer = CloudNewsletterEmailer(gmail_user, gmail_password, database_url)
        
        # Scrape articles
        articles = scraper.scrape_latest_news(max_articles=5)
        if not articles:
            logger.error("No articles found, aborting newsletter")
            sys.exit(1)
        
        # Send newsletter
        success = emailer.send_newsletter(articles)
        
        if success:
            logger.info("Cloud newsletter automation completed successfully")
        else:
            logger.error("Newsletter automation failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in newsletter automation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
