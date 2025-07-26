#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Food Analyzer API
Tests all endpoints and verifies analysis algorithms
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# Backend URL from frontend/.env
BASE_URL = "https://84fba3ec-51f2-495a-b130-c09fc152e76c.preview.emergentagent.com/api"

class FoodAnalyzerTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_results = []
        self.session = requests.Session()
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def test_analyze_product_nutella(self):
        """Test Nutella analysis - should be ultra-processed with low diabetic score"""
        try:
            barcode = "3017620422003"
            response = self.session.post(
                f"{self.base_url}/analyze-product",
                json={"barcode": barcode},
                timeout=30
            )
            
            if response.status_code != 200:
                self.log_test("Nutella Analysis", False, f"HTTP {response.status_code}: {response.text}")
                return
            
            data = response.json()
            
            # Verify basic structure
            required_fields = ['barcode', 'product_name', 'nutrition_score', 'diabetic_score', 
                             'processing_level', 'who_compliance', 'nutritional_info', 'ingredients']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Nutella Analysis", False, f"Missing fields: {missing_fields}")
                return
            
            # Verify Nutella-specific expectations
            issues = []
            
            # Check processing level - Nutella should be ultra-processed
            if data['processing_level'] != "Ultra-processed":
                issues.append(f"Processing level is '{data['processing_level']}', expected 'Ultra-processed'")
            
            # Check diabetic score - should be low due to high sugar
            if data['diabetic_score'] > 3.0:
                issues.append(f"Diabetic score is {data['diabetic_score']}, expected ≤3.0 due to high sugar")
            
            # Check product name
            if "nutella" not in data['product_name'].lower():
                issues.append(f"Product name '{data['product_name']}' doesn't contain 'nutella'")
            
            # Check nutritional info has sugar data
            if not data['nutritional_info'].get('sugars'):
                issues.append("Missing sugar information in nutritional_info")
            
            if issues:
                self.log_test("Nutella Analysis", False, "; ".join(issues))
            else:
                self.log_test("Nutella Analysis", True, 
                            f"Processing: {data['processing_level']}, Diabetic: {data['diabetic_score']:.1f}, Nutrition: {data['nutrition_score']:.1f}")
                
        except Exception as e:
            self.log_test("Nutella Analysis", False, f"Exception: {str(e)}")
    
    def test_analyze_product_perrier(self):
        """Test Perrier water analysis - should be unprocessed with high scores"""
        try:
            barcode = "3274080005003"
            response = self.session.post(
                f"{self.base_url}/analyze-product",
                json={"barcode": barcode},
                timeout=30
            )
            
            if response.status_code != 200:
                self.log_test("Perrier Analysis", False, f"HTTP {response.status_code}: {response.text}")
                return
            
            data = response.json()
            
            # Verify Perrier-specific expectations
            issues = []
            
            # Water should be unprocessed or minimally processed
            if data['processing_level'] not in ["Unprocessed", "Minimally processed"]:
                issues.append(f"Processing level is '{data['processing_level']}', expected 'Unprocessed' or 'Minimally processed'")
            
            # Should have high diabetic score (water is diabetic-friendly)
            if data['diabetic_score'] < 4.0:
                issues.append(f"Diabetic score is {data['diabetic_score']}, expected ≥4.0 for water")
            
            # Check product name
            if "perrier" not in data['product_name'].lower():
                issues.append(f"Product name '{data['product_name']}' doesn't contain 'perrier'")
            
            if issues:
                self.log_test("Perrier Analysis", False, "; ".join(issues))
            else:
                self.log_test("Perrier Analysis", True,
                            f"Processing: {data['processing_level']}, Diabetic: {data['diabetic_score']:.1f}, Nutrition: {data['nutrition_score']:.1f}")
                
        except Exception as e:
            self.log_test("Perrier Analysis", False, f"Exception: {str(e)}")
    
    def test_analyze_product_third(self):
        """Test third product analysis"""
        try:
            barcode = "8712566451111"
            response = self.session.post(
                f"{self.base_url}/analyze-product",
                json={"barcode": barcode},
                timeout=30
            )
            
            if response.status_code != 200:
                self.log_test("Third Product Analysis", False, f"HTTP {response.status_code}: {response.text}")
                return
            
            data = response.json()
            
            # Basic validation
            if not data.get('product_name') or data['product_name'] == 'Unknown Product':
                self.log_test("Third Product Analysis", False, "Product name is missing or unknown")
                return
            
            # Check scores are in valid range
            if not (1.0 <= data['nutrition_score'] <= 5.0):
                self.log_test("Third Product Analysis", False, f"Nutrition score {data['nutrition_score']} out of range 1-5")
                return
                
            if not (1.0 <= data['diabetic_score'] <= 5.0):
                self.log_test("Third Product Analysis", False, f"Diabetic score {data['diabetic_score']} out of range 1-5")
                return
            
            self.log_test("Third Product Analysis", True,
                        f"Product: {data['product_name']}, Processing: {data['processing_level']}")
                
        except Exception as e:
            self.log_test("Third Product Analysis", False, f"Exception: {str(e)}")
    
    def test_invalid_barcode(self):
        """Test error handling for invalid barcode"""
        try:
            response = self.session.post(
                f"{self.base_url}/analyze-product",
                json={"barcode": "invalid123"},
                timeout=30
            )
            
            if response.status_code == 404:
                self.log_test("Invalid Barcode Handling", True, "Correctly returned 404 for invalid barcode")
            else:
                self.log_test("Invalid Barcode Handling", False, f"Expected 404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Barcode Handling", False, f"Exception: {str(e)}")
    
    def test_nonexistent_product(self):
        """Test error handling for non-existent product"""
        try:
            # Use a valid barcode format but non-existent product
            response = self.session.post(
                f"{self.base_url}/analyze-product",
                json={"barcode": "9999999999999"},
                timeout=30
            )
            
            if response.status_code == 404:
                self.log_test("Non-existent Product Handling", True, "Correctly returned 404 for non-existent product")
            else:
                self.log_test("Non-existent Product Handling", False, f"Expected 404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Non-existent Product Handling", False, f"Exception: {str(e)}")
    
    def test_scan_history(self):
        """Test scan history endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/scan-history", timeout=30)
            
            if response.status_code != 200:
                self.log_test("Scan History", False, f"HTTP {response.status_code}: {response.text}")
                return
            
            data = response.json()
            
            if not isinstance(data, list):
                self.log_test("Scan History", False, "Response is not a list")
                return
            
            # If we have history, validate structure
            if data:
                first_item = data[0]
                required_fields = ['id', 'barcode', 'product_name', 'nutrition_score', 
                                 'diabetic_score', 'processing_level', 'scanned_at']
                missing_fields = [field for field in required_fields if field not in first_item]
                if missing_fields:
                    self.log_test("Scan History", False, f"Missing fields in history item: {missing_fields}")
                    return
            
            self.log_test("Scan History", True, f"Retrieved {len(data)} history items")
                
        except Exception as e:
            self.log_test("Scan History", False, f"Exception: {str(e)}")
    
    def test_cached_analysis(self):
        """Test cached analysis retrieval"""
        try:
            # First analyze a product to ensure it's cached
            barcode = "3017620422003"
            self.session.post(
                f"{self.base_url}/analyze-product",
                json={"barcode": barcode},
                timeout=30
            )
            
            # Now try to retrieve cached analysis
            response = self.session.get(f"{self.base_url}/product/{barcode}", timeout=30)
            
            if response.status_code != 200:
                self.log_test("Cached Analysis", False, f"HTTP {response.status_code}: {response.text}")
                return
            
            data = response.json()
            
            if data.get('barcode') != barcode:
                self.log_test("Cached Analysis", False, f"Barcode mismatch: expected {barcode}, got {data.get('barcode')}")
                return
            
            self.log_test("Cached Analysis", True, f"Successfully retrieved cached analysis for {barcode}")
                
        except Exception as e:
            self.log_test("Cached Analysis", False, f"Exception: {str(e)}")
    
    def test_algorithm_accuracy(self):
        """Test algorithm accuracy by analyzing known products"""
        try:
            # Test Nutella for algorithm accuracy
            response = self.session.post(
                f"{self.base_url}/analyze-product",
                json={"barcode": "3017620422003"},
                timeout=30
            )
            
            if response.status_code != 200:
                self.log_test("Algorithm Accuracy", False, "Could not get Nutella data for algorithm test")
                return
            
            data = response.json()
            issues = []
            
            # Check NOVA classification logic
            ingredients = data.get('ingredients', [])
            if ingredients:
                ingredients_text = ' '.join(ingredients).lower()
                ultra_indicators = ['sugar', 'palm oil', 'lecithin', 'vanillin']
                found_indicators = [ind for ind in ultra_indicators if ind in ingredients_text]
                
                if len(found_indicators) >= 2 and data['processing_level'] != "Ultra-processed":
                    issues.append(f"NOVA classification error: found {found_indicators} but classified as {data['processing_level']}")
            
            # Check diabetic scoring logic
            nutritional_info = data.get('nutritional_info', {})
            sugars = nutritional_info.get('sugars', 0) or 0
            if sugars > 15 and data['diabetic_score'] > 3.0:
                issues.append(f"Diabetic scoring error: {sugars}g sugar but score is {data['diabetic_score']}")
            
            # Check WHO compliance
            who_compliance = data.get('who_compliance', {})
            if sugars > 5 and who_compliance.get('sugar', True):
                issues.append(f"WHO sugar compliance error: {sugars}g sugar but marked as compliant")
            
            if issues:
                self.log_test("Algorithm Accuracy", False, "; ".join(issues))
            else:
                self.log_test("Algorithm Accuracy", True, "All algorithm checks passed")
                
        except Exception as e:
            self.log_test("Algorithm Accuracy", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("FOOD ANALYZER BACKEND COMPREHENSIVE TESTING")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print()
        
        # Test analyze-product endpoint with specific barcodes
        print("Testing analyze-product endpoint...")
        self.test_analyze_product_nutella()
        self.test_analyze_product_perrier()
        self.test_analyze_product_third()
        
        # Test error handling
        print("Testing error handling...")
        self.test_invalid_barcode()
        self.test_nonexistent_product()
        
        # Test other endpoints
        print("Testing other endpoints...")
        self.test_scan_history()
        self.test_cached_analysis()
        
        # Test algorithm accuracy
        print("Testing algorithm accuracy...")
        self.test_algorithm_accuracy()
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['passed'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"❌ {result['test']}: {result['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = FoodAnalyzerTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)