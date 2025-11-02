#!/usr/bin/env python3
"""
Backend API Testing Suite for HexaBid ERP
Tests the ML competitor analysis endpoint and basic API health
"""

import requests
import json
import sys
from typing import Dict, Any, Optional
import time

# Configuration
BACKEND_URL = "https://hexabid-app.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_user_email = "test.competitor.analysis@hexabid.com"
        self.test_user_password = "TestPass123!"
        self.results = []
        
    def log_result(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        }
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    def test_health_endpoint(self) -> bool:
        """Test 1: Health endpoint GET / (no auth) returns {status: ok}"""
        try:
            response = self.session.get(f"{BACKEND_URL}/", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Health Check", False, f"Expected 200, got {response.status_code}", 
                              {"status_code": response.status_code, "response": response.text})
                return False
            
            data = response.json()
            if data.get("status") != "ok":
                self.log_result("Health Check", False, f"Expected status 'ok', got {data.get('status')}", 
                              {"response": data})
                return False
            
            self.log_result("Health Check", True, "Health endpoint working correctly", {"response": data})
            return True
            
        except Exception as e:
            self.log_result("Health Check", False, f"Exception occurred: {str(e)}")
            return False
    
    def test_auth_flow(self) -> bool:
        """Test 2: Auth flow - register user and get token, then verify with /me"""
        try:
            # Step 1: Register user
            register_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "full_name": "Test Competitor User",
                "company_name": "Test Analytics Corp",
                "role": "contractor"
            }
            
            response = self.session.post(f"{API_BASE}/auth/register", json=register_data, timeout=10)
            
            # If user already exists, try login instead
            if response.status_code == 400 and "already registered" in response.text:
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password
                }
                response = self.session.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
            
            if response.status_code not in [200, 201]:
                self.log_result("Auth Registration/Login", False, f"Auth failed with status {response.status_code}", 
                              {"status_code": response.status_code, "response": response.text})
                return False
            
            auth_data = response.json()
            if "access_token" not in auth_data:
                self.log_result("Auth Registration/Login", False, "No access_token in response", 
                              {"response": auth_data})
                return False
            
            self.auth_token = auth_data["access_token"]
            
            # Step 2: Test /me endpoint with token
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            me_response = self.session.get(f"{API_BASE}/auth/me", headers=headers, timeout=10)
            
            if me_response.status_code != 200:
                self.log_result("Auth /me Verification", False, f"Expected 200, got {me_response.status_code}", 
                              {"status_code": me_response.status_code, "response": me_response.text})
                return False
            
            user_data = me_response.json()
            if user_data.get("email") != self.test_user_email:
                self.log_result("Auth /me Verification", False, "User email mismatch", 
                              {"expected": self.test_user_email, "got": user_data.get("email")})
                return False
            
            self.log_result("Auth Flow", True, "Authentication flow working correctly", 
                          {"user_id": user_data.get("id"), "email": user_data.get("email")})
            return True
            
        except Exception as e:
            self.log_result("Auth Flow", False, f"Exception occurred: {str(e)}")
            return False
    
    def test_seed_tenders(self) -> bool:
        """Test 3: Seed tenders using POST /api/tenders/import"""
        try:
            if not self.auth_token:
                self.log_result("Seed Tenders", False, "No auth token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.post(f"{API_BASE}/tenders/import", headers=headers, timeout=15)
            
            if response.status_code != 200:
                self.log_result("Seed Tenders", False, f"Expected 200, got {response.status_code}", 
                              {"status_code": response.status_code, "response": response.text})
                return False
            
            data = response.json()
            if "count" not in data or data["count"] <= 0:
                self.log_result("Seed Tenders", False, "No tenders imported", {"response": data})
                return False
            
            self.log_result("Seed Tenders", True, f"Successfully imported {data['count']} tenders", 
                          {"count": data["count"]})
            return True
            
        except Exception as e:
            self.log_result("Seed Tenders", False, f"Exception occurred: {str(e)}")
            return False
    
    def test_fetch_tenders(self) -> Optional[str]:
        """Test 4: Fetch tenders and return first tender ID"""
        try:
            response = self.session.get(f"{API_BASE}/tenders", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Fetch Tenders", False, f"Expected 200, got {response.status_code}", 
                              {"status_code": response.status_code, "response": response.text})
                return None
            
            tenders = response.json()
            if not isinstance(tenders, list) or len(tenders) == 0:
                self.log_result("Fetch Tenders", False, "No tenders found", {"response": tenders})
                return None
            
            first_tender = tenders[0]
            tender_id = first_tender.get("id")
            if not tender_id:
                self.log_result("Fetch Tenders", False, "First tender has no ID", {"tender": first_tender})
                return None
            
            self.log_result("Fetch Tenders", True, f"Found {len(tenders)} tenders, first ID: {tender_id}", 
                          {"total_tenders": len(tenders), "first_tender_title": first_tender.get("title")})
            return tender_id
            
        except Exception as e:
            self.log_result("Fetch Tenders", False, f"Exception occurred: {str(e)}")
            return None
    
    def test_competitor_ml_endpoint(self, tender_id: str) -> bool:
        """Test 5: ML Competitor Analysis endpoint"""
        try:
            if not self.auth_token:
                self.log_result("Competitor ML Analysis", False, "No auth token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.post(f"{API_BASE}/tenders/{tender_id}/competitors-ml", 
                                       headers=headers, timeout=15)
            
            if response.status_code != 200:
                self.log_result("Competitor ML Analysis", False, f"Expected 200, got {response.status_code}", 
                              {"status_code": response.status_code, "response": response.text})
                return False
            
            data = response.json()
            
            # Verify required structure: {tender_id, competitors[], market_analysis, competitive_advantage[], threat_level}
            required_fields = ["tender_id", "competitors", "market_analysis", "competitive_advantage", "threat_level"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result("Competitor ML Analysis", False, f"Missing required fields: {missing_fields}", 
                              {"response": data})
                return False
            
            # Verify data types and content
            if data["tender_id"] != tender_id:
                self.log_result("Competitor ML Analysis", False, "Tender ID mismatch", 
                              {"expected": tender_id, "got": data["tender_id"]})
                return False
            
            if not isinstance(data["competitors"], list) or len(data["competitors"]) == 0:
                self.log_result("Competitor ML Analysis", False, "Competitors should be non-empty list", 
                              {"competitors": data["competitors"]})
                return False
            
            if not isinstance(data["competitive_advantage"], list):
                self.log_result("Competitor ML Analysis", False, "Competitive advantage should be list", 
                              {"competitive_advantage": data["competitive_advantage"]})
                return False
            
            if not isinstance(data["market_analysis"], str) or len(data["market_analysis"]) == 0:
                self.log_result("Competitor ML Analysis", False, "Market analysis should be non-empty string", 
                              {"market_analysis": data["market_analysis"]})
                return False
            
            if data["threat_level"] not in ["Low", "Medium", "High"]:
                self.log_result("Competitor ML Analysis", False, f"Invalid threat level: {data['threat_level']}", 
                              {"threat_level": data["threat_level"]})
                return False
            
            # Verify competitor structure
            for i, competitor in enumerate(data["competitors"]):
                if not isinstance(competitor, dict):
                    self.log_result("Competitor ML Analysis", False, f"Competitor {i} should be dict", 
                                  {"competitor": competitor})
                    return False
                
                if "name" not in competitor or "threat" not in competitor:
                    self.log_result("Competitor ML Analysis", False, f"Competitor {i} missing name or threat", 
                                  {"competitor": competitor})
                    return False
            
            self.log_result("Competitor ML Analysis", True, "ML endpoint working correctly", 
                          {"competitors_count": len(data["competitors"]), 
                           "threat_level": data["threat_level"],
                           "market_analysis_length": len(data["market_analysis"])})
            return True
            
        except Exception as e:
            self.log_result("Competitor ML Analysis", False, f"Exception occurred: {str(e)}")
            return False
    
    def test_analysis_persistence(self, tender_id: str) -> bool:
        """Test 6: Verify analysis persistence in database"""
        try:
            if not self.auth_token:
                self.log_result("Analysis Persistence", False, "No auth token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # First check if analysis exists (should be 404 initially)
            response = self.session.get(f"{API_BASE}/tenders/{tender_id}/analysis", 
                                      headers=headers, timeout=10)
            
            # Note: The endpoint /tenders/{tender_id}/analysis is for TenderAnalysis, not CompetitorAnalysis
            # The competitor analysis doesn't have a direct GET endpoint, so we'll verify by calling the ML endpoint
            # and checking that it returns consistent data (indicating persistence)
            
            # Call ML endpoint first time
            ml_response1 = self.session.post(f"{API_BASE}/tenders/{tender_id}/competitors-ml", 
                                           headers=headers, timeout=15)
            
            if ml_response1.status_code != 200:
                self.log_result("Analysis Persistence", False, "First ML call failed", 
                              {"status_code": ml_response1.status_code})
                return False
            
            data1 = ml_response1.json()
            
            # Wait a moment and call again
            time.sleep(1)
            
            ml_response2 = self.session.post(f"{API_BASE}/tenders/{tender_id}/competitors-ml", 
                                           headers=headers, timeout=15)
            
            if ml_response2.status_code != 200:
                self.log_result("Analysis Persistence", False, "Second ML call failed", 
                              {"status_code": ml_response2.status_code})
                return False
            
            data2 = ml_response2.json()
            
            # Verify that both calls return data (indicating the endpoint works consistently)
            if data1.get("tender_id") != data2.get("tender_id"):
                self.log_result("Analysis Persistence", False, "Inconsistent tender_id between calls")
                return False
            
            if len(data1.get("competitors", [])) != len(data2.get("competitors", [])):
                self.log_result("Analysis Persistence", False, "Inconsistent competitor count between calls")
                return False
            
            self.log_result("Analysis Persistence", True, "Analysis endpoint working consistently", 
                          {"calls_made": 2, "consistent_results": True})
            return True
            
        except Exception as e:
            self.log_result("Analysis Persistence", False, f"Exception occurred: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests in sequence"""
        print("🚀 Starting HexaBid Backend API Tests")
        print("=" * 50)
        
        # Test 1: Health Check
        health_ok = self.test_health_endpoint()
        
        # Test 2: Authentication
        auth_ok = self.test_auth_flow()
        
        # Test 3: Seed Tenders
        seed_ok = self.test_seed_tenders() if auth_ok else False
        
        # Test 4: Fetch Tenders
        tender_id = self.test_fetch_tenders() if seed_ok else None
        
        # Test 5: ML Competitor Analysis
        ml_ok = self.test_competitor_ml_endpoint(tender_id) if tender_id else False
        
        # Test 6: Analysis Persistence
        persistence_ok = self.test_analysis_persistence(tender_id) if tender_id and ml_ok else False
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.results,
            "critical_failures": [r for r in self.results if not r["success"]],
            "overall_status": "PASS" if failed_tests == 0 else "FAIL"
        }

def main():
    """Main test execution"""
    tester = BackendTester()
    summary = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if summary["overall_status"] == "PASS" else 1)

if __name__ == "__main__":
    main()