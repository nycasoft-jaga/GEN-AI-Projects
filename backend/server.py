from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import cv2
import numpy as np
import json
import asyncio
import base64
import io
from PIL import Image
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import os
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Health Tracker API",
    description="Face scanning health monitoring for glucose, anxiety and depression",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.health_tracker

@dataclass
class HealthResult:
    id: str
    emotion: str
    confidence: float
    stress_level: float
    anxiety_score: float
    depression_score: float
    glucose_simulation: float
    timestamp: float
    face_coordinates: Optional[Tuple[int, int, int, int]] = None
    recommendations: List[str] = None

class LocalHealthAnalyzer:
    def __init__(self):
        self.emotion_history = deque(maxlen=50)
        self.stress_emotions = ['angry', 'fear', 'sad', 'disgust']
        self.anxiety_keywords = ['fear', 'surprise', 'angry']
        self.depression_keywords = ['sad', 'fear', 'disgust']
        
        # Initialize face cascade
        cascade_path = '/app/backend/haarcascade_frontalface_default.xml'
        if not os.path.exists(cascade_path):
            # Download if not exists
            import requests
            url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
            response = requests.get(url)
            with open(cascade_path, 'wb') as f:
                f.write(response.content)
        
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        logger.info("Local Health Analyzer initialized")

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces in the frame"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(30, 30)
            )
            return [(x, y, w, h) for x, y, w, h in faces]
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return []

    def simulate_emotion_analysis(self, face_region: np.ndarray) -> Dict[str, Any]:
        """Simulate emotion analysis (replace with actual DeepFace when installed)"""
        try:
            if face_region.size == 0:
                return {"dominant_emotion": "neutral", "emotion_scores": {}, "confidence": 0.5}
            
            # Simulate emotion detection based on image characteristics
            height, width = face_region.shape[:2]
            brightness = np.mean(face_region)
            
            # Simple heuristic-based emotion simulation
            emotions = ['happy', 'sad', 'angry', 'fear', 'surprise', 'disgust', 'neutral']
            
            # Simulate based on brightness and other simple features
            if brightness > 150:
                dominant = 'happy'
                scores = {'Happy': 75, 'Neutral': 15, 'Surprise': 10}
            elif brightness < 80:
                dominant = 'sad'
                scores = {'Sad': 70, 'Neutral': 20, 'Fear': 10}
            else:
                dominant = 'neutral'
                scores = {'Neutral': 60, 'Happy': 25, 'Sad': 15}
            
            confidence = min(0.9, max(0.3, brightness / 255.0))
            
            return {
                "dominant_emotion": dominant,
                "emotion_scores": scores,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Emotion analysis error: {e}")
            return {"dominant_emotion": "neutral", "emotion_scores": {}, "confidence": 0.0}

    def calculate_health_metrics(self, emotion_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate health metrics from emotion data"""
        current_emotion = emotion_data.get('dominant_emotion', 'neutral')
        emotion_scores = emotion_data.get('emotion_scores', {})
        confidence = emotion_data.get('confidence', 0.0)
        
        # Calculate stress level
        stress_score = 0.0
        for emotion in self.stress_emotions:
            if emotion.title() in emotion_scores:
                stress_score += emotion_scores[emotion.title()] * 0.01
        
        # Add historical pattern analysis
        if len(self.emotion_history) >= 5:
            recent_emotions = list(self.emotion_history)[-5:]
            stress_count = sum(1 for e in recent_emotions if e in self.stress_emotions)
            stress_score += (stress_count / len(recent_emotions)) * 0.5
        
        stress_level = min(stress_score, 1.0)
        
        # Calculate anxiety score
        anxiety_score = 0.0
        if current_emotion in self.anxiety_keywords:
            anxiety_score += 0.3
        if emotion_scores.get('Fear', 0) > 40:
            anxiety_score += 0.4
        if stress_level > 0.7:
            anxiety_score += 0.3
        
        # Calculate depression score
        depression_score = 0.0
        if current_emotion in self.depression_keywords:
            depression_score += 0.3
        if emotion_scores.get('Sad', 0) > 50:
            depression_score += 0.5
        if emotion_scores.get('Happy', 0) < 10 and emotion_scores.get('Neutral', 0) < 30:
            depression_score += 0.2
        
        # Simulate glucose level (normally would require actual medical device)
        # Based on stress and other factors
        base_glucose = 90  # Normal fasting glucose
        stress_impact = stress_level * 30  # Stress can raise glucose
        glucose_simulation = base_glucose + stress_impact + np.random.normal(0, 5)
        glucose_simulation = max(70, min(200, glucose_simulation))  # Realistic range
        
        return {
            'stress_level': min(stress_level, 1.0),
            'anxiety_score': min(anxiety_score, 1.0),
            'depression_score': min(depression_score, 1.0),
            'glucose_simulation': round(glucose_simulation, 1)
        }

    def generate_recommendations(self, health_metrics: Dict[str, float], emotion: str) -> List[str]:
        """Generate health recommendations"""
        recommendations = []
        
        if health_metrics['stress_level'] > 0.6:
            recommendations.append("High stress detected. Try deep breathing exercises.")
        
        if health_metrics['anxiety_score'] > 0.5:
            recommendations.append("Anxiety indicators present. Consider relaxation techniques.")
        
        if health_metrics['depression_score'] > 0.5:
            recommendations.append("Low mood detected. Gentle exercise or sunlight may help.")
        
        if health_metrics['glucose_simulation'] > 140:
            recommendations.append("Elevated glucose simulation. Stay hydrated and avoid stress.")
        elif health_metrics['glucose_simulation'] < 80:
            recommendations.append("Low glucose simulation. Consider a healthy snack.")
        
        if emotion == 'happy':
            recommendations.append("Great mood detected! Keep up the positive energy.")
        
        if not recommendations:
            recommendations.append("Overall health indicators look balanced. Keep monitoring!")
        
        return recommendations

    async def analyze_frame(self, frame: np.ndarray) -> List[HealthResult]:
        """Analyze frame for health indicators"""
        results = []
        faces = self.detect_faces(frame)
        
        for x, y, w, h in faces:
            face_region = frame[y:y+h, x:x+w]
            
            # Analyze emotion
            emotion_data = self.simulate_emotion_analysis(face_region)
            
            # Update emotion history
            self.emotion_history.append(emotion_data['dominant_emotion'])
            
            # Calculate health metrics
            health_metrics = self.calculate_health_metrics(emotion_data)
            
            # Generate recommendations
            recommendations = self.generate_recommendations(health_metrics, emotion_data['dominant_emotion'])
            
            result = HealthResult(
                id=str(uuid.uuid4()),
                emotion=emotion_data['dominant_emotion'],
                confidence=emotion_data['confidence'],
                stress_level=health_metrics['stress_level'],
                anxiety_score=health_metrics['anxiety_score'],
                depression_score=health_metrics['depression_score'],
                glucose_simulation=health_metrics['glucose_simulation'],
                timestamp=time.time(),
                face_coordinates=(x, y, w, h),
                recommendations=recommendations
            )
            
            results.append(result)
        
        return results

# Global analyzer instance
analyzer = LocalHealthAnalyzer()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_analysis_result(self, result: Dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(result))
        except Exception as e:
            logger.error(f"Error sending websocket message: {e}")

manager = ConnectionManager()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Health Tracker API is running"}

@app.post("/api/analyze/image")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze uploaded image for health indicators"""
    try:
        # Read and process image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Perform analysis
        results = await analyzer.analyze_frame(frame)
        
        # Store results in database
        for result in results:
            await db.health_readings.insert_one(asdict(result))
        
        return JSONResponse(content={
            "success": True,
            "faces_detected": len(results),
            "results": [asdict(result) for result in results]
        })
        
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health/history")
async def get_health_history(limit: int = 50):
    """Get recent health readings"""
    try:
        cursor = db.health_readings.find().sort("timestamp", -1).limit(limit)
        readings = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for reading in readings:
            reading["_id"] = str(reading["_id"])
        
        return JSONResponse(content={
            "success": True,
            "readings": readings
        })
        
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/api/ws/scan")
async def websocket_scan(websocket: WebSocket):
    """WebSocket endpoint for real-time health scanning"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive frame data from client
            data = await websocket.receive_text()
            frame_data = json.loads(data)
            
            if 'frame' in frame_data:
                try:
                    # Decode base64 image
                    image_data = base64.b64decode(frame_data['frame'].split(',')[1])
                    image = Image.open(io.BytesIO(image_data))
                    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    
                    # Perform analysis
                    results = await analyzer.analyze_frame(frame)
                    
                    # Store results in database
                    for result in results:
                        await db.health_readings.insert_one(asdict(result))
                    
                    # Prepare response
                    response = {
                        "type": "analysis_result",
                        "timestamp": time.time(),
                        "faces_detected": len(results),
                        "results": [asdict(result) for result in results]
                    }
                    
                    await manager.send_analysis_result(response, websocket)
                    
                except Exception as e:
                    logger.error(f"Frame processing error: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Processing failed: {str(e)}"
                    }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1000)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)