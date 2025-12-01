"""
Firebase Configuration and Utilities
Handles Firebase Admin SDK initialization and provides utility functions
"""

import os
import json
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv

load_dotenv()

# Global Firebase app instance
_firebase_app: Optional[firebase_admin.App] = None
_firestore_client: Optional[firestore.client] = None


def initialize_firebase():
    """
    Initialize Firebase Admin SDK
    Can use either service account JSON file or JSON string from environment variable
    """
    global _firebase_app, _firestore_client
    
    if _firebase_app is not None:
        return _firebase_app
    
    try:
        # Try to load from JSON file path
        firebase_creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        
        if firebase_creds_path and os.path.exists(firebase_creds_path):
            cred = credentials.Certificate(firebase_creds_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized from credentials file")
        
        # Try to load from JSON string in environment variable
        elif os.getenv('FIREBASE_CREDENTIALS_JSON'):
            firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            _firebase_app = firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized from credentials JSON string")
        
        else:
            print("⚠️ Firebase credentials not found. Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON in .env")
            return None
        
        # Initialize Firestore client
        _firestore_client = firestore.client()
        
        return _firebase_app
        
    except Exception as e:
        print(f"❌ Error initializing Firebase: {str(e)}")
        return None


def get_firestore_client():
    """Get Firestore client instance"""
    global _firestore_client
    
    if _firestore_client is None:
        initialize_firebase()
    
    return _firestore_client


def check_firebase_connection() -> dict:
    """
    Check Firebase connection status
    Returns a dictionary with connection info and test results
    """
    try:
        if _firebase_app is None:
            initialize_firebase()
        
        if _firebase_app is None:
            return {
                "status": "disconnected",
                "message": "Firebase not initialized. Check credentials in .env file.",
                "firebase_app": None,
                "firestore": None,
            }
        
        # Test Firestore connection
        db = get_firestore_client()
        firestore_status = "connected" if db is not None else "disconnected"
        
        # Try to read a test collection (this doesn't need to exist)
        test_result = None
        try:
            # This will succeed even if collection doesn't exist
            test_ref = db.collection('_connection_test').limit(1)
            list(test_ref.stream())  # Force execution
            test_result = "success"
        except Exception as e:
            test_result = f"error: {str(e)}"
        
        return {
            "status": "connected",
            "message": "Firebase Admin SDK initialized successfully",
            "firebase_app": _firebase_app.name if _firebase_app else None,
            "firestore": firestore_status,
            "test_query": test_result,
            "project_id": _firebase_app.project_id if _firebase_app else None,
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking Firebase connection: {str(e)}",
            "firebase_app": None,
            "firestore": None,
        }


# Firestore utility functions
async def get_user_by_uid(uid: str) -> Optional[dict]:
    """Get user data from Firestore by UID"""
    try:
        db = get_firestore_client()
        if db is None:
            return None
        
        doc_ref = db.collection('users').document(uid)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        return None


async def get_user_favorites(uid: str) -> list:
    """Get user's favorite products from Firestore"""
    try:
        db = get_firestore_client()
        if db is None:
            return []
        
        # Assuming favorites are stored in a subcollection
        favorites_ref = db.collection('users').document(uid).collection('favorites')
        favorites = favorites_ref.stream()
        
        return [doc.to_dict() for doc in favorites]
    except Exception as e:
        print(f"Error fetching favorites: {str(e)}")
        return []


async def add_user_favorite(uid: str, product_id: str, product_data: dict) -> bool:
    """Add a product to user's favorites"""
    try:
        db = get_firestore_client()
        if db is None:
            return False
        
        favorite_ref = db.collection('users').document(uid).collection('favorites').document(product_id)
        favorite_ref.set(product_data)
        
        return True
    except Exception as e:
        print(f"Error adding favorite: {str(e)}")
        return False


async def remove_user_favorite(uid: str, product_id: str) -> bool:
    """Remove a product from user's favorites"""
    try:
        db = get_firestore_client()
        if db is None:
            return False
        
        favorite_ref = db.collection('users').document(uid).collection('favorites').document(product_id)
        favorite_ref.delete()
        
        return True
    except Exception as e:
        print(f"Error removing favorite: {str(e)}")
        return False


async def get_all_products() -> list:
    """Get all products from Firestore"""
    try:
        db = get_firestore_client()
        if db is None:
            return []
        
        products_ref = db.collection('products')
        products = products_ref.stream()
        
        return [{"id": doc.id, **doc.to_dict()} for doc in products]
    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        return []


async def get_product_by_id(product_id: str) -> Optional[dict]:
    """Get a specific product by ID"""
    try:
        db = get_firestore_client()
        if db is None:
            return None
        
        doc_ref = db.collection('products').document(product_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return {"id": doc.id, **doc.to_dict()}
        return None
    except Exception as e:
        print(f"Error fetching product: {str(e)}")
        return None


# Verify Firebase Auth token
def verify_firebase_token(id_token: str) -> Optional[dict]:
    """
    Verify Firebase ID token and return decoded token
    Use this for authentication middleware
    """
    try:
        if _firebase_app is None:
            initialize_firebase()
        
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Error verifying token: {str(e)}")
        return None
