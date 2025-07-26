#!/usr/bin/env python3
"""
Detailed diagnostic test for NOVA classification issue
"""

import requests
import json

BASE_URL = "https://84fba3ec-51f2-495a-b130-c09fc152e76c.preview.emergentagent.com/api"

def detailed_nutella_analysis():
    """Get detailed analysis of Nutella to understand NOVA classification issue"""
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-product",
            json={"barcode": "3017620422003"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        
        print("=== NUTELLA ANALYSIS DETAILS ===")
        print(f"Product Name: {data.get('product_name')}")
        print(f"Brand: {data.get('brand')}")
        print(f"Processing Level: {data.get('processing_level')}")
        print(f"Nutrition Score: {data.get('nutrition_score')}")
        print(f"Diabetic Score: {data.get('diabetic_score')}")
        
        print("\n=== INGREDIENTS ===")
        ingredients = data.get('ingredients', [])
        for i, ingredient in enumerate(ingredients, 1):
            print(f"{i}. {ingredient}")
        
        print(f"\nTotal ingredients: {len(ingredients)}")
        
        print("\n=== NUTRITIONAL INFO ===")
        nutrition = data.get('nutritional_info', {})
        for key, value in nutrition.items():
            print(f"{key}: {value}")
        
        print("\n=== ANALYSIS DETAILS ===")
        analysis_details = data.get('analysis_details', {})
        
        if 'processing_analysis' in analysis_details:
            print("Processing Analysis:")
            proc_analysis = analysis_details['processing_analysis']
            for key, value in proc_analysis.items():
                print(f"  {key}: {value}")
        
        if 'diabetic_analysis' in analysis_details:
            print("\nDiabetic Analysis:")
            diab_analysis = analysis_details['diabetic_analysis']
            for key, value in diab_analysis.items():
                print(f"  {key}: {value}")
        
        if 'who_analysis' in analysis_details:
            print("\nWHO Analysis:")
            who_analysis = analysis_details['who_analysis']
            for key, value in who_analysis.items():
                print(f"  {key}: {value}")
        
        print("\n=== WHO COMPLIANCE ===")
        who_compliance = data.get('who_compliance', {})
        for key, value in who_compliance.items():
            print(f"{key}: {value}")
        
        # Check for ultra-processed indicators in ingredients
        print("\n=== ULTRA-PROCESSED INDICATORS CHECK ===")
        ingredients_text = ' '.join(ingredients).lower()
        ultra_indicators = [
            'high fructose corn syrup', 'corn syrup', 'artificial flavor', 'artificial colour',
            'preservative', 'emulsifier', 'stabilizer', 'thickener', 'anti-caking agent',
            'flavor enhancer', 'maltodextrin', 'modified starch', 'hydrogenated',
            'partially hydrogenated', 'aspartame', 'sucralose', 'acesulfame'
        ]
        
        found_indicators = []
        for indicator in ultra_indicators:
            if indicator in ingredients_text:
                found_indicators.append(indicator)
        
        print(f"Found ultra-processed indicators: {found_indicators}")
        print(f"Count: {len(found_indicators)}")
        
        # Check for processed indicators
        processed_indicators = ['sugar', 'salt', 'oil', 'butter', 'vinegar', 'honey', 'syrup']
        found_processed = []
        for indicator in processed_indicators:
            if indicator in ingredients_text:
                found_processed.append(indicator)
        
        print(f"Found processed indicators: {found_processed}")
        print(f"Count: {len(found_processed)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    detailed_nutella_analysis()