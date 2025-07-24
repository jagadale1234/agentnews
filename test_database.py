#!/usr/bin/env python3
"""
Test script for AgentNews Cloud Database
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_news_cloud import DatabaseManager, load_env_file

def test_database_connection():
    """Test database connection and basic operations"""
    print("🔍 Testing AgentNews Cloud Database Connection")
    print("=" * 50)
    
    # Load environment variables
    load_env_file()
    
    try:
        # Initialize database
        print("📊 Initializing database connection...")
        db = DatabaseManager()
        print(f"✅ Database connected successfully!")
        print(f"   Database type: {'PostgreSQL' if db.is_postgres else 'SQLite'}")
        
        # Test subscriber count
        print("\n📈 Getting subscriber count...")
        count = db.get_subscriber_count()
        print(f"   Current subscribers: {count}")
        
        # Test adding a subscriber
        print("\n➕ Testing add subscriber...")
        test_email = "test@example.com"
        success, message = db.add_subscriber(test_email)
        print(f"   Add result: {'✅' if success else '❌'} {message}")
        
        # Test getting subscribers
        print("\n📋 Getting all active subscribers...")
        subscribers = db.get_active_subscribers()
        print(f"   Found {len(subscribers)} active subscribers:")
        for sub in subscribers:
            print(f"     - {sub['email']} (token: {sub['unsubscribe_token'][:8]}...)")
        
        # Test removing the test subscriber
        print(f"\n➖ Testing remove subscriber ({test_email})...")
        success, message = db.remove_subscriber(test_email)
        print(f"   Remove result: {'✅' if success else '❌'} {message}")
        
        # Final count
        final_count = db.get_subscriber_count()
        print(f"\n📊 Final subscriber count: {final_count}")
        
        print("\n🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def add_real_subscriber():
    """Add your real email as a subscriber"""
    print("\n" + "=" * 50)
    print("➕ Add Real Subscriber")
    print("=" * 50)
    
    load_env_file()
    
    try:
        db = DatabaseManager()
        
        # Add your email
        your_email = "jagadaleanish@gmail.com"
        success, message = db.add_subscriber(your_email)
        print(f"Adding {your_email}: {'✅' if success else '❌'} {message}")
        
        # Show all subscribers
        subscribers = db.get_active_subscribers()
        print(f"\nActive subscribers ({len(subscribers)}):")
        for sub in subscribers:
            print(f"  📧 {sub['email']}")
            print(f"     🔗 Unsubscribe token: {sub['unsubscribe_token']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding subscriber: {e}")
        return False

def main():
    """Main test function"""
    print("🤖 AgentNews Cloud Database Test")
    print("=" * 50)
    
    # Test database connection
    if not test_database_connection():
        print("\n❌ Database tests failed. Check your DATABASE_URL.")
        return
    
    # Add real subscriber
    response = input("\n➕ Do you want to add your email as a real subscriber? (y/N): ").strip().lower()
    if response == 'y':
        add_real_subscriber()
    
    print("\n✅ Database testing completed!")
    print("\nNext steps:")
    print("1. Run 'python web_interface.py' to test the web interface")
    print("2. Run 'python agent_news_cloud.py' to send a test newsletter")
    print("3. Set up GitHub Actions for automated newsletters")

if __name__ == "__main__":
    main()
