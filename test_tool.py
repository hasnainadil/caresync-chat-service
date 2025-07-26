from tools import (
    hospital_search_tool, 
    get_test_by_id_tool, 
    get_tests_by_type_tool, 
    get_tests_by_hospital_tool,
    get_hospital_feedbacks_tool,
    doctor_search_tool
)
import json

def parse_if_json(result):
    """Helper function to parse result as JSON if possible"""
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return result

def test_hospital_search():
    print("=" * 50)
    print("TESTING HOSPITAL SEARCH TOOL")
    print("=" * 50)
    
    # Test 1: Search by test types and cost ranges
    print("\n1. Search by test types and cost ranges:")
    result = hospital_search_tool.invoke({
        "test_types": ["BLOOD"],
        "cost_ranges": ["HIGH"]
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 2: Search by hospital types
    print("\n2. Search by hospital types:")
    result = hospital_search_tool.invoke({
        "hospital_types": ["PUBLIC", "GENERAL"]
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 3: Search by city
    print("\n3. Search by city:")
    result = hospital_search_tool.invoke({
        "city": "Dhaka"
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 4: Search by hospital name
    print("\n4. Search by hospital name:")
    result = hospital_search_tool.invoke({
        "hospital_name": "General Hospital"
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 5: Search with ICU minimum
    print("\n5. Search with ICU minimum:")
    result = hospital_search_tool.invoke({
        "icu_min": 10
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 6: Get all hospitals (no filters)
    print("\n6. Get all hospitals (no filters):")
    result = hospital_search_tool.invoke({})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result length: {len(parsed_result) if isinstance(parsed_result, list) else 'N/A'}")

def test_get_test_by_id():
    print("\n" + "=" * 50)
    print("TESTING GET TEST BY ID TOOL")
    print("=" * 50)
    
    # Test 1: Valid test ID
    print("\n1. Get test by ID 1:")
    result = get_test_by_id_tool.invoke({"id": 1})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 2: Another test ID
    print("\n2. Get test by ID 2:")
    result = get_test_by_id_tool.invoke({"id": 2})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")

def test_get_tests_by_type():
    print("\n" + "=" * 50)
    print("TESTING GET TESTS BY TYPE TOOL")
    print("=" * 50)
    
    # Test 1: Blood tests
    print("\n1. Get BLOOD tests:")
    result = get_tests_by_type_tool.invoke({"type": "BLOOD"})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 2: Heart tests
    print("\n2. Get HEART tests:")
    result = get_tests_by_type_tool.invoke({"type": "HEART"})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 3: Test with typo
    print("\n3. Get tests with typo (BLOD instead of BLOOD):")
    result = get_tests_by_type_tool.invoke({"type": "BLOD"})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")

def test_get_tests_by_hospital():
    print("\n" + "=" * 50)
    print("TESTING GET TESTS BY HOSPITAL TOOL")
    print("=" * 50)
    
    # Test 1: By hospital ID
    print("\n1. Get tests by hospital ID 1:")
    result = get_tests_by_hospital_tool.invoke({"hospitalId": 1})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 2: By hospital name
    print("\n2. Get tests by hospital name:")
    result = get_tests_by_hospital_tool.invoke({"hospitalName": "General Hospital"})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 3: By hospital name with typo
    print("\n3. Get tests by hospital name with typo:")
    result = get_tests_by_hospital_tool.invoke({"hospitalName": "Genral Hospitl"})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 4: No parameters (should return error)
    print("\n4. No parameters (should return error):")
    result = get_tests_by_hospital_tool.invoke({})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")

def test_get_hospital_feedbacks():
    print("\n" + "=" * 50)
    print("TESTING GET HOSPITAL FEEDBACKS TOOL")
    print("=" * 50)
    
    # Test 1: By hospital ID
    print("\n1. Get feedbacks by hospital ID 1:")
    result = get_hospital_feedbacks_tool.invoke({"hospitalId": 1})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 2: By hospital name
    print("\n2. Get feedbacks by hospital name:")
    result = get_hospital_feedbacks_tool.invoke({"hospitalName": "General Hospital"})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 3: By hospital name with typo
    print("\n3. Get feedbacks by hospital name with typo:")
    result = get_hospital_feedbacks_tool.invoke({"hospitalName": "Genral Hospitl"})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 4: No parameters (should return error)
    print("\n4. No parameters (should return error):")
    result = get_hospital_feedbacks_tool.invoke({})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")

def test_doctor_search():
    print("\n" + "=" * 50)
    print("TESTING DOCTOR SEARCH TOOL")
    print("=" * 50)
    
    # Test 1: Search by specialties
    print("\n1. Search by specialties:")
    result = doctor_search_tool.invoke({
        "specialties": ["Cardiology", "Internal Medicine"]
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 2: Search by department
    print("\n2. Search by department:")
    result = doctor_search_tool.invoke({
        "department": "Surgery Department"
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 3: Search by doctor name
    print("\n3. Search by doctor name:")
    result = doctor_search_tool.invoke({
        "doctor_name": "Dr. Smith"
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 4: Search by city
    print("\n4. Search by city:")
    result = doctor_search_tool.invoke({
        "city": "New York"
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 5: Search by hospital name
    print("\n5. Search by hospital name:")
    result = doctor_search_tool.invoke({
        "hospital_name": "General Hospital"
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 6: Combined search
    print("\n6. Combined search (specialties + city):")
    result = doctor_search_tool.invoke({
        "specialties": ["Cardiology"],
        "city": "New York"
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 7: Search with typos
    print("\n7. Search with typos:")
    result = doctor_search_tool.invoke({
        "specialties": ["Cardiolgy"],  # Typo in Cardiology
        "department": "Surgry Dept"    # Typo in Surgery Department
    })
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result: {parsed_result}")
    
    # Test 8: Get all doctors (no filters)
    print("\n8. Get all doctors (no filters):")
    result = doctor_search_tool.invoke({})
    parsed_result = parse_if_json(result)
    print(f"Result type: {type(parsed_result)}")
    print(f"Result length: {len(parsed_result) if isinstance(parsed_result, list) else 'N/A'}")

def run_all_tests():
    """Run all tool tests"""
    try:
        test_hospital_search()
        test_get_test_by_id()
        test_get_tests_by_type()
        test_get_tests_by_hospital()
        test_get_hospital_feedbacks()
        test_doctor_search()
        
        print("\n" + "=" * 50)
        print("ALL TESTS COMPLETED")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()