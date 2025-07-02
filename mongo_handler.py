from pymongo import MongoClient
from datetime import datetime
import json
import os
from dotenv import load_dotenv

class MongoDBHandler:
    def __init__(self):
        # Ortam değişkenlerini yükle
        load_dotenv()
        
        self.MONGODB_URI = os.getenv('MONGODB_URI')
        self.DB_NAME = os.getenv('MONGODB_DB_NAME')
        self.COLLECTION_NAME = os.getenv('MONGODB_COLLECTION_NAME')
        
        self.client = MongoClient(self.MONGODB_URI)
        self.db = self.client[self.DB_NAME]
    
    def save_analysis_results(self, video_name, json_path):
        """Video analiz sonuçlarını MongoDB'ye kaydeder"""
        collection = self.db[self.COLLECTION_NAME]
        
        with open(json_path) as f:
            labels = json.load(f)
        
        document = {
            "video_name": video_name,
            "analysis_date": datetime.now(),
            "labels": labels,
            "status": "completed"
        }
        
        return collection.insert_one(document).inserted_id
    
    def get_results(self, video_name=None):
        """Sonuçları sorgular"""
        collection = self.db[self.COLLECTION_NAME]
        if video_name:
            return collection.find_one({"video_name": video_name})
        return list(collection.find({}))
    
    def close_connection(self):
        """Bağlantıyı güvenli şekilde kapat"""
        if hasattr(self, 'client') and self.client:
            self.client.close()
            self.client = None
            self.db = None