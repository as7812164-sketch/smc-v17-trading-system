"""
MongoDB Atlas (Free Tier) Client with Graceful Local SQLite Fallback.
Provides NoSQL document persistence for SMC V17 Crypto Sniper trades, telemetry, and memory.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("smc.mongo")

# Try importing pymongo gracefully
try:
    from pymongo import MongoClient, ReplaceOne
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    MongoClient = None
    PYMONGO_AVAILABLE = False
    logger.info("pymongo is not installed. System will use SQLite + CSV storage.")

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "smc_v17_crypto")

_client = None
_db = None

def get_mongo_db():
    """Returns the MongoDB database instance if configured and reachable, else None."""
    global _client, _db
    if not PYMONGO_AVAILABLE or not MONGO_URI:
        return None
    
    if _db is not None:
        return _db
    
    try:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
        # Verify connection
        _client.admin.command('ping')
        _db = _client[MONGO_DB_NAME]
        logger.info(f"Connected to MongoDB Atlas: {MONGO_DB_NAME}")
        return _db
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Falling back to SQLite/CSV.")
        _client = None
        _db = None
        return None

def is_mongo_connected() -> bool:
    """Check if MongoDB is actively connected and reachable."""
    return get_mongo_db() is not None

def save_trade_to_mongo(trade_dict: Dict[str, Any]) -> bool:
    """Save or update a single trade document in MongoDB."""
    db = get_mongo_db()
    if db is None:
        return False
    try:
        trade_id = trade_dict.get("trade_id")
        if not trade_id:
            return False
        db.trades_ledger.replace_one({"trade_id": trade_id}, trade_dict, upsert=True)
        return True
    except Exception as e:
        logger.warning(f"Failed to save trade to MongoDB: {e}")
        return False

def sync_trades_to_mongo(trades: List[Dict[str, Any]]) -> int:
    """Batch sync multiple trades into MongoDB trades_ledger collection."""
    db = get_mongo_db()
    if db is None or not trades:
        return 0
    try:
        operations = [
            ReplaceOne({"trade_id": t["trade_id"]}, t, upsert=True)
            for t in trades if "trade_id" in t
        ]
        if operations:
            res = db.trades_ledger.bulk_write(operations, ordered=False)
            return (res.upserted_count or 0) + (res.modified_count or 0)
    except Exception as e:
        logger.warning(f"Batch MongoDB sync failed: {e}")
    return 0

def get_trades_from_mongo(limit: int = 300) -> List[Dict[str, Any]]:
    """Retrieve trades from MongoDB sorted newest first."""
    db = get_mongo_db()
    if db is None:
        return []
    try:
        cursor = db.trades_ledger.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return list(cursor)
    except Exception as e:
        logger.warning(f"Failed to fetch trades from MongoDB: {e}")
        return []

def record_scan_snapshot(scan_results: Dict[str, Any]) -> bool:
    """Record a market scan snapshot to MongoDB for historical tracking."""
    db = get_mongo_db()
    if db is None:
        return False
    try:
        import time
        doc = {
            "timestamp": int(time.time()),
            "results": scan_results
        }
        db.market_scans.insert_one(doc)
        return True
    except Exception as e:
        logger.warning(f"Failed to save scan snapshot to MongoDB: {e}")
        return False
