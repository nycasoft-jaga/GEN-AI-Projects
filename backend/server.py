from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import httpx
import asyncio
import re


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class ProductAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    barcode: str
    product_name: str
    brand: Optional[str] = None
    nutrition_score: float  # 1-5 stars
    diabetic_score: float  # 1-5 stars
    processing_level: str  # "Unprocessed", "Processed", "Ultra-processed", "Unknown"
    who_compliance: Dict[str, bool]  # WHO guideline compliance
    nutritional_info: Dict
    ingredients: List[str] = []
    analysis_details: Dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProductAnalysisCreate(BaseModel):
    barcode: str

class ScanHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    barcode: str
    product_name: str
    nutrition_score: float
    diabetic_score: float
    processing_level: str
    scanned_at: datetime = Field(default_factory=datetime.utcnow)


class FoodAnalyzer:
    """Comprehensive food analysis engine"""
    
    @staticmethod
    def calculate_diabetic_score(nutrition: Dict) -> tuple[float, Dict]:
        """Calculate diabetic friendliness score (1-5, higher is better)"""
        score = 5.0
        details = {}
        
        # Sugar content analysis
        sugars = nutrition.get('sugars_100g', 0) or 0
        if sugars > 15:  # High sugar
            score -= 2.0
            details['sugar_impact'] = 'High sugar content - not diabetic friendly'
        elif sugars > 5:  # Medium sugar
            score -= 1.0
            details['sugar_impact'] = 'Moderate sugar content - consume with caution'
        else:
            details['sugar_impact'] = 'Low sugar content - diabetic friendly'
        
        # Carbohydrate analysis
        carbs = nutrition.get('carbohydrates_100g', 0) or 0
        fiber = nutrition.get('fiber_100g', 0) or 0
        
        # Calculate net carbs
        net_carbs = max(0, carbs - fiber)
        if net_carbs > 20:
            score -= 1.5
            details['carb_impact'] = 'High net carbohydrates'
        elif net_carbs > 10:
            score -= 0.5
            details['carb_impact'] = 'Moderate net carbohydrates'
        else:
            details['carb_impact'] = 'Low net carbohydrates - good for diabetics'
        
        # Fiber bonus
        if fiber > 5:
            score += 0.5
            details['fiber_bonus'] = 'High fiber content helps slow glucose absorption'
        
        # Glycemic load estimation
        gl_estimate = (carbs * 0.7) / 100  # Simplified GL calculation
        if gl_estimate > 20:
            score -= 1.0
            details['glycemic_load'] = 'High estimated glycemic load'
        elif gl_estimate < 10:
            score += 0.5
            details['glycemic_load'] = 'Low estimated glycemic load - good for blood sugar control'
        
        return max(1.0, min(5.0, score)), details
    
    @staticmethod
    def classify_processing_level(ingredients: List[str], nutrition: Dict) -> tuple[str, Dict]:
        """Classify food processing level using NOVA system"""
        if not ingredients:
            return "Unknown", {"reason": "No ingredients information available"}
        
        ingredients_text = ' '.join(ingredients).lower()
        details = {}
        
        # Ultra-processed indicators
        ultra_processed_indicators = [
            'high fructose corn syrup', 'corn syrup', 'artificial flavor', 'artificial colour',
            'preservative', 'emulsifier', 'stabilizer', 'thickener', 'anti-caking agent',
            'flavor enhancer', 'maltodextrin', 'modified starch', 'hydrogenated',
            'partially hydrogenated', 'aspartame', 'sucralose', 'acesulfame'
        ]
        
        ultra_count = sum(1 for indicator in ultra_processed_indicators if indicator in ingredients_text)
        
        # Processed indicators
        processed_indicators = [
            'sugar', 'salt', 'oil', 'butter', 'vinegar', 'honey', 'syrup'
        ]
        
        processed_count = sum(1 for indicator in processed_indicators if indicator in ingredients_text)
        
        # Classification logic
        if ultra_count >= 2:
            details['classification_reason'] = f'Contains {ultra_count} ultra-processing indicators'
            details['indicators_found'] = [ind for ind in ultra_processed_indicators if ind in ingredients_text]
            return "Ultra-processed", details
        elif ultra_count >= 1 or processed_count >= 3:
            details['classification_reason'] = f'Contains processing ingredients'
            return "Processed", details
        elif processed_count >= 1:
            details['classification_reason'] = 'Contains some processed ingredients'
            return "Minimally processed", details
        else:
            details['classification_reason'] = 'Contains mainly whole food ingredients'
            return "Unprocessed", details
    
    @staticmethod
    def check_who_compliance(nutrition: Dict) -> tuple[Dict[str, bool], Dict]:
        """Check compliance with WHO guidelines"""
        compliance = {}
        details = {}
        
        # WHO sugar guideline: <10% of calories (roughly <50g/day, or <5g per 100g)
        sugars = nutrition.get('sugars_100g', 0) or 0
        compliance['sugar'] = sugars <= 5.0
        details['sugar'] = f"Sugar content: {sugars}g/100g (WHO recommends ≤5g/100g)"
        
        # WHO salt guideline: <5g/day (roughly <0.5g per 100g)
        salt = nutrition.get('salt_100g', 0) or 0
        compliance['salt'] = salt <= 0.5
        details['salt'] = f"Salt content: {salt}g/100g (WHO recommends ≤0.5g/100g)"
        
        # WHO saturated fat guideline: <10% of calories (roughly <1g per 100g)
        sat_fat = nutrition.get('saturated-fat_100g', 0) or 0
        compliance['saturated_fat'] = sat_fat <= 1.0
        details['saturated_fat'] = f"Saturated fat: {sat_fat}g/100g (WHO recommends ≤1g/100g)"
        
        return compliance, details
    
    @staticmethod
    def calculate_nutrition_score(nutrition: Dict, processing_level: str, who_compliance: Dict) -> tuple[float, Dict]:
        """Calculate overall nutrition score (1-5 stars)"""
        score = 3.0  # Start with middle score
        details = {}
        
        # Processing level impact
        processing_scores = {
            "Unprocessed": 2.0,
            "Minimally processed": 1.0,
            "Processed": -0.5,
            "Ultra-processed": -1.5,
            "Unknown": 0
        }
        
        processing_impact = processing_scores.get(processing_level, 0)
        score += processing_impact
        details['processing_impact'] = f"Processing level ({processing_level}): {processing_impact:+.1f} points"
        
        # WHO compliance
        compliance_score = sum(who_compliance.values()) * 0.5
        score += compliance_score
        details['who_compliance_impact'] = f"WHO compliance: {compliance_score:+.1f} points"
        
        # Nutritional quality
        fiber = nutrition.get('fiber_100g', 0) or 0
        protein = nutrition.get('proteins_100g', 0) or 0
        
        if fiber > 5:
            score += 0.5
            details['fiber_bonus'] = "High fiber: +0.5 points"
        
        if protein > 10:
            score += 0.5
            details['protein_bonus'] = "Good protein content: +0.5 points"
        
        # Energy density consideration
        energy = nutrition.get('energy-kcal_100g', 0) or 0
        if energy > 500:  # Very high calorie
            score -= 0.5
            details['calorie_penalty'] = "High calorie density: -0.5 points"
        
        return max(1.0, min(5.0, score)), details


@api_router.post("/analyze-product", response_model=ProductAnalysis)
async def analyze_product(input: ProductAnalysisCreate):
    """Analyze a product by barcode"""
    try:
        # Fetch product data from Open Food Facts
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://world.openfoodfacts.org/api/v2/product/{input.barcode}.json"
            )
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Product not found")
        
        data = response.json()
        
        if data.get('status') != 1:
            raise HTTPException(status_code=404, detail="Product not found in database")
        
        product = data['product']
        
        # Extract nutritional information
        nutriments = product.get('nutriments', {})
        ingredients_list = product.get('ingredients_text', '').split(',') if product.get('ingredients_text') else []
        ingredients_list = [ing.strip() for ing in ingredients_list if ing.strip()]
        
        # Perform analysis
        analyzer = FoodAnalyzer()
        
        # Calculate scores
        diabetic_score, diabetic_details = analyzer.calculate_diabetic_score(nutriments)
        processing_level, processing_details = analyzer.classify_processing_level(ingredients_list, nutriments)
        who_compliance, who_details = analyzer.check_who_compliance(nutriments)
        nutrition_score, nutrition_details = analyzer.calculate_nutrition_score(
            nutriments, processing_level, who_compliance
        )
        
        # Create analysis object
        analysis = ProductAnalysis(
            barcode=input.barcode,
            product_name=product.get('product_name', 'Unknown Product'),
            brand=product.get('brands', '').split(',')[0].strip() if product.get('brands') else None,
            nutrition_score=nutrition_score,
            diabetic_score=diabetic_score,
            processing_level=processing_level,
            who_compliance=who_compliance,
            nutritional_info={
                'energy_kcal': nutriments.get('energy-kcal_100g'),
                'proteins': nutriments.get('proteins_100g'),
                'carbohydrates': nutriments.get('carbohydrates_100g'),
                'sugars': nutriments.get('sugars_100g'),
                'fiber': nutriments.get('fiber_100g'),
                'fat': nutriments.get('fat_100g'),
                'saturated_fat': nutriments.get('saturated-fat_100g'),
                'salt': nutriments.get('salt_100g'),
                'sodium': nutriments.get('sodium_100g')
            },
            ingredients=ingredients_list,
            analysis_details={
                'diabetic_analysis': diabetic_details,
                'processing_analysis': processing_details,
                'who_analysis': who_details,
                'nutrition_analysis': nutrition_details
            }
        )
        
        # Store in database
        await db.product_analyses.insert_one(analysis.dict())
        
        # Add to scan history
        history = ScanHistory(
            barcode=input.barcode,
            product_name=analysis.product_name,
            nutrition_score=nutrition_score,
            diabetic_score=diabetic_score,
            processing_level=processing_level
        )
        await db.scan_history.insert_one(history.dict())
        
        return analysis
        
    except Exception as e:
        logging.error(f"Error analyzing product {input.barcode}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@api_router.get("/scan-history", response_model=List[ScanHistory])
async def get_scan_history(limit: int = 50):
    """Get scan history"""
    history = await db.scan_history.find().sort("scanned_at", -1).limit(limit).to_list(limit)
    return [ScanHistory(**item) for item in history]


@api_router.get("/product/{barcode}")
async def get_cached_analysis(barcode: str):
    """Get cached analysis for a barcode"""
    analysis = await db.product_analyses.find_one({"barcode": barcode})
    if analysis:
        return ProductAnalysis(**analysis)
    raise HTTPException(status_code=404, detail="Analysis not found")


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()