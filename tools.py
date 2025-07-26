import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage
from models import HOSPITAL_TYPE, COST_RANGE, TEST_TYPE, HospitalResponse, TestResponse
from typing import Any, Dict, Optional
import json
from rapidfuzz import process, fuzz
from typing import Annotated
from dotenv import load_dotenv

# --- Config ---
load_dotenv()
HOSPITAL_SERVICE_URL = os.getenv("HOSPITAL_SERVICE_URL")
TEST_SERVICE_URL = os.getenv("TEST_SERVICE_URL")
FEEDBACK_SERVICE_URL = os.getenv("FEEDBACK_SERVICE_URL")
DOCTOR_SERVICE_URL = os.getenv("DOCTOR_SERVICE_URL")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not HOSPITAL_SERVICE_URL or not TEST_SERVICE_URL or not FEEDBACK_SERVICE_URL or not DOCTOR_SERVICE_URL or not GOOGLE_API_KEY:
    raise ValueError("HOSPITAL_SERVICE_URL, TEST_SERVICE_URL, FEEDBACK_SERVICE_URL, DOCTOR_SERVICE_URL, and GOOGLE_API_KEY must be set")


# --- Tool Functions ---

def intersect_hospitals(lists):
    if not lists:
        return []
    sets = [set(h['id'] for h in l) for l in lists if l]
    if not sets:
        return []
    common_ids = set.intersection(*sets)
    id_to_hospital = {h['id']: h for l in lists for h in l}
    return [id_to_hospital[i] for i in common_ids]

# Helper for fuzzy enum matching
def fuzzy_enum_match(value: str, choices: list, threshold: int = 80) -> Optional[str]:
    match, score, _ = process.extractOne(value, choices, scorer=fuzz.ratio)
    if score >= threshold:
        return match
    return None

@tool("hospital_search", return_direct=False)
def hospital_search_tool(
    test_types: Annotated[Optional[List[str]], "Array of test types to filter hospitals by (e.g., BLOOD, HEART, etc). Typos allowed."] = None,
    cost_ranges: Annotated[Optional[List[str]], "Array of cost ranges to filter hospitals by (e.g., LOW, MODERATE, HIGH, etc). Typos allowed."] = None,
    hospital_types: Annotated[Optional[List[str]], "Array of hospital types to filter by (e.g., GENERAL, PUBLIC, PRIVATE, etc). Typos allowed."] = None,
    icu_min: Annotated[Optional[int], "Minimum number of ICU units required."] = None,
    city: Annotated[Optional[str], "City name to filter hospitals by. Typos allowed."] = None,
    thana: Annotated[Optional[str], "Thana/Upazila to filter hospitals by. Typos allowed."] = None,
    po: Annotated[Optional[str], "Post office to filter hospitals by. Typos allowed."] = None,
    zone_id: Annotated[Optional[int], "Zone ID to filter hospitals by."] = None,
    latitude: Annotated[Optional[float], "Latitude for proximity search."] = None,
    longitude: Annotated[Optional[float], "Longitude for proximity search."] = None,
    radius_km: Annotated[Optional[float], "Radius in kilometers for proximity search."] = None,
    hospital_name: Annotated[Optional[str], "Hospital name to filter by. Typos allowed."] = None,
    top_n: Annotated[Optional[int], "Number of hospitals to return."] = 5,
) -> str:
    """
    Search for hospitals by test types, cost ranges, hospital types, ICU count, city, thana, post office, zone, hospital name, or location proximity.
    All arguments are optional and can be arrays (for test_types, cost_ranges, hospital_types). Typos are tolerated for string fields and enums.
    """
    client = httpx.Client()
    hospital_sets = []
    # 1. Fuzzy match test_types to valid enums
    valid_test_types = [e.value for e in TEST_TYPE]
    if test_types:
        matched_types = []
        for t in test_types:
            m = fuzzy_enum_match(t, valid_test_types)
            if m:
                matched_types.append(m)
        test_types = matched_types
    # 2. Fuzzy match cost_ranges to valid enums
    valid_cost_ranges = [e.value for e in COST_RANGE]
    if cost_ranges:
        matched_ranges = []
        for c in cost_ranges:
            m = fuzzy_enum_match(c, valid_cost_ranges)
            if m:
                matched_ranges.append(m)
        cost_ranges = matched_ranges
    # 3. Fuzzy match hospital_types to valid enums
    valid_hospital_types = [e.value for e in HOSPITAL_TYPE]
    if hospital_types:
        matched_htypes = []
        for h in hospital_types:
            m = fuzzy_enum_match(h, valid_hospital_types)
            if m:
                matched_htypes.append(m)
        hospital_types = matched_htypes
    # 4. Filter by test types (get hospitals for each test type)
    if test_types:
        hospitals_by_test = []
        for ttype in test_types:
            resp = client.get(f"{TEST_SERVICE_URL}/test/v1/type/{ttype}")
            if 200 <= resp.status_code < 300:
                tests = resp.json()
                hospitals = [test['hospitalResponse'] for test in tests if 'hospitalResponse' in test]
                hospitals_by_test.append(hospitals)
        if hospitals_by_test:
            flat = [h for sub in hospitals_by_test for h in sub]
            by_id = {h['id']: h for h in flat}
            hospital_sets.append(list(by_id.values()))
    # 5. Filter by cost ranges
    if cost_ranges:
        hospitals_by_cost = []
        for crange in cost_ranges:
            resp = client.get(f"{HOSPITAL_SERVICE_URL}/hospital/v1/cost-range/{crange}")
            if 200 <= resp.status_code < 300:
                hospitals_by_cost.append(resp.json())
        if hospitals_by_cost:
            flat = [h for sub in hospitals_by_cost for h in sub]
            by_id = {h['id']: h for h in flat}
            hospital_sets.append(list(by_id.values()))
    # 6. Filter by hospital types
    if hospital_types:
        hospitals_by_type = []
        for htype in hospital_types:
            resp = client.get(f"{HOSPITAL_SERVICE_URL}/hospital/v1/type/{htype}")
            if 200 <= resp.status_code < 300:
                hospitals_by_type.append(resp.json())
        if hospitals_by_type:
            flat = [h for sub in hospitals_by_type for h in sub]
            by_id = {h['id']: h for h in flat}
            hospital_sets.append(list(by_id.values()))
    # 7. If no filters, get all hospitals
    if not hospital_sets or len(hospital_sets) == 0:
        resp = client.get(f"{HOSPITAL_SERVICE_URL}/hospital/v1/all")
        if 200 <= resp.status_code < 300:
            hospital_sets.append(resp.json())
    # 8. Intersect all sets
    hospitals = intersect_hospitals(hospital_sets)
    # 9. Further filter by icu_min, city, thana, po, zone_id, hospital_name, location
    def hospital_filter(h):
        if icu_min is not None and (h.get('icus') is None or h['icus'] < icu_min):
            return False
        loc = h.get('locationResponse') or {}
        # Fuzzy match city
        if city and loc.get('city'):
            score = fuzz.ratio(city.lower(), loc.get('city', '').lower())
            if score < 80:
                return False
        if thana and loc.get('thana'):
            score = fuzz.ratio(thana.lower(), loc.get('thana', '').lower())
            if score < 80:
                return False
        if po and loc.get('po'):
            score = fuzz.ratio(po.lower(), loc.get('po', '').lower())
            if score < 80:
                return False
        if zone_id and loc.get('zoneId') != zone_id:
            return False
        # Fuzzy match hospital name
        if hospital_name and h.get('name'):
            score = fuzz.ratio(hospital_name.lower(), h.get('name', '').lower())
            if score < 80:
                return False
        # Optionally, filter by lat/lon/radius
        if latitude is not None and longitude is not None and radius_km is not None:
            from math import radians, cos, sin, sqrt, atan2
            lat2 = h.get('latitude')
            lon2 = h.get('longitude')
            if lat2 is None or lon2 is None:
                return False
            R = 6371
            dlat = radians(latitude - lat2)
            dlon = radians(longitude - lon2)
            a = sin(dlat/2)**2 + cos(radians(lat2)) * cos(radians(latitude)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            dist = R * c
            if dist > radius_km:
                return False
        return True
    filtered = [h for h in hospitals if hospital_filter(h)]
    
    # Add feedback ratings to each hospital
    for hospital in filtered:
        hospital_id = hospital.get('id')
        if hospital_id:
            try:
                feedback_resp = client.get(f"{FEEDBACK_SERVICE_URL}/feedback/v1/hospital/{hospital_id}")
                if 200 <= feedback_resp.status_code < 300:
                    feedbacks = feedback_resp.json()
                    ratings = [feedback.get('rating') for feedback in feedbacks if feedback.get('rating') is not None]
                    hospital['ratings'] = ratings
                    # Calculate average rating for sorting
                    hospital['averageRating'] = sum(ratings) / len(ratings) if ratings else 0
                else:
                    hospital['ratings'] = []
                    hospital['averageRating'] = 0
            except Exception:
                hospital['ratings'] = []
                hospital['averageRating'] = 0
        else:
            hospital['ratings'] = []
            hospital['averageRating'] = 0
    
    # Sort by average rating (highest first) and take top_n
    filtered_sorted = sorted(filtered, key=lambda h: h.get('averageRating', 0), reverse=True)[:top_n]
    
    
    client.close()
    return json.dumps(filtered_sorted)

@tool("get_test_by_id", return_direct=False)
def get_test_by_id_tool(
    id: Annotated[int, "The unique identifier of the test."]
) -> str:
    """Get test details by test ID."""
    url = f"{TEST_SERVICE_URL}/test/v1/id/{id}"
    resp = httpx.get(url)
    if not (200 <= resp.status_code < 300):
        return f"Error: {resp.status_code}"
    return resp.text

@tool("get_tests_by_type", return_direct=False)
def get_tests_by_type_tool(
    type: Annotated[str, "Type of medical test (e.g., BLOOD, HEART, GENERAL, etc). Typos allowed."]
) -> str:
    """Get tests by type."""
    url = f"{TEST_SERVICE_URL}/test/v1/type/{type}"
    resp = httpx.get(url)
    if not (200 <= resp.status_code < 300):
        return f"Error: {resp.status_code}"
    return resp.text

@tool("get_tests_by_hospital_name_or_id", return_direct=False)
def get_tests_by_hospital_tool(
    hospitalId: Annotated[Optional[int], "The unique identifier of the hospital."] = None,
    hospitalName: Annotated[Optional[str], "The name of the hospital."] = None
) -> str:
    """Get all tests offered by a specific hospital. Either hospitalId or hospitalName must be provided."""
    if hospitalId is None and hospitalName is None:
        return "Error: Either hospitalId or hospitalName must be provided "
    res = None
    if hospitalId is not None:
        url = f"{TEST_SERVICE_URL}/test/v1/hospital/{hospitalId}"
        res = httpx.get(url)
    elif hospitalName is not None:
        hospitals = httpx.get(f"{HOSPITAL_SERVICE_URL}/hospital/v1/all").json()
        match = process.extractOne(hospitalName, [h['name'] for h in hospitals], scorer=fuzz.ratio)
        if match[1] < 80:
            return f"Error: No hospital found matching '{hospitalName}'"
        closest_hospital_name = match[0]
        closest_hospital = next((h for h in hospitals if h['name'] == closest_hospital_name), None)
        if closest_hospital is None:
            return f"Error: No hospital found matching '{hospitalName}'"
        url = f"{TEST_SERVICE_URL}/test/v1/hospital/{closest_hospital['id']}"
        res = httpx.get(url)
    if res is None or not (200 <= res.status_code < 300):
        return f"Error: {res.status_code if res else 'No response from server'}"
    return res.text

@tool("get_hospital_feedbacks", return_direct=False)
def get_hospital_feedbacks_tool(
    hospitalId: Annotated[Optional[int], "The unique identifier of the hospital."] = None,
    hospitalName: Annotated[Optional[str], "The name of the hospital."] = None
) -> str:
    """Get all feedback entries for a specific hospital. Either hospitalId or hospitalName must be provided."""
    if hospitalId is None and hospitalName is None:
        return "Error: Either hospitalId or hospitalName must be provided"
    
    client = httpx.Client()
    try:
        target_hospital_id = hospitalId
        
        # If hospital name is provided, find the hospital ID
        if hospitalId is None and hospitalName is not None:
            hospitals_resp = client.get(f"{HOSPITAL_SERVICE_URL}/hospital/v1/all")
            if not (200 <= hospitals_resp.status_code < 300):
                return f"Error: Failed to fetch hospitals list. Status: {hospitals_resp.status_code}"
            
            hospitals = hospitals_resp.json()
            hospital_names = [h['name'] for h in hospitals]
            match = process.extractOne(hospitalName, hospital_names, scorer=fuzz.ratio)
            
            if match[1] < 80:
                return f"Error: No hospital found matching '{hospitalName}'"
            
            closest_hospital_name = match[0]
            closest_hospital = next((h for h in hospitals if h['name'] == closest_hospital_name), None)
            
            if closest_hospital is None:
                return f"Error: No hospital found matching '{hospitalName}'"
            
            target_hospital_id = closest_hospital['id']
        
        # Fetch feedbacks for the hospital
        feedback_resp = client.get(f"{FEEDBACK_SERVICE_URL}/feedback/v1/hospital/{target_hospital_id}")
        
        if not (200 <= feedback_resp.status_code < 300):
            return f"Error: Failed to fetch feedbacks. Status: {feedback_resp.status_code}"
        
        return feedback_resp.text
        
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        client.close()

@tool("doctor_search", return_direct=False)
def doctor_search_tool(
    specialties: Annotated[Optional[List[str]], "Array of medical specialties to filter doctors by (e.g., Cardiology, Internal Medicine, etc). Typos allowed."] = None,
    department: Annotated[Optional[str], "Department name to filter doctors by (e.g., Cardiology Department, Surgery Department, etc). Typos allowed."] = None,
    doctor_name: Annotated[Optional[str], "Doctor name to filter by. Typos allowed."] = None,
    city: Annotated[Optional[str], "City name to filter doctors by. Typos allowed."] = None,
    hospital_name: Annotated[Optional[str], "Hospital name to filter doctors by. Typos allowed."] = None,
    top_n: Annotated[Optional[int], "Number of doctors to return."] = 10,
) -> str:
    """
    Search for doctors by specialties, department, doctor name, city, or hospital affiliation.
    All arguments are optional. Specialties can be an array. Typos are tolerated for string fields.
    """
    client = httpx.Client()
    try:
        # Get all doctors from the service
        doctors_resp = client.get(f"{DOCTOR_SERVICE_URL}/doctor/v1/all")
        if not (200 <= doctors_resp.status_code < 300):
            return f"Error: Failed to fetch doctors. Status: {doctors_resp.status_code}"
        
        doctors = doctors_resp.json()
        
        # Filter doctors based on criteria
        def doctor_filter(doctor):
            # Filter by specialties (fuzzy match)
            if specialties:
                doctor_specialties = doctor.get('specialties', [])
                specialty_match = False
                for search_specialty in specialties:
                    for doctor_specialty in doctor_specialties:
                        score = fuzz.ratio(search_specialty.lower(), doctor_specialty.lower())
                        if score >= 80:
                            specialty_match = True
                            break
                    if specialty_match:
                        break
                if not specialty_match:
                    return False
            
            # Filter by department (fuzzy match)
            if department:
                dept_response = doctor.get('departmentResponse') or {}
                dept_name = dept_response.get('name', '')
                if dept_name:
                    score = fuzz.ratio(department.lower(), dept_name.lower())
                    if score < 80:
                        return False
                else:
                    return False
            
            # Filter by doctor name (fuzzy match)
            if doctor_name:
                name = doctor.get('name', '')
                if name:
                    score = fuzz.ratio(doctor_name.lower(), name.lower())
                    if score < 80:
                        return False
                else:
                    return False
            
            # Filter by city (fuzzy match)
            if city:
                location_response = doctor.get('locationResponse') or {}
                doctor_city = location_response.get('city', '')
                if doctor_city:
                    score = fuzz.ratio(city.lower(), doctor_city.lower())
                    if score < 80:
                        return False
                else:
                    return False
            
            # Filter by hospital name (fuzzy match)
            if hospital_name:
                doctor_hospitals = doctor.get('doctorHospitals') or []
                hospital_match = False
                for hospital in doctor_hospitals:
                    hospital_name_field = hospital.get('hospitalName', '')
                    if hospital_name_field:
                        score = fuzz.ratio(hospital_name.lower(), hospital_name_field.lower())
                        if score >= 80:
                            hospital_match = True
                            break
                if not hospital_match:
                    return False
            
            return True
        
        # Apply filters
        filtered_doctors = [doctor for doctor in doctors if doctor_filter(doctor)]
        
        # Limit results to top_n
        limited_doctors = filtered_doctors[:top_n]
        
        return json.dumps(limited_doctors)
        
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        client.close()
        


