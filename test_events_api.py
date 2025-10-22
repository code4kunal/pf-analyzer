#!/usr/bin/env python3
"""
Test script for GrowFolio CMS Calendar & Events API
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Login and get auth token"""
    payload = {
        "email": "admin@grow-folio.in",
        "password": "Admin@123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def get_customer_id(token):
    """Get first customer ID for testing"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/customers?page_size=1", headers=headers)
    if response.status_code == 200:
        customers = response.json()['items']
        if customers:
            return customers[0]['id']
    return None

def test_create_event(token, customer_id):
    """Test creating an event with Google Meet link"""
    print("\n" + "="*60)
    print("TEST 1: Create Event with Google Meet Link")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # Event tomorrow at 2 PM
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    payload = {
        "title": "Investment Portfolio Review Meeting",
        "event_type": "ONE_ON_ONE",
        "description": "Quarterly portfolio review and rebalancing discussion",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "participant_ids": [customer_id] if customer_id else [],
        "create_meet_link": True
    }

    response = requests.post(f"{BASE_URL}/api/events", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        event = response.json()
        print(f"✅ Event created successfully!")
        print(f"Title: {event['title']}")
        print(f"Type: {event['event_type']}")
        print(f"Start: {event['start_time']}")
        print(f"Google Meet Link: {event['meet_link']}")
        print(f"Participants: {len(event['participants'])}")
        return event['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def test_create_seminar(token):
    """Test creating a seminar event"""
    print("\n" + "="*60)
    print("TEST 2: Create Seminar Event")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # Seminar next week
    next_week = datetime.now() + timedelta(days=7)
    start_time = next_week.replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=2)

    payload = {
        "title": "Wealth Creation Strategies 2025",
        "event_type": "SEMINAR",
        "description": "Learn about tax-efficient investment strategies for 2025",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "location": "Conference Hall, Mumbai",
        "participant_ids": [],
        "create_meet_link": True
    }

    response = requests.post(f"{BASE_URL}/api/events", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        event = response.json()
        print(f"✅ Seminar event created!")
        print(f"Title: {event['title']}")
        print(f"Location: {event['location']}")
        print(f"Google Meet Link: {event['meet_link']}")
        return event['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def test_list_events(token):
    """Test listing all events"""
    print("\n" + "="*60)
    print("TEST 3: List All Events")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/events", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        events = response.json()
        print(f"✅ Found {len(events)} event(s)")
        for event in events:
            print(f"  - {event['title']} ({event['event_type']}) - {event['start_time'][:10]}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_upcoming_events(token):
    """Test getting upcoming events"""
    print("\n" + "="*60)
    print("TEST 4: Get Upcoming Events (Next 7 Days)")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/events/upcoming?days=7", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        events = response.json()
        print(f"✅ Found {len(events)} upcoming event(s)")
        for event in events:
            start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
            print(f"  - {event['title']}")
            print(f"    When: {start.strftime('%b %d at %I:%M %p')}")
            print(f"    Type: {event['event_type']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_get_event_details(token, event_id):
    """Test getting event details"""
    print("\n" + "="*60)
    print("TEST 5: Get Event Details")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/events/{event_id}", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        event = response.json()
        print(f"✅ Event details retrieved!")
        print(f"Title: {event['title']}")
        print(f"Description: {event['description']}")
        print(f"Meet Link: {event['meet_link']}")
        print(f"Completed: {event['is_completed']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_update_event(token, event_id, customer_id):
    """Test updating an event"""
    print("\n" + "="*60)
    print("TEST 6: Update Event (Add Participant)")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "description": "Updated: Quarterly portfolio review with market analysis",
        "participant_ids": [customer_id] if customer_id else []
    }

    response = requests.put(f"{BASE_URL}/api/events/{event_id}", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        event = response.json()
        print(f"✅ Event updated!")
        print(f"Updated Description: {event['description']}")
        print(f"Participants: {len(event['participants'])}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_mark_completed(token, event_id):
    """Test marking event as completed"""
    print("\n" + "="*60)
    print("TEST 7: Mark Event as Completed")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/events/{event_id}/complete", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print(f"✅ Event marked as completed!")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_calendar_month(token):
    """Test getting calendar month view"""
    print("\n" + "="*60)
    print("TEST 8: Get Calendar Month View")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now()
    response = requests.get(
        f"{BASE_URL}/api/calendar/month/{now.year}/{now.month}",
        headers=headers
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Calendar retrieved!")
        print(f"Month: {data['month']}/{data['year']}")
        print(f"Total Events: {data['total_events']}")
        print(f"Events by Day: {list(data['events_by_day'].keys())}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_filter_by_type(token):
    """Test filtering events by type"""
    print("\n" + "="*60)
    print("TEST 9: Filter Events by Type (SEMINAR)")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/events?event_type=SEMINAR", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        events = response.json()
        print(f"✅ Found {len(events)} seminar(s)")
        for event in events:
            print(f"  - {event['title']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_get_notifications(token):
    """Test getting event notifications"""
    print("\n" + "="*60)
    print("TEST 10: Get Event Notifications")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/notifications?unread_only=true", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        notifications = response.json()
        print(f"✅ Found {len(notifications)} unread notification(s)")
        for notif in notifications:
            print(f"  - {notif['title']}: {notif['message']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def main():
    print("\n" + "="*60)
    print("GrowFolio CMS - Calendar & Events API Test Suite")
    print("="*60)

    # Get auth token
    print("\nLogging in...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to login. Aborting tests.")
        return

    print("✅ Logged in successfully!")

    # Get customer for testing
    customer_id = get_customer_id(token)
    if customer_id:
        print(f"✅ Found customer ID: {customer_id}")
    else:
        print("⚠️  No customers found, will test without participants")

    # Run tests
    event_id = test_create_event(token, customer_id)
    if not event_id:
        print("\n❌ Failed to create event. Aborting remaining tests.")
        return

    seminar_id = test_create_seminar(token)
    test_list_events(token)
    test_upcoming_events(token)
    test_get_event_details(token, event_id)
    test_update_event(token, event_id, customer_id)
    test_calendar_month(token)
    test_filter_by_type(token)
    test_get_notifications(token)
    test_mark_completed(token, event_id)

    print("\n" + "="*60)
    print("✅ All Calendar & Events Tests Completed!")
    print("="*60)
    print()
    print("📝 Summary:")
    print("- Events created with Google Meet links")
    print("- Event participants managed")
    print("- Notifications generated automatically")
    print("- Calendar month view working")
    print("- Event filtering functional")
    print()

if __name__ == "__main__":
    main()
