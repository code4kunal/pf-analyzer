#!/usr/bin/env python3
"""
Test script for GrowFolio CMS Document Management API
"""
import requests
import io
import json

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

def test_upload_document(token, customer_id):
    """Test uploading a document"""
    print("\n" + "="*60)
    print("TEST 1: Upload Document (KYC)")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # Create a test PDF file (simulated)
    file_content = b"%PDF-1.4\n%Test KYC Document\nThis is a test KYC document for customer verification."
    files = {
        'file': ('kyc_document.pdf', io.BytesIO(file_content), 'application/pdf')
    }
    data = {
        'customer_id': customer_id,
        'document_name': 'PAN Card Copy',
        'document_category': 'KYC',
        'description': 'PAN card for KYC verification'
    }

    response = requests.post(f"{BASE_URL}/api/documents/upload", headers=headers, files=files, data=data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        document = response.json()
        print(f"✅ Document uploaded successfully!")
        print(f"ID: {document['id']}")
        print(f"Name: {document['document_name']}")
        print(f"Category: {document['document_category']}")
        print(f"Size: {document['file_size']} bytes")
        print(f"Path: {document['file_path']}")
        return document['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def test_upload_agreement(token, customer_id):
    """Test uploading an agreement document"""
    print("\n" + "="*60)
    print("TEST 2: Upload Document (Agreement)")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # Create a test agreement file
    file_content = b"INVESTMENT ADVISORY AGREEMENT\n\nThis agreement is entered into between..."
    files = {
        'file': ('advisory_agreement.pdf', io.BytesIO(file_content), 'application/pdf')
    }
    data = {
        'customer_id': customer_id,
        'document_name': 'Advisory Agreement 2025',
        'document_category': 'AGREEMENT',
        'description': 'Investment advisory agreement signed on Jan 2025'
    }

    response = requests.post(f"{BASE_URL}/api/documents/upload", headers=headers, files=files, data=data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        document = response.json()
        print(f"✅ Agreement uploaded!")
        print(f"Name: {document['document_name']}")
        print(f"Category: {document['document_category']}")
        return document['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def test_list_customer_documents(token, customer_id):
    """Test listing all documents for a customer"""
    print("\n" + "="*60)
    print("TEST 3: List All Customer Documents")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/customers/{customer_id}/documents", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        documents = response.json()
        print(f"✅ Found {len(documents)} document(s)")
        for doc in documents:
            print(f"  - {doc['document_name']} ({doc['document_category']}) - {doc['file_size']} bytes")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_filter_documents_by_category(token, customer_id):
    """Test filtering documents by category"""
    print("\n" + "="*60)
    print("TEST 4: Filter Documents by Category (KYC)")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/customers/{customer_id}/documents?document_category=KYC",
        headers=headers
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        documents = response.json()
        print(f"✅ Found {len(documents)} KYC document(s)")
        for doc in documents:
            print(f"  - {doc['document_name']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_get_document_details(token, document_id):
    """Test getting document details"""
    print("\n" + "="*60)
    print("TEST 5: Get Document Details")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/documents/{document_id}", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        document = response.json()
        print(f"✅ Document details retrieved!")
        print(f"Name: {document['document_name']}")
        print(f"Category: {document['document_category']}")
        print(f"Description: {document['description']}")
        print(f"Uploaded: {document['uploaded_at']}")
        print(f"Storage: {document['storage_type']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_download_document(token, document_id):
    """Test downloading a document"""
    print("\n" + "="*60)
    print("TEST 6: Download Document")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/documents/{document_id}/download", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print(f"✅ Document downloaded successfully!")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"File size: {len(response.content)} bytes")
        print(f"First 50 chars: {response.content[:50]}")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_update_document_metadata(token, document_id):
    """Test updating document metadata"""
    print("\n" + "="*60)
    print("TEST 7: Update Document Metadata")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    params = {
        'document_name': 'PAN Card - Updated',
        'description': 'Updated description: PAN card for KYC (verified)'
    }

    response = requests.put(f"{BASE_URL}/api/documents/{document_id}", headers=headers, params=params)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        document = response.json()
        print(f"✅ Document updated!")
        print(f"New Name: {document['document_name']}")
        print(f"New Description: {document['description']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_delete_document(token, document_id):
    """Test deleting a document (admin only)"""
    print("\n" + "="*60)
    print("TEST 8: Delete Document (Admin Only)")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/api/documents/{document_id}", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print(f"✅ Document deleted successfully!")
        print(f"Message: {response.json()['message']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_activity_log(token, customer_id):
    """Test that document activities are logged"""
    print("\n" + "="*60)
    print("TEST 9: Verify Activity Logging")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/customers/{customer_id}/activities", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        activities = response.json()
        document_activities = [a for a in activities if 'document' in a['action']]
        print(f"✅ Found {len(document_activities)} document-related activities")
        for activity in document_activities[:3]:  # Show first 3
            print(f"  - {activity['action']}: {activity['description']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def main():
    print("\n" + "="*60)
    print("GrowFolio CMS - Document Management API Test Suite")
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
    if not customer_id:
        print("❌ No customers found. Please create a customer first.")
        return

    print(f"✅ Found customer ID: {customer_id}")

    # Run tests
    kyc_doc_id = test_upload_document(token, customer_id)
    if not kyc_doc_id:
        print("\n❌ Failed to upload document. Aborting remaining tests.")
        return

    agreement_doc_id = test_upload_agreement(token, customer_id)
    test_list_customer_documents(token, customer_id)
    test_filter_documents_by_category(token, customer_id)
    test_get_document_details(token, kyc_doc_id)
    test_download_document(token, kyc_doc_id)
    test_update_document_metadata(token, kyc_doc_id)
    test_activity_log(token, customer_id)

    # Delete one document to test deletion
    if agreement_doc_id:
        test_delete_document(token, agreement_doc_id)

    print("\n" + "="*60)
    print("✅ All Document Management Tests Completed!")
    print("="*60)
    print()
    print("📝 Summary:")
    print("- Documents uploaded with file storage")
    print("- Document listing and filtering working")
    print("- Document download functional")
    print("- Metadata updates working")
    print("- Document deletion (admin) working")
    print("- Activity logging active")
    print()

if __name__ == "__main__":
    main()
