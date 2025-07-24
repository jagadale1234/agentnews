#!/usr/bin/env python3
"""
Unsubscribe Handler for AgentNews
=================================

A utility script to handle unsubscribe requests from newsletter subscribers.
Can be run manually or automated to check Gmail for unsubscribe requests.
"""

import os
import sys
import logging
import re
import time
from agent_news import NewsletterEmailer, load_env_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unsubscribe.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def manual_unsubscribe(email_address: str) -> bool:
    """
    Manually unsubscribe an email address
    
    Args:
        email_address: The email address to unsubscribe
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load environment variables
        load_env_file()
        
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not gmail_user or not gmail_password:
            logger.error("Gmail credentials not found")
            return False
        
        emailer = NewsletterEmailer(gmail_user, gmail_password)
        success = emailer.remove_subscriber(email_address)
        
        if success:
            logger.info(f"Successfully unsubscribed {email_address}")
            return True
        else:
            logger.error(f"Failed to unsubscribe {email_address}")
            return False
            
    except Exception as e:
        logger.error(f"Error during manual unsubscribe: {e}")
        return False


def manual_subscribe(email_address: str) -> bool:
    """
    Manually subscribe an email address
    
    Args:
        email_address: The email address to subscribe
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load environment variables
        load_env_file()
        
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not gmail_user or not gmail_password:
            logger.error("Gmail credentials not found")
            return False
        
        emailer = NewsletterEmailer(gmail_user, gmail_password)
        success = emailer.add_subscriber(email_address)
        
        if success:
            logger.info(f"Successfully subscribed {email_address}")
            return True
        else:
            logger.error(f"Failed to subscribe {email_address}")
            return False
            
    except Exception as e:
        logger.error(f"Error during manual subscribe: {e}")
        return False


def list_subscribers() -> bool:
    """
    List all current subscribers
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load environment variables
        load_env_file()
        
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not gmail_user or not gmail_password:
            logger.error("Gmail credentials not found")
            return False
        
        emailer = NewsletterEmailer(gmail_user, gmail_password)
        subscribers = emailer.read_subscribers()
        
        print(f"\nCurrent Subscribers ({len(subscribers)}):")
        print("=" * 40)
        for i, email in enumerate(subscribers, 1):
            print(f"{i:3d}. {email}")
        print()
        
        return True
        
    except Exception as e:
        logger.error(f"Error listing subscribers: {e}")
        return False


def process_unsubscribe_requests():
    """
    Check Gmail for unsubscribe requests and process them automatically
    Note: This requires additional email processing libraries
    """
    logger.info("Automatic email processing not implemented yet")
    logger.info("For now, manually process unsubscribe requests using this script")
    logger.info("Example: python unsubscribe_handler.py unsubscribe user@example.com")


def main():
    """Main function for command line interface"""
    if len(sys.argv) < 2:
        print("AgentNews Unsubscribe Handler")
        print("=" * 40)
        print("\nUsage:")
        print("  python unsubscribe_handler.py unsubscribe <email>")
        print("  python unsubscribe_handler.py subscribe <email>")
        print("  python unsubscribe_handler.py list")
        print("  python unsubscribe_handler.py process")
        print("\nExamples:")
        print("  python unsubscribe_handler.py unsubscribe user@example.com")
        print("  python unsubscribe_handler.py subscribe newuser@example.com")
        print("  python unsubscribe_handler.py list")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "unsubscribe":
        if len(sys.argv) < 3:
            print("Error: Email address required for unsubscribe")
            print("Usage: python unsubscribe_handler.py unsubscribe <email>")
            sys.exit(1)
        
        email = sys.argv[2]
        success = manual_unsubscribe(email)
        sys.exit(0 if success else 1)
    
    elif command == "subscribe":
        if len(sys.argv) < 3:
            print("Error: Email address required for subscribe")
            print("Usage: python unsubscribe_handler.py subscribe <email>")
            sys.exit(1)
        
        email = sys.argv[2]
        success = manual_subscribe(email)
        sys.exit(0 if success else 1)
    
    elif command == "list":
        success = list_subscribers()
        sys.exit(0 if success else 1)
    
    elif command == "process":
        process_unsubscribe_requests()
        sys.exit(0)
    
    else:
        print(f"Error: Unknown command '{command}'")
        print("Valid commands: unsubscribe, subscribe, list, process")
        sys.exit(1)


if __name__ == "__main__":
    main()
