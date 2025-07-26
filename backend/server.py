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
        """Classify food processing level using NOVA system with multi-language support"""
        if not ingredients:
            return "Unknown", {"reason": "No ingredients information available"}
        
        ingredients_text = ' '.join(ingredients).lower()
        details = {}
        
        # Multi-language ultra-processed indicators
        ultra_processed_indicators = [
            # English
            'high fructose corn syrup', 'corn syrup', 'artificial flavor', 'artificial colour', 'artificial color',
            'preservative', 'emulsifier', 'stabilizer', 'stabiliser', 'thickener', 'anti-caking agent',
            'flavor enhancer', 'flavour enhancer', 'maltodextrin', 'modified starch', 'hydrogenated',
            'partially hydrogenated', 'aspartame', 'sucralose', 'acesulfame', 'lecithin', 'vanillin',
            'mono- and diglycerides', 'soy lecithin', 'palm oil', 'polyglycerol', 'carrageenan',
            # French
            'sirop de glucose-fructose', 'sirop de glucose', 'arôme artificiel', 'arômes artificiels',
            'colorant artificiel', 'conservateur', 'émulsifiant', 'stabilisant', 'épaississant',
            'agent anti-mottant', 'exhausteur de goût', 'lécithines', 'vanilline', 'huile de palme',
            'mono- et diglycérides', 'lécithine de soja', 'carraghénanes',
            # German  
            'glukose-fruktose-sirup', 'glukosesirup', 'künstliche aromen', 'künstlicher farbstoff',
            'konservierungsstoff', 'emulgator', 'stabilisator', 'verdickungsmittel', 'trennmittel',
            'geschmacksverstärker', 'lecithin', 'vanillin', 'palmöl', 'mono- und diglyceride',
            'sojalecithin', 'carrageen',
            # Spanish
            'jarabe de glucosa-fructosa', 'jarabe de glucosa', 'aroma artificial', 'colorante artificial',
            'conservante', 'emulsificante', 'estabilizante', 'espesante', 'antiaglomerante',
            'potenciador del sabor', 'lecitina', 'vainillina', 'aceite de palma',
            # Italian
            'sciroppo di glucosio-fruttosio', 'sciroppo di glucosio', 'aroma artificiale', 'colorante artificiale',
            'conservante', 'emulsionante', 'stabilizzante', 'addensante', 'antiagglomerante',
            'esaltatore di sapidità', 'lecitina', 'vanillina', 'olio di palma',
            # Common E-numbers (universal)
            'e100', 'e101', 'e102', 'e104', 'e110', 'e120', 'e122', 'e124', 'e129', 'e131', 'e132', 'e133',
            'e150', 'e151', 'e154', 'e155', 'e160', 'e161', 'e162', 'e163', 'e170', 'e171', 'e172', 'e173',
            'e174', 'e175', 'e180', 'e200', 'e201', 'e202', 'e203', 'e210', 'e211', 'e212', 'e213', 'e214',
            'e215', 'e216', 'e217', 'e218', 'e219', 'e220', 'e221', 'e222', 'e223', 'e224', 'e226', 'e227',
            'e228', 'e234', 'e235', 'e239', 'e242', 'e249', 'e250', 'e251', 'e252', 'e260', 'e261', 'e262',
            'e263', 'e270', 'e280', 'e281', 'e282', 'e283', 'e290', 'e296', 'e297', 'e300', 'e301', 'e302',
            'e304', 'e306', 'e307', 'e308', 'e309', 'e310', 'e311', 'e312', 'e315', 'e316', 'e320', 'e321',
            'e322', 'e325', 'e326', 'e327', 'e330', 'e331', 'e332', 'e333', 'e334', 'e335', 'e336', 'e337',
            'e338', 'e339', 'e340', 'e341', 'e343', 'e350', 'e351', 'e352', 'e353', 'e354', 'e355', 'e356',
            'e357', 'e363', 'e380', 'e385', 'e400', 'e401', 'e402', 'e403', 'e404', 'e405', 'e406', 'e407',
            'e410', 'e412', 'e413', 'e414', 'e415', 'e416', 'e417', 'e418', 'e420', 'e421', 'e422', 'e440',
            'e450', 'e451', 'e452', 'e459', 'e460', 'e461', 'e462', 'e463', 'e464', 'e465', 'e466', 'e470',
            'e471', 'e472', 'e473', 'e474', 'e475', 'e476', 'e477', 'e481', 'e482', 'e483', 'e491', 'e492',
            'e493', 'e494', 'e495', 'e500', 'e501', 'e503', 'e504', 'e507', 'e508', 'e509', 'e511', 'e512',
            'e513', 'e514', 'e515', 'e516', 'e517', 'e518', 'e519', 'e520', 'e521', 'e522', 'e523', 'e524',
            'e525', 'e526', 'e527', 'e528', 'e529', 'e530', 'e535', 'e536', 'e538', 'e541', 'e551', 'e552',
            'e553', 'e554', 'e555', 'e556', 'e558', 'e559', 'e570', 'e574', 'e575', 'e576', 'e577', 'e578',
            'e579', 'e585', 'e620', 'e621', 'e622', 'e623', 'e624', 'e625', 'e626', 'e627', 'e628', 'e629',
            'e630', 'e631', 'e632', 'e633', 'e634', 'e635', 'e640', 'e641', 'e650', 'e900', 'e901', 'e902',
            'e903', 'e904', 'e905', 'e912', 'e914', 'e920', 'e927', 'e928', 'e950', 'e951', 'e952', 'e954',
            'e955', 'e957', 'e959', 'e961', 'e962', 'e965', 'e966', 'e967', 'e968', 'e999'
        ]
        
        ultra_count = sum(1 for indicator in ultra_processed_indicators if indicator in ingredients_text)
        
        # Multi-language processed indicators
        processed_indicators = [
            # English
            'sugar', 'salt', 'oil', 'butter', 'vinegar', 'honey', 'syrup',
            # French
            'sucre', 'sel', 'huile', 'beurre', 'vinaigre', 'miel', 'sirop',
            # German
            'zucker', 'salz', 'öl', 'butter', 'essig', 'honig', 'sirup',
            # Spanish
            'azúcar', 'sal', 'aceite', 'mantequilla', 'vinagre', 'miel', 'jarabe',
            # Italian
            'zucchero', 'sale', 'olio', 'burro', 'aceto', 'miele', 'sciroppo'
        ]
        
        processed_count = sum(1 for indicator in processed_indicators if indicator in ingredients_text)
        
        # Enhanced classification logic with nutritional context
        sugar_content = nutrition.get('sugars_100g', 0) or 0
        
        # Classification logic with additional nutritional context
        if ultra_count >= 3 or (ultra_count >= 2 and sugar_content > 20):
            details['classification_reason'] = f'Contains {ultra_count} ultra-processing indicators'
            details['indicators_found'] = [ind for ind in ultra_processed_indicators if ind in ingredients_text][:10]  # Limit to first 10
            return "Ultra-processed", details
        elif ultra_count >= 1 or processed_count >= 4 or (processed_count >= 2 and sugar_content > 15):
            details['classification_reason'] = f'Contains processing ingredients (ultra: {ultra_count}, processed: {processed_count})'
            return "Processed", details
        elif processed_count >= 2:
            details['classification_reason'] = f'Contains some processed ingredients ({processed_count} found)'
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
        """Calculate overall nutrition score (1-5 stars) with improved logic"""
        score = 3.0  # Start with middle score
        details = {}
        
        # Processing level impact (most important factor)
        processing_scores = {
            "Unprocessed": 1.5,
            "Minimally processed": 0.5,
            "Processed": -0.8,
            "Ultra-processed": -2.0,  # Heavily penalize ultra-processed
            "Unknown": -0.5
        }
        
        processing_impact = processing_scores.get(processing_level, 0)
        score += processing_impact
        details['processing_impact'] = f"Processing level ({processing_level}): {processing_impact:+.1f} points"
        
        # WHO compliance (critical for health)
        compliance_count = sum(who_compliance.values())
        total_guidelines = len(who_compliance)
        compliance_ratio = compliance_count / total_guidelines if total_guidelines > 0 else 0
        
        # Strong penalty for non-compliance
        if compliance_ratio == 1.0:  # All compliant
            compliance_impact = 0.5
        elif compliance_ratio >= 0.67:  # 2/3 compliant
            compliance_impact = 0.0
        elif compliance_ratio >= 0.33:  # 1/3 compliant
            compliance_impact = -0.5
        else:  # Most non-compliant
            compliance_impact = -1.0
            
        score += compliance_impact
        details['who_compliance_impact'] = f"WHO compliance ({compliance_count}/{total_guidelines}): {compliance_impact:+.1f} points"
        
        # Nutritional quality bonuses
        fiber = nutrition.get('fiber_100g', 0) or 0
        protein = nutrition.get('proteins_100g', 0) or 0
        sugars = nutrition.get('sugars_100g', 0) or 0
        salt = nutrition.get('salt_100g', 0) or 0
        
        # Fiber bonus
        if fiber > 10:
            score += 0.5
            details['fiber_bonus'] = "Very high fiber (>10g): +0.5 points"
        elif fiber > 5:
            score += 0.3
            details['fiber_bonus'] = "High fiber (>5g): +0.3 points"
        
        # Protein bonus
        if protein > 15:
            score += 0.3
            details['protein_bonus'] = "High protein (>15g): +0.3 points"
        elif protein > 8:
            score += 0.1
            details['protein_bonus'] = "Good protein (>8g): +0.1 points"
        
        # Sugar penalty (additional to WHO compliance)
        if sugars > 30:  # Very high sugar
            score -= 1.0
            details['sugar_penalty'] = "Very high sugar (>30g): -1.0 points"
        elif sugars > 15:  # High sugar
            score -= 0.5
            details['sugar_penalty'] = "High sugar (>15g): -0.5 points"
        
        # Salt penalty (additional to WHO compliance)
        if salt > 2.0:  # Very high salt
            score -= 0.5
            details['salt_penalty'] = "Very high salt (>2g): -0.5 points"
        elif salt > 1.0:  # High salt
            score -= 0.2
            details['salt_penalty'] = "High salt (>1g): -0.2 points"
        
        # Energy density consideration
        energy = nutrition.get('energy-kcal_100g', 0) or 0
        if energy > 600:  # Very high calorie
            score -= 0.3
            details['calorie_penalty'] = "Very high calorie density (>600kcal): -0.3 points"
        elif energy > 400:  # High calorie
            score -= 0.1
            details['calorie_penalty'] = "High calorie density (>400kcal): -0.1 points"
        
        # Ensure score stays within bounds
        final_score = max(1.0, min(5.0, score))
        
        # Round to one decimal place for cleaner display
        return round(final_score, 1), details


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