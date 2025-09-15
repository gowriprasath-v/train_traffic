import os
import logging
from contextlib import contextmanager
from pymongo import MongoClient, errors, ASCENDING, DESCENDING
from pymongo.collection import Collection
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set in .env")

logger = logging.getLogger(__name__)

class MongoConnectionManager:
    """Enhanced MongoDB connection manager with proper error handling"""
    
    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db = None
        self._alerts_collection: Optional[Collection] = None
        self._connected = False
    
    def connect(self):
        """Establish MongoDB connection with retry logic"""
        if self._connected:
            return
            
        try:
            self._client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                maxPoolSize=50,
                retryWrites=True
            )
            
            # Test connection
            self._client.server_info()
            
            self._db = self._client["train_traffic_alerts"]
            self._alerts_collection = self._db.get_collection("alerts")
            
            # Create indexes for better performance
            self._create_indexes()
            
            self._connected = True
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.exception(f"Failed to connect to MongoDB: {e}")
            self._client = None
            self._connected = False
            raise RuntimeError(f"MongoDB connection failed: {e}")
    
    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Create indexes
            self._alerts_collection.create_index([("timestamp", DESCENDING)])
            self._alerts_collection.create_index([("level", ASCENDING)])
            self._alerts_collection.create_index([("alert_type", ASCENDING)])
            self._alerts_collection.create_index([
                ("timestamp", DESCENDING),
                ("level", ASCENDING)
            ])
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self._client:
            try:
                self._client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")
            finally:
                self._client = None
                self._db = None
                self._alerts_collection = None
                self._connected = False
    
    @contextmanager
    def get_collection(self):
        """Context manager for collection operations"""
        if not self._connected:
            self.connect()
        
        try:
            yield self._alerts_collection
        except errors.ServerSelectionTimeoutError:
            logger.error("MongoDB server selection timeout")
            self._connected = False
            raise
        except errors.NetworkTimeout:
            logger.error("MongoDB network timeout")
            self._connected = False
            raise
        except Exception as e:
            logger.error(f"MongoDB operation error: {e}")
            raise
    
    @property
    def is_connected(self) -> bool:
        """Check if connection is active"""
        if not self._connected or not self._client:
            return False
        
        try:
            self._client.server_info()
            return True
        except Exception:
            self._connected = False
            return False

# Global connection manager
connection_manager = MongoConnectionManager()

def ensure_connection():
    """Ensure MongoDB connection is active"""
    if not connection_manager.is_connected:
        connection_manager.connect()

def save_alert(alert_data: Dict) -> str:
    """
    Save alert to MongoDB with enhanced validation and error handling
    """
    if not alert_data or not isinstance(alert_data, dict):
        raise ValueError("Invalid alert data provided")
    
    # Validate required fields
    required_fields = ["alert_type", "message", "level"]
    missing_fields = [field for field in required_fields if field not in alert_data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    # Ensure timestamp
    if "timestamp" not in alert_data or not alert_data["timestamp"]:
        alert_data["timestamp"] = datetime.utcnow().isoformat()
    
    # Add metadata
    alert_data.update({
        "created_at": datetime.utcnow(),
        "source": "train_traffic_system",
        "version": "1.0"
    })
    
    # Validate alert level
    valid_levels = ["info", "warning", "error", "critical"]
    if alert_data["level"].lower() not in valid_levels:
        raise ValueError(f"Invalid alert level. Must be one of: {valid_levels}")
    
    try:
        ensure_connection()
        
        with connection_manager.get_collection() as collection:
            result = collection.insert_one(alert_data)
            alert_id = str(result.inserted_id)
            
        logger.info(f"Alert saved successfully: {alert_id}")
        return alert_id
        
    except errors.PyMongoError as e:
        logger.exception(f"MongoDB error while saving alert: {e}")
        raise RuntimeError(f"Failed to save alert: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error while saving alert: {e}")
        raise

def get_recent_alerts(limit: int = 10, level: Optional[str] = None, 
                     alert_type: Optional[str] = None, 
                     hours_back: Optional[int] = None) -> List[Dict]:
    """
    Retrieve recent alerts with enhanced filtering options
    """
    if limit <= 0 or limit > 1000:
        raise ValueError("Limit must be between 1 and 1000")
    
    try:
        ensure_connection()
        
        # Build query filter
        query_filter = {}
        
        if level:
            query_filter["level"] = level.lower()
        
        if alert_type:
            query_filter["alert_type"] = {"$regex": alert_type, "$options": "i"}
        
        if hours_back:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            query_filter["created_at"] = {"$gte": cutoff_time}
        
        with connection_manager.get_collection() as collection:
            cursor = (collection
                     .find(query_filter)
                     .sort("created_at", DESCENDING)
                     .limit(limit))
            
            results = []
            for alert in cursor:
                # Remove MongoDB ObjectId and convert datetime
                alert.pop("_id", None)
                if "created_at" in alert and isinstance(alert["created_at"], datetime):
                    alert["created_at"] = alert["created_at"].isoformat()
                results.append(alert)
        
        logger.info(f"Retrieved {len(results)} alerts")
        return results
        
    except errors.PyMongoError as e:
        logger.exception(f"MongoDB error while reading alerts: {e}")
        raise RuntimeError(f"Failed to retrieve alerts: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error while reading alerts: {e}")
        raise

# Initialize connection on module import
try:
    connection_manager.connect()
except Exception as e:
    logger.warning(f"Failed to initialize MongoDB connection: {e}")
    # Don't raise here to allow the module to load
