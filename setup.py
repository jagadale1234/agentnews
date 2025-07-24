#!/usr/bin/env python3
"""
Setup script for AgentNews
Helps configure Gmail credentials and test the setup
"""

import os
import getpass

def setup_gmail_credentials():
    """Interactive setup for Gmail credentials"""
    print("AgentNews Setup")
    print("=" * 50)
    print("\nTo use AgentNews, you need a Gmail account with an App Password.")
    print("Here's how to set it up:")
    print("\n1. Go to your Google Account settings")
    print("2. Enable 2-factor authentication if not already enabled")
    print("3. Go to Security > App passwords")
    print("4. Generate an App Password for 'Mail'")
    print("5. Use that 16-character password below (not your regular password)")
    
    print("\n" + "-" * 50)
    
    gmail_user = input("Enter your Gmail address: ").strip()
    gmail_password = getpass.getpass("Enter your Gmail App Password: ").strip()
    
    # Create .env file
    env_content = f"""# AgentNews Environment Variables
GMAIL_USER={gmail_user}
GMAIL_APP_PASSWORD={gmail_password}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\nCredentials saved to .env file")
    print("Keep this file secure and don't commit it to version control!")
    
    return gmail_user, gmail_password

def test_setup():
    """Test if everything is working"""
    print("\n" + "=" * 50)
    print("Testing setup...")
    
    try:
        from agent_news import AgentNewsletterScraper, NewsletterEmailer
        
        # Test scraping
        print("Testing web scraping...")
        scraper = AgentNewsletterScraper()
        articles = scraper.scrape_latest_news(max_articles=2)
        print(f"   Found {len(articles)} articles")
        
        # Test email formatting (without sending)
        print("Testing email formatting...")
        emailer = NewsletterEmailer("test@example.com", "dummy_password")
        formatted_email = emailer.format_newsletter(articles)
        print("   Email formatted successfully")
        
        # Test subscriber reading
        print("Testing subscriber reading...")
        subscribers = emailer.read_subscribers()
        print(f"   Found {len(subscribers)} subscribers in CSV")
        
        print("\nAll tests passed! AgentNews is ready to use.")
        print("\nTo send the newsletter, run: python agent_news.py")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        print("Please check your setup and try again.")

def main():
    print("Welcome to AgentNews Setup!")
    print("\nThis script will help you configure AgentNews for the first time.")
    
    # Check if .env already exists
    if os.path.exists('.env'):
        response = input("\n.env file already exists. Recreate it? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping credential setup...")
        else:
            setup_gmail_credentials()
    else:
        setup_gmail_credentials()
    
    # Test the setup
    test_setup()
    
    print("\n" + "=" * 50)
    print("Setup complete! Next steps:")
    print("1. Edit subscribers.csv to add your actual subscribers")
    print("2. Run: python agent_news.py")
    print("3. Set up a cron job for automation (see README.md)")

if __name__ == "__main__":
    main()
