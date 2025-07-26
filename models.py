from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

# Enums
class HOSPITAL_TYPE(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    GENERAL = "GENERAL"
    SPECIALIZED = "SPECIALIZED"
    CHILDREN = "CHILDREN"
    MATERNITY = "MATERNITY"
    RESEARCH = "RESEARCH"
    REHABILITATION = "REHABILITATION"

class COST_RANGE(str, Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"

class TEST_TYPE(str, Enum):
    BLOOD = "BLOOD"
    HEART = "HEART"
    BRAIN = "BRAIN"
    LUNG = "LUNG"
    EYE = "EYE"
    BONE = "BONE"
    SKIN = "SKIN"
    GENERAL = "GENERAL"
    LIVER = "LIVER"
    KIDNEY = "KIDNEY"

class LOCATION_TYPE(str, Enum):
    URBAN = "URBAN"
    RURAL = "RURAL"
    SUBURBAN = "SUBURBAN"

class FEEDBACK_TARGET_TYPE(str, Enum):
    DOCTOR = "DOCTOR"
    HOSPITAL = "HOSPITAL"

# Data Models
class LocationResponse(BaseModel):
    id: int
    locationType: Optional[LOCATION_TYPE]
    address: Optional[str]
    thana: Optional[str]
    po: Optional[str]
    city: Optional[str]
    postalCode: Optional[int]
    zoneId: Optional[int]
    # For test service, sometimes division/district/upazila are used
    division: Optional[str] = None
    district: Optional[str] = None
    upazila: Optional[str] = None

class HospitalResponse(BaseModel):
    id: int
    name: str
    phoneNumber: Optional[str]
    website: Optional[str]
    types: List[HOSPITAL_TYPE]
    icus: Optional[int]
    costRange: COST_RANGE
    latitude: Optional[float]
    longitude: Optional[float]
    locationResponse: LocationResponse

class TestResponse(BaseModel):
    id: int
    name: str
    types: List[TEST_TYPE]
    price: float
    hospitalResponse: HospitalResponse

class FeedbackResponse(BaseModel):
    id: int
    userId: str
    targetType: FEEDBACK_TARGET_TYPE
    targetId: int
    rating: int
    comment: str
    createdAt: str

class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: str

class DoctorHospitalResponse(BaseModel):
    id: int
    hospitalId: int
    hospitalName: str
    appointmentFee: float
    weeklySchedules: List[str]
    appointmentTimes: List[str]

class DoctorResponse(BaseModel):
    id: int
    name: str
    specialties: List[str]
    phoneNumber: str
    email: str
    departmentResponse: DepartmentResponse
    locationResponse: LocationResponse
    doctorHospitals: List[DoctorHospitalResponse]

class PageSort(BaseModel):
    sorted: bool
    unsorted: bool
    empty: bool

class Pageable(BaseModel):
    sort: PageSort
    pageNumber: int
    pageSize: int
    offset: int
    paged: bool
    unpaged: bool

class PageResponse(BaseModel):
    content: List[HospitalResponse]
    pageable: Pageable
    totalElements: int
    totalPages: int
    last: bool
    first: bool
    numberOfElements: int
    size: int
    number: int
    sort: PageSort
    empty: bool

# Location Request Model
class Location(BaseModel):
    id: Optional[int] = None
    locationType: LOCATION_TYPE
    address: Optional[str] = None
    thana: Optional[str] = None
    po: Optional[str] = None
    city: str
    postalCode: int
    zoneId: int

# Request Models
class ChatRequest(BaseModel):
    message: str
    user_location: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    hospitals: Optional[List[HospitalResponse]] = None
    tests: Optional[List[TestResponse]] = None

class FeedbackCreateRequest(BaseModel):
    userId: str
    targetType: FEEDBACK_TARGET_TYPE
    targetId: int
    rating: int
    comment: Optional[str] = None

class FeedbackUpdateRequest(BaseModel):
    userId: str
    rating: Optional[int] = None
    comment: Optional[str] = None

class DoctorHospitalCreateRequest(BaseModel):
    hospitalId: int
    appointmentFee: Optional[float] = None
    weeklySchedules: Optional[List[str]] = None
    appointmentTimes: Optional[List[str]] = None
    
