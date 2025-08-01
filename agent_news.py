#!/usr/bin/env python3
"""
AgentNews - Automated AI News Newsletter
=========================================

A simple script that scrapes AI agent news from aiagentsdirectory.com,
formats a newsletter, and sends it to subscribers via email.

Requirements:
- Gmail account with App Password for yagmail
- subscribers.csv file with email addresses
- Environment variables for email credentials
"""

import os
import csv
import sys
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import requests
from bs4 import BeautifulSoup
import yagmail

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


class AgentNewsletterScraper:
    """Scrapes AI agent news from aiagentsdirectory.com"""
    
    def __init__(self):
        self.base_url = "https://aiagentsdirectory.com"
        self.blog_url = f"{self.base_url}/blog"
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_latest_news(self, max_articles: int = 5) -> List[Dict[str, str]]:
        """
        Scrape the latest AI agent news articles
        
        Args:
            max_articles: Maximum number of articles to return
            
        Returns:
            List of dictionaries with 'title', 'link', and 'summary' keys
        """
        try:
            logger.info(f"Scraping news from {self.blog_url}")
            response = self.session.get(self.blog_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Look for article links - adjust selectors based on the actual HTML structure
            # Try multiple selectors to be more robust
            article_selectors = [
                'a[href*="/blog/"]',  # Generic blog links
                '.article-link',      # Common class name
                '[data-article]',     # Data attribute
                'article a',          # Article tag links
            ]
            
            article_links = []
            for selector in article_selectors:
                links = soup.select(selector)
                if links:
                    article_links = links
                    break
            
            # If no specific selectors work, try the homepage approach
            if not article_links:
                logger.info("Trying homepage for latest articles section")
                home_response = self.session.get(self.base_url, timeout=10)
                home_response.raise_for_status()
                home_soup = BeautifulSoup(home_response.content, 'html.parser')
                
                # Look for the "Latest Articles" section we saw in the webpage content
                article_links = home_soup.select('a[href*="/blog/"]')
            
            logger.info(f"Found {len(article_links)} potential article links")
            
            # Process the found links
            seen_links = set()
            for link in article_links[:max_articles * 2]:  # Get extra in case of duplicates
                if len(articles) >= max_articles:
                    break
                    
                href = link.get('href', '')
                if not href or href in seen_links:
                    continue
                
                # Make sure it's a full URL
                if href.startswith('/'):
                    href = self.base_url + href
                elif not href.startswith('http'):
                    continue
                
                seen_links.add(href)
                title = link.get_text(strip=True)
                
                if title and len(title) > 10:  # Filter out very short titles
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


class NewsletterEmailer:
    """Handles email composition and sending"""
    
    def __init__(self, gmail_user: str, gmail_password: str):
        self.gmail_user = gmail_user
        self.gmail_password = gmail_password
    
    def format_newsletter(self, articles: List[Dict[str, str]], subscriber_email: Optional[str] = None) -> str:
        """
        Format articles into a newsletter email body
        
        Args:
            articles: List of article dictionaries
            subscriber_email: Email address of the subscriber (for unsubscribe link)
            
        Returns:
            Formatted email body as string
        """
        current_date = datetime.now().strftime("%B %d, %Y")
        
        email_body = f"""AgentNews Weekly - {current_date}
{'=' * 50}

Welcome to this week's AgentNews! Here are the top AI agent stories:

"""
        
        for i, article in enumerate(articles, 1):
            email_body += f"{i}. {article['title']}\n"
            email_body += f"   Link: {article['link']}\n"
            email_body += f"   Summary: {article['summary']}\n\n"
        
        # Add unsubscribe instructions
        unsubscribe_text = ""
        if subscriber_email:
            unsubscribe_text = f"""
To unsubscribe: Reply with "UNSUBSCRIBE" or send an email to {self.gmail_user} with subject "UNSUBSCRIBE {subscriber_email}"
"""
        else:
            unsubscribe_text = "\nTo unsubscribe: Reply with \"UNSUBSCRIBE\""
        
        email_body += f"""
==================================================

Thanks for reading AgentNews! Stay ahead of the AI agent revolution.
{unsubscribe_text}
Best regards,
The AgentNews Team
"""
        
        return email_body
    
    def read_subscribers(self, csv_file: str = 'subscribers.csv') -> List[str]:
        """
        Read subscriber email addresses from CSV file
        
        Args:
            csv_file: Path to CSV file with email addresses
            
        Returns:
            List of email addresses
        """
        subscribers = []
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if row and row[0].strip():  # Skip empty rows
                        email = row[0].strip()
                        if '@' in email:  # Basic email validation
                            subscribers.append(email)
            
            logger.info(f"Loaded {len(subscribers)} subscribers from {csv_file}")
            return subscribers
            
        except FileNotFoundError:
            logger.error(f"Subscribers file {csv_file} not found")
            return []
        except Exception as e:
            logger.error(f"Error reading subscribers: {e}")
            return []
    
    def remove_subscriber(self, email_to_remove: str, csv_file: str = 'subscribers.csv') -> bool:
        """
        Remove a subscriber from the CSV file
        
        Args:
            email_to_remove: Email address to remove
            csv_file: Path to CSV file with email addresses
            
        Returns:
            True if successfully removed, False otherwise
        """
        try:
            # Read all current subscribers
            subscribers = self.read_subscribers(csv_file)
            
            # Check if email exists
            if email_to_remove not in subscribers:
                logger.warning(f"Email {email_to_remove} not found in subscribers list")
                return False
            
            # Remove the email
            subscribers.remove(email_to_remove)
            
            # Write back to file
            with open(csv_file, 'w', newline='', encoding='utf-8') as file:
                csv_writer = csv.writer(file)
                for email in subscribers:
                    csv_writer.writerow([email])
            
            logger.info(f"Successfully removed {email_to_remove} from subscribers")
            return True
            
        except Exception as e:
            logger.error(f"Error removing subscriber {email_to_remove}: {e}")
            return False
    
    def add_subscriber(self, email_to_add: str, csv_file: str = 'subscribers.csv') -> bool:
        """
        Add a new subscriber to the CSV file
        
        Args:
            email_to_add: Email address to add
            csv_file: Path to CSV file with email addresses
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            # Basic email validation
            if '@' not in email_to_add or '.' not in email_to_add:
                logger.error(f"Invalid email format: {email_to_add}")
                return False
            
            # Read current subscribers to check for duplicates
            subscribers = self.read_subscribers(csv_file)
            
            if email_to_add in subscribers:
                logger.warning(f"Email {email_to_add} already exists in subscribers list")
                return False
            
            # Add the new email
            with open(csv_file, 'a', newline='', encoding='utf-8') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow([email_to_add])
            
            logger.info(f"Successfully added {email_to_add} to subscribers")
            return True
            
        except Exception as e:
            logger.error(f"Error adding subscriber {email_to_add}: {e}")
            return False
    
    def send_newsletter(self, articles: List[Dict[str, str]], subscribers: List[str]) -> bool:
        """
        Send newsletter to all subscribers
        
        Args:
            articles: List of article dictionaries
            subscribers: List of subscriber email addresses
            
        Returns:
            True if successful, False otherwise
        """
        if not articles:
            logger.error("No articles to send")
            return False
        
        if not subscribers:
            logger.error("No subscribers to send to")
            return False
        
        try:
            # Create yagmail instance
            yag = yagmail.SMTP(self.gmail_user, self.gmail_password)
            
            subject = "AgentNews Weekly"
            logger.info(f"Sending newsletter to {len(subscribers)} subscribers")
            
            # Send to each subscriber individually (for personalized unsubscribe links)
            for subscriber in subscribers:
                try:
                    # Format newsletter with personalized unsubscribe link
                    email_body = self.format_newsletter(articles, subscriber)
                    
                    yag.send(
                        to=subscriber,
                        subject=subject,
                        contents=email_body
                    )
                    logger.info(f"Newsletter sent to {subscriber}")
                    
                except Exception as e:
                    logger.error(f"Failed to send newsletter to {subscriber}: {e}")
                    continue
            
            logger.info("Newsletter sending completed!")
            return True
            
        except Exception as e:
            logger.error(f"Error sending newsletter: {e}")
            return False


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
    """Main function to run the newsletter automation"""
    logger.info("Starting AgentNews newsletter automation")
    
    # Load environment variables from .env file
    load_env_file()
    
    # Get email credentials from environment variables
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')  # Use App Password, not regular password
    
    if not gmail_user or not gmail_password:
        logger.error("Gmail credentials not found in environment variables")
        logger.error("Please set GMAIL_USER and GMAIL_APP_PASSWORD environment variables")
        sys.exit(1)
    
    # Initialize scraper and emailer
    scraper = AgentNewsletterScraper()
    emailer = NewsletterEmailer(gmail_user, gmail_password)
    
    # Scrape latest news
    articles = scraper.scrape_latest_news(max_articles=5)
    
    if not articles:
        logger.error("No articles found, aborting newsletter")
        sys.exit(1)
    
    # Read subscribers
    subscribers = emailer.read_subscribers()
    
    if not subscribers:
        logger.error("No subscribers found, aborting newsletter")
        sys.exit(1)
    
    # Send newsletter
    success = emailer.send_newsletter(articles, subscribers)
    
    if success:
        logger.info("Newsletter automation completed successfully")
    else:
        logger.error("Newsletter automation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
