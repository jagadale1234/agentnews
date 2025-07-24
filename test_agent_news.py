#!/usr/bin/env python3
"""
Test script for AgentNews newsletter functionality
"""

import sys
import os
from agent_news import AgentNewsletterScraper, NewsletterEmailer

def test_scraping():
    """Test the web scraping functionality"""
    print("Testing web scraping...")
    
    scraper = AgentNewsletterScraper()
    articles = scraper.scrape_latest_news(max_articles=3)
    
    print(f"Found {len(articles)} articles:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        print(f"   Link: {article['link']}")
        print(f"   Summary: {article['summary'][:100]}...")
        print()

def test_email_formatting():
    """Test email formatting without sending"""
    print("Testing email formatting...")
    
    # Sample articles for testing
    sample_articles = [
        {
            'title': 'Test Article 1: AI Breakthrough',
            'link': 'https://example.com/article1',
            'summary': 'This is a test summary of the first article.'
        },
        {
            'title': 'Test Article 2: New AI Agent Platform',
            'link': 'https://example.com/article2',
            'summary': 'This is a test summary of the second article.'
        }
    ]
    
    emailer = NewsletterEmailer("test@example.com", "dummy_password")
    
    # Test without subscriber email (generic unsubscribe)
    formatted_email = emailer.format_newsletter(sample_articles)
    print("Formatted newsletter (generic):")
    print("-" * 50)
    print(formatted_email)
    print("-" * 50)
    
    # Test with subscriber email (personalized unsubscribe)
    formatted_email_personal = emailer.format_newsletter(sample_articles, "subscriber@example.com")
    print("\nFormatted newsletter (personalized):")
    print("-" * 50)
    print(formatted_email_personal)
    print("-" * 50)

def test_subscriber_management():
    """Test subscriber management functions"""
    print("Testing subscriber management...")
    
    emailer = NewsletterEmailer("test@example.com", "dummy_password")
    test_csv = "test_subscribers.csv"
    
    # Clean up any existing test file
    if os.path.exists(test_csv):
        os.remove(test_csv)
    
    # Test adding subscribers
    print("Testing add_subscriber...")
    success1 = emailer.add_subscriber("test1@example.com", test_csv)
    success2 = emailer.add_subscriber("test2@example.com", test_csv)
    success3 = emailer.add_subscriber("invalid-email", test_csv)  # Should fail
    
    print(f"  Add test1@example.com: {'✓' if success1 else '✗'}")
    print(f"  Add test2@example.com: {'✓' if success2 else '✗'}")
    print(f"  Add invalid-email: {'✗' if not success3 else '✓'} (should fail)")
    
    # Test reading subscribers
    print("\nTesting read_subscribers...")
    subscribers = emailer.read_subscribers(test_csv)
    print(f"  Found {len(subscribers)} subscribers: {subscribers}")
    
    # Test removing subscribers
    print("\nTesting remove_subscriber...")
    remove_success1 = emailer.remove_subscriber("test1@example.com", test_csv)
    remove_success2 = emailer.remove_subscriber("nonexistent@example.com", test_csv)  # Should fail
    
    print(f"  Remove test1@example.com: {'✓' if remove_success1 else '✗'}")
    print(f"  Remove nonexistent@example.com: {'✗' if not remove_success2 else '✓'} (should fail)")
    
    # Test final state
    final_subscribers = emailer.read_subscribers(test_csv)
    print(f"  Final subscribers: {final_subscribers}")
    
    # Clean up
    if os.path.exists(test_csv):
        os.remove(test_csv)
        print("  Test file cleaned up")

def test_subscriber_reading():
    """Test reading subscribers from CSV"""
    print("Testing subscriber reading...")
    
    emailer = NewsletterEmailer("test@example.com", "dummy_password")
    subscribers = emailer.read_subscribers()
    
    print(f"Found {len(subscribers)} subscribers:")
    for email in subscribers:
        print(f"  - {email}")

def main():
    """Run all tests"""
    print("AgentNews Test Suite")
    print("=" * 50)
    
    test_scraping()
    print()
    
    test_email_formatting()
    print()
    
    test_subscriber_reading()
    print()
    
    test_subscriber_management()
    print()
    
    print("All tests completed!")
    print("\nTo run the actual newsletter, set environment variables and run:")
    print("python agent_news.py")
    print("\nTo manage subscribers manually, use:")
    print("python unsubscribe_handler.py")

if __name__ == "__main__":
    main()
