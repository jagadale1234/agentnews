#!/usr/bin/env python3
"""
Cloud-enabled AgentNews with Database Integration
================================================

This enhanced version was born out of necessity - the original CSV-based approach 
worked fine locally, but fell apart when deploying to the cloud. Multiple instances 
trying to write to the same file? Recipe for disaster. So we made the jump to 
proper database management that can handle concurrent users and scale properly.

Why both PostgreSQL and SQLite? Simple - we want developers to be able to 
test locally without needing a full cloud setup, but production deserves 
the robustness of PostgreSQL.
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

# We're being extra careful with imports here - psycopg2 can be finicky to install
# especially on different platforms. Better to gracefully degrade to SQLite
# than crash the whole application.
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("PostgreSQL support not available. Install with: pip install psycopg2-binary")

# I learned the hard way that logging to both file and console is essential
# When things go wrong in production, you need those logs accessible from 
# multiple places. The file persists between runs, console helps with debugging.
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
    """
    The heart of our cloud architecture - handles all database operations
    
    This class was designed with one principle: work everywhere, fail gracefully.
    Whether you're running on your laptop with SQLite or in production with 
    PostgreSQL, the interface stays the same. That's the beauty of abstraction.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        # First, figure out what database we're dealing with
        # Railway, Heroku, and other cloud providers give us this via DATABASE_URL
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.is_postgres = self.database_url and self.database_url.startswith('postgresql')
        
        # Safety check - don't let the app start if we can't handle the database
        if self.is_postgres and not POSTGRES_AVAILABLE:
            raise ImportError("PostgreSQL support required but psycopg2 not installed")
        
        # Get the database ready for action
        self.init_database()
    
    def get_connection(self):
        """
        Get database connection - the universal translator
        
        This method hides the complexity of different database types.
        Your code doesn't need to know if it's talking to PostgreSQL 
        or SQLite - it just asks for a connection and gets one.
        """
        if self.is_postgres:
            # We already checked POSTGRES_AVAILABLE in __init__, so this should be safe
            import psycopg2
            return psycopg2.connect(self.database_url)
        else:
            # SQLite for local development - simple and no setup required
            # Store in current directory so developers can easily find and inspect it
            db_path = 'subscribers.db'
            return sqlite3.connect(db_path)
    
    def init_database(self):
        """
        Set up our database tables - the foundation of everything
        
        I spent way too much time debugging issues caused by missing indexes
        in production. Now I create them upfront. Email lookups need to be fast,
        and filtering by active status happens constantly.
        """
        with self.get_connection() as conn:
            if self.is_postgres:
                cursor = conn.cursor()
                # PostgreSQL syntax with proper data types for production
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
                # These indexes are performance lifesavers when you have thousands of subscribers
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_subscribers_active ON subscribers(is_active);
                """)
            else:
                cursor = conn.cursor()
                # SQLite version - slightly different syntax but same structure
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
                # Same indexes for consistency
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_subscribers_active ON subscribers(is_active);
                """)
            
            conn.commit()
    
    def add_subscriber(self, email: str) -> tuple:
        """
        Add a new subscriber with smart conflict handling
        
        This method does more than just insert - it handles the tricky case where
        someone tries to resubscribe. We treat that as reactivating their account
        rather than creating a duplicate. The return tuple tells us if they're 
        truly new (triggering welcome emails) or just reactivating.
        
        Returns:
            (success: bool, message: str, is_new_subscriber: bool)
        """
        import uuid
        # Generate a unique token for unsubscribe links - security first!
        unsubscribe_token = str(uuid.uuid4())[:32]
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if this email already exists in our system
                # This drives the welcome email logic
                if self.is_postgres:
                    cursor.execute("SELECT is_active FROM subscribers WHERE email = %s", (email,))
                else:
                    cursor.execute("SELECT is_active FROM subscribers WHERE email = ?", (email,))
                
                existing = cursor.fetchone()
                is_new_subscriber = existing is None
                
                # PostgreSQL has better conflict resolution with ON CONFLICT
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
                    # SQLite uses INSERT OR REPLACE - simpler but less precise
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
        """
        Send a warm welcome to new subscribers - first impressions matter!
        
        This was added because I realized we were missing a huge opportunity.
        When someone subscribes, they're excited about AI agents RIGHT NOW.
        Why make them wait until tomorrow for their first newsletter?
        
        We grab fresh articles and send them immediately. If no articles are
        available (rare, but it happens), we send a friendly welcome anyway.
        """
        try:
            # Find the subscriber's data - we need their unsubscribe token
            subscribers = self.db.get_active_subscribers()
            subscriber_data = None
            for sub in subscribers:
                if sub['email'] == subscriber_email:
                    subscriber_data = sub
                    break
            
            if not subscriber_data:
                logger.error(f"Subscriber data not found for {subscriber_email}")
                return False
            
            # Get the freshest articles available - welcome emails deserve the best
            scraper = AgentNewsletterScraper()
            articles = scraper.scrape_latest_news(max_articles=3)  # Three articles feels right - not overwhelming
            
            if not articles:
                # Graceful fallback when scraping fails
                logger.warning("No articles available for welcome email, sending welcome message only")
                articles = [{
                    'title': 'Welcome to AgentNews!',
                    'link': 'https://aiagentsdirectory.com',
                    'summary': 'Stay tuned for the latest AI agent news and updates.'
                }]
            
            # Create the welcome email - different tone than regular newsletters
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
    """
    Multi-source AI agent news scraper
    
    After manually checking dozens of AI agent sites, I found these two give us 
    the best coverage: aiagentsdirectory.com for breaking news and individual 
    tool announcements, and aiagentstore.ai for comprehensive weekly digests 
    and strategic analysis.
    
    The strategy here is diversity - if one source is down or light on content,
    we fall back to the other. Real newsletters need reliable content flow.
    """
    
    def __init__(self):
        # Primary sources - each serves a different content style
        self.sources = {
            'aiagentsdirectory': {
                'base_url': "https://aiagentsdirectory.com",
                'blog_url': "https://aiagentsdirectory.com/blog",
                'selectors': [
                    'a[href*="/blog/"]',
                    '.article-link', 
                    '[data-article]',
                    'article a'
                ]
            },
            'aiagentstore': {
                'base_url': "https://aiagentstore.ai", 
                'blog_url': "https://aiagentstore.ai/ai-agent-news/this-week",
                'selectors': [
                    'h3',  # Section headers like "OpenAI Expands Agent Capabilities"
                    'h2',  # Main digest sections
                    'strong', # Bold headlines within content
                    '.news-item'  # In case they have specific news item classes
                ]
            }
        }
        
        # Configure session with realistic browser headers
        # Some sites block obvious scrapers, so we blend in
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_latest_news(self, max_articles: int = 5) -> List[Dict[str, str]]:
        """
        Scrape from multiple sources for comprehensive coverage
        
        I learned the hard way that relying on a single source is risky.
        Sites go down, change their structure, or just have slow news days.
        This method tries both sources and combines the results, giving us
        the best chance of always having fresh content for our readers.
        """
        all_articles = []
        
        # Try each source - if one fails, we still have the other
        for source_name, source_config in self.sources.items():
            try:
                logger.info(f"Scraping news from {source_name}: {source_config['blog_url']}")
                articles = self._scrape_source(source_name, source_config, max_articles)
                all_articles.extend(articles)
                logger.info(f"Got {len(articles)} articles from {source_name}")
            except Exception as e:
                logger.warning(f"Failed to scrape {source_name}: {e}")
                continue
        
        # Remove duplicates and return the best articles
        # Prioritize by source order (aiagentsdirectory first for recency)
        seen_titles = set()
        unique_articles = []
        
        for article in all_articles:
            # Simple deduplication by title similarity
            title_lower = article['title'].lower()
            if not any(title_lower in seen_title or seen_title in title_lower for seen_title in seen_titles):
                seen_titles.add(title_lower)
                unique_articles.append(article)
                
                if len(unique_articles) >= max_articles:
                    break
        
        logger.info(f"Returning {len(unique_articles)} unique articles from all sources")
        return unique_articles
    
    def _scrape_source(self, source_name: str, config: dict, max_articles: int) -> List[Dict[str, str]]:
        """Scrape articles from a specific source"""
        if source_name == 'aiagentsdirectory':
            return self._scrape_aiagentsdirectory(config, max_articles)
        elif source_name == 'aiagentstore':
            return self._scrape_aiagentstore(config, max_articles)
        else:
            return []
    
    def _scrape_aiagentsdirectory(self, config: dict, max_articles: int) -> List[Dict[str, str]]:
        """Original aiagentsdirectory.com scraping logic"""
        try:
            response = self.session.get(config['blog_url'], timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Try different selectors to find article links
            article_links = []
            for selector in config['selectors']:
                links = soup.select(selector)
                if links:
                    article_links = links
                    break
            
            # Fallback to homepage if blog doesn't work
            if not article_links:
                logger.info("Trying homepage for latest articles section")
                home_response = self.session.get(config['base_url'], timeout=10)
                home_response.raise_for_status()
                home_soup = BeautifulSoup(home_response.content, 'html.parser')
                article_links = home_soup.select('a[href*="/blog/"]')
            
            # Process the links we found
            seen_links = set()
            for link in article_links[:max_articles * 2]:  # Get extra in case some are invalid
                if len(articles) >= max_articles:
                    break
                    
                href = link.get('href', '')
                if not href or href in seen_links:
                    continue
                
                # Handle relative URLs
                if isinstance(href, list):
                    href = href[0] if href else ''
                href = str(href)
                
                if href.startswith('/'):
                    href = config['base_url'] + href
                elif not href.startswith('http'):
                    continue
                
                seen_links.add(href)
                title = link.get_text(strip=True)
                
                if title and len(title) > 10:
                    articles.append({
                        'title': title,
                        'link': href,
                        'summary': title  # Use title as summary for now
                    })
            
            return articles[:max_articles]
            
        except Exception as e:
            logger.error(f"Error scraping aiagentsdirectory: {e}")
            return []
    
    def _scrape_aiagentstore(self, config: dict, max_articles: int) -> List[Dict[str, str]]:
        """
        Scrape the aiagentstore.ai weekly digest
        
        This site has a different structure - it's more of a curated digest
        with sections like "OpenAI Expands Agent Capabilities" and detailed 
        analysis. We extract these section headers and key points as articles.
        """
        try:
            response = self.session.get(config['blog_url'], timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Look for main content sections in the digest
            # Find headers that contain AI agent keywords
            all_headers = soup.find_all(['h2', 'h3'])
            content_sections = []
            
            for header in all_headers:
                text = header.get_text(strip=True)
                if text and any(keyword in text.lower() for keyword in [
                    'openai', 'agent', 'ai', 'aws', 'claude', 'anthropic', 
                    'microsoft', 'google', 'news', 'update', 'launch', 'breakthrough'
                ]):
                    content_sections.append(header)
            
            for section in content_sections[:max_articles]:
                title = section.get_text(strip=True)
                
                # Find the content that follows this heading
                content_elements = []
                next_element = section.find_next_sibling()
                
                # Collect content until we hit another heading or run out
                while next_element and hasattr(next_element, 'name'):
                    if next_element.name and next_element.name not in ['h1', 'h2', 'h3']:
                        if next_element.name == 'p' and next_element.get_text(strip=True):
                            content_elements.append(next_element.get_text(strip=True))
                        elif next_element.name == 'ul' and hasattr(next_element, 'find_all'):
                            # Handle bullet points
                            for li in next_element.find_all('li'):
                                content_elements.append(f"• {li.get_text(strip=True)}")
                        next_element = next_element.find_next_sibling()
                        
                        # Don't go too far down the page
                        if len(content_elements) > 5:
                            break
                    else:
                        break
                
                # Create summary from first few content elements
                summary = ' '.join(content_elements[:2]) if content_elements else title
                # Limit summary length for email formatting
                if len(summary) > 200:
                    summary = summary[:200] + "..."
                
                articles.append({
                    'title': title,
                    'link': config['blog_url'],  # Link back to the full digest
                    'summary': summary
                })
            
            # If we didn't find section headers, try looking for other patterns
            if not articles:
                # Look for any strong/bold text that might be news items
                strong_elements = soup.find_all('strong')
                for element in strong_elements[:max_articles]:
                    text = element.get_text(strip=True)
                    if len(text) > 20 and any(keyword in text.lower() for keyword in ['ai', 'agent', 'openai', 'aws']):
                        # Get surrounding context
                        parent = element.parent
                        context = parent.get_text(strip=True) if parent else text
                        summary = context[:200] + "..." if len(context) > 200 else context
                        
                        articles.append({
                            'title': text,
                            'link': config['blog_url'],
                            'summary': summary
                        })
            
            return articles[:max_articles]
            
        except Exception as e:
            logger.error(f"Error scraping aiagentstore: {e}")
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
