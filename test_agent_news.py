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
    formatted_email = emailer.format_newsletter(sample_articles)
    
    print("Formatted newsletter:")
    print("-" * 50)
    print(formatted_email)
    print("-" * 50)

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
    
    print("All tests completed!")
    print("\nTo run the actual newsletter, set environment variables and run:")
    print("python agent_news.py")

if __name__ == "__main__":
    main()
