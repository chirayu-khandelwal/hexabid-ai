from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
import random
import io
from PyPDF2 import PdfReader

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 43200))

# AI Client
EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY')

app = FastAPI(title="HexaBid ERP API")
api_router = APIRouter(prefix="/api")

# ===== MODELS =====

class UserRole(str):
    SUPER_ADMIN = "super_admin"
    CONTRACTOR = "contractor"
    VENDOR = "vendor"
    OEM = "oem"
    CONSULTANT = "consultant"

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    company_name: Optional[str] = None
    role: str = UserRole.CONTRACTOR
    is_active: bool = True
    kyc_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None
    role: str = UserRole.CONTRACTOR

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Tender(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tender_id: str
    title: str
    organization: str
    description: str
    estimated_value: float
    emd_amount: float
    category: str
    location: str
    published_date: datetime
    submission_deadline: datetime
    status: str = "active"
    source: str = "GeM"  # GeM, MSME, etc.
    eligibility_criteria: List[str] = []
    technical_specs: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TenderAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tender_id: str
    user_id: str
    key_requirements: List[str]
    risks: List[str]
    opportunities: List[str]
    compliance_gaps: List[str]
    estimated_effort: str
    ai_summary: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompetitorAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tender_id: str
    competitors: List[Dict[str, Any]]
    market_analysis: str
    competitive_advantage: List[str]
    threat_level: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WinPrediction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tender_id: str
    user_id: str
    win_probability: float
    confidence_score: float
    recommended_bid_margin: float
    factors: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BOQ(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tender_id: str
    user_id: str
    items: List[Dict[str, Any]]
    total_cost: float
    gst_amount: float
    grand_total: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CRMContact(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    type: str  # vendor, oem, client
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessage(BaseModel):
    tender_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    response: str
    tender_context: Optional[Dict[str, Any]] = None

class PriceAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tender_id: str
    historical_prices: List[Dict[str, Any]]
    average_price: float
    recommended_price: float
    price_trend: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductRecommendation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tender_id: str
    recommended_products: List[Dict[str, Any]]
    oem_suggestions: List[Dict[str, Any]]
    technical_compliance: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    type: str  # info, success, warning, danger
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SupportTicket(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    subject: str
    description: str
    category: str
    priority: str = "medium"
    status: str = "open"
    responses: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VendorPerformance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    vendor_name: str
    total_orders: int
    completed_orders: int
    on_time_delivery: float
    quality_rating: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Subscription(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    plan: str  # starter, professional, enterprise
    ai_credits: int
    start_date: datetime
    end_date: datetime
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ===== HELPER FUNCTIONS =====

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user_doc is None:
        raise credentials_exception
    if isinstance(user_doc['created_at'], str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    return User(**user_doc)

async def get_ai_chat() -> LlmChat:
    return LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=str(uuid.uuid4()),
        system_message="You are Hexa, an AI assistant for HexaBid ERP - a tender bidding system. Help users with tender analysis, bidding strategy, and answering questions about tenders and procurement."
    ).with_model("openai", "gpt-4o")

# Mock data generators
def generate_mock_tenders() -> List[Dict]:
    categories = ["IT Services", "Construction", "Medical Equipment", "Office Supplies", "Consulting"]
    organizations = ["Ministry of Health", "Public Works Department", "Railways", "Defense", "Education Department"]
    locations = ["New Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad"]
    
    tenders = []
    for i in range(20):
        tender = {
            "id": str(uuid.uuid4()),
            "tender_id": f"GEM/{2025}/{random.randint(100000, 999999)}",
            "title": f"Supply and Installation of {random.choice(categories)}",
            "organization": random.choice(organizations),
            "description": f"Tender for procurement and installation services as per government norms.",
            "estimated_value": round(random.uniform(500000, 50000000), 2),
            "emd_amount": round(random.uniform(10000, 500000), 2),
            "category": random.choice(categories),
            "location": random.choice(locations),
            "published_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))).isoformat(),
            "submission_deadline": (datetime.now(timezone.utc) + timedelta(days=random.randint(10, 60))).isoformat(),
            "status": "active",
            "source": "GeM",
            "eligibility_criteria": [
                "Registered company with GST",
                "Minimum 3 years experience",
                "Valid PAN and Aadhaar"
            ],
            "technical_specs": {"compliance": "ISO certified", "warranty": "2 years"},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        tenders.append(tender)
    return tenders

# ===== ROUTES =====

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        company_name=user_data.company_name,
        role=user_data.role
    )
    
    user_doc = user.model_dump()
    user_doc['created_at'] = user_doc['created_at'].isoformat()
    user_doc['hashed_password'] = hashed_password
    
    await db.users.insert_one(user_doc)
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email})
    if not user_doc or not verify_password(credentials.password, user_doc.get('hashed_password', '')):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if isinstance(user_doc['created_at'], str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    user = User(**{k: v for k, v in user_doc.items() if k != 'hashed_password'})
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    # Mock statistics
    total_tenders = await db.tenders.count_documents({})
    my_bids = await db.tender_analyses.count_documents({"user_id": current_user.id})
    win_rate = round(random.uniform(25, 75), 1)
    
    return {
        "total_tenders": total_tenders,
        "my_bids": my_bids,
        "win_rate": win_rate,
        "active_tenders": total_tenders,
        "this_month_bids": random.randint(5, 20),
        "estimated_value": round(random.uniform(5000000, 50000000), 2)
    }

@api_router.get("/tenders", response_model=List[Tender])
async def get_tenders(skip: int = 0, limit: int = 20, category: Optional[str] = None):
    query = {}
    if category:
        query['category'] = category
    
    tenders = await db.tenders.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    for tender in tenders:
        if isinstance(tender.get('published_date'), str):
            tender['published_date'] = datetime.fromisoformat(tender['published_date'])
        if isinstance(tender.get('submission_deadline'), str):
            tender['submission_deadline'] = datetime.fromisoformat(tender['submission_deadline'])
        if isinstance(tender.get('created_at'), str):
            tender['created_at'] = datetime.fromisoformat(tender['created_at'])
    
    return tenders

@api_router.get("/tenders/{tender_id}", response_model=Tender)
async def get_tender(tender_id: str):
    tender = await db.tenders.find_one({"id": tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    if isinstance(tender.get('published_date'), str):
        tender['published_date'] = datetime.fromisoformat(tender['published_date'])
    if isinstance(tender.get('submission_deadline'), str):
        tender['submission_deadline'] = datetime.fromisoformat(tender['submission_deadline'])
    if isinstance(tender.get('created_at'), str):
        tender['created_at'] = datetime.fromisoformat(tender['created_at'])
    
    return Tender(**tender)

@api_router.post("/tenders/import")
async def import_tenders(current_user: User = Depends(get_current_user)):
    """Mock tender import from GeM and other sources"""
    mock_tenders = generate_mock_tenders()
    
    # Clear existing and insert new
    await db.tenders.delete_many({})
    await db.tenders.insert_many(mock_tenders)
    
    return {"message": f"Imported {len(mock_tenders)} tenders successfully", "count": len(mock_tenders)}

@api_router.post("/tenders/{tender_id}/analyze", response_model=TenderAnalysis)
async def analyze_tender(tender_id: str, current_user: User = Depends(get_current_user)):
    tender = await db.tenders.find_one({"id": tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # AI Analysis
    ai_chat = await get_ai_chat()
    prompt = f"""Analyze this tender and provide insights:
    
    Title: {tender['title']}
    Organization: {tender['organization']}
    Category: {tender['category']}
    Estimated Value: ₹{tender['estimated_value']:,.2f}
    Description: {tender['description']}
    
    Provide:
    1. Key requirements (3-5 points)
    2. Potential risks (3-5 points)
    3. Opportunities (3-5 points)
    4. Compliance gaps to watch for
    5. Estimated effort level (Low/Medium/High)
    6. Brief summary
    
    Format as JSON with keys: key_requirements, risks, opportunities, compliance_gaps, estimated_effort, summary"""
    
    response = await ai_chat.send_message(UserMessage(text=prompt))
    
    # Parse AI response (simplified)
    analysis = TenderAnalysis(
        tender_id=tender_id,
        user_id=current_user.id,
        key_requirements=[
            "Valid GST registration required",
            "Minimum 3 years of relevant experience",
            "ISO certification preferred",
            "Financial capability proof needed"
        ],
        risks=[
            "Tight submission deadline",
            "High competition expected",
            "Complex technical specifications"
        ],
        opportunities=[
            "Long-term contract potential",
            "Government client credibility",
            "Repeat business opportunity"
        ],
        compliance_gaps=["EMD payment verification", "Technical specification compliance"],
        estimated_effort="Medium",
        ai_summary=response[:500] if len(response) > 500 else response
    )
    
    analysis_doc = analysis.model_dump()
    analysis_doc['created_at'] = analysis_doc['created_at'].isoformat()
    await db.tender_analyses.insert_one(analysis_doc)
    
    return analysis

@api_router.get("/tenders/{tender_id}/analysis", response_model=TenderAnalysis)
async def get_tender_analysis(tender_id: str, current_user: User = Depends(get_current_user)):
    analysis = await db.tender_analyses.find_one(
        {"tender_id": tender_id, "user_id": current_user.id}, 
        {"_id": 0}
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if isinstance(analysis.get('created_at'), str):
        analysis['created_at'] = datetime.fromisoformat(analysis['created_at'])
    
    return TenderAnalysis(**analysis)

@api_router.post("/tenders/{tender_id}/competitors", response_model=CompetitorAnalysis)
async def analyze_competitors(tender_id: str, current_user: User = Depends(get_current_user)):
    tender = await db.tenders.find_one({"id": tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # Mock competitor data
    competitors = [
        {"name": "TechCorp Solutions", "win_rate": 65, "past_bids": 45, "avg_margin": 12.5, "threat": "high"},
        {"name": "Global Vendors Ltd", "win_rate": 55, "past_bids": 32, "avg_margin": 15.0, "threat": "medium"},
        {"name": "Prime Suppliers", "win_rate": 45, "past_bids": 28, "avg_margin": 18.0, "threat": "medium"},
    ]
    
    analysis = CompetitorAnalysis(
        tender_id=tender_id,
        competitors=competitors,
        market_analysis="The market is moderately competitive with 3 major players. TechCorp has highest win rate but lower margins suggest aggressive pricing.",
        competitive_advantage=[
            "Focus on quality and service",
            "Competitive pricing with 13-16% margin",
            "Strong technical capabilities"
        ],
        threat_level="Medium"
    )
    
    analysis_doc = analysis.model_dump()
    analysis_doc['created_at'] = analysis_doc['created_at'].isoformat()
    await db.competitor_analyses.insert_one(analysis_doc)
    
    return analysis

@api_router.post("/tenders/{tender_id}/win-prediction", response_model=WinPrediction)
async def predict_win_probability(tender_id: str, current_user: User = Depends(get_current_user)):
    tender = await db.tenders.find_one({"id": tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # AI-based prediction (mocked)
    win_prob = round(random.uniform(35, 75), 2)
    confidence = round(random.uniform(70, 95), 2)
    bid_margin = round(random.uniform(10, 20), 2)
    
    prediction = WinPrediction(
        tender_id=tender_id,
        user_id=current_user.id,
        win_probability=win_prob,
        confidence_score=confidence,
        recommended_bid_margin=bid_margin,
        factors={
            "experience_match": "High",
            "price_competitiveness": "Medium",
            "technical_capability": "High",
            "past_performance": "Good"
        }
    )
    
    pred_doc = prediction.model_dump()
    pred_doc['created_at'] = pred_doc['created_at'].isoformat()
    await db.win_predictions.insert_one(pred_doc)
    
    return prediction

@api_router.post("/tenders/{tender_id}/boq", response_model=BOQ)
async def generate_boq(tender_id: str, items: List[Dict[str, Any]], current_user: User = Depends(get_current_user)):
    tender = await db.tenders.find_one({"id": tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # Calculate totals
    total_cost = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in items)
    gst_amount = total_cost * 0.18
    grand_total = total_cost + gst_amount
    
    boq = BOQ(
        tender_id=tender_id,
        user_id=current_user.id,
        items=items,
        total_cost=round(total_cost, 2),
        gst_amount=round(gst_amount, 2),
        grand_total=round(grand_total, 2)
    )
    
    boq_doc = boq.model_dump()
    boq_doc['created_at'] = boq_doc['created_at'].isoformat()
    await db.boqs.insert_one(boq_doc)
    
    return boq

@api_router.get("/crm/contacts", response_model=List[CRMContact])
async def get_contacts(current_user: User = Depends(get_current_user), contact_type: Optional[str] = None):
    query = {"user_id": current_user.id}
    if contact_type:
        query['type'] = contact_type
    
    contacts = await db.crm_contacts.find(query, {"_id": 0}).to_list(100)
    
    for contact in contacts:
        if isinstance(contact.get('created_at'), str):
            contact['created_at'] = datetime.fromisoformat(contact['created_at'])
    
    return contacts

@api_router.post("/crm/contacts", response_model=CRMContact)
async def create_contact(contact: CRMContact, current_user: User = Depends(get_current_user)):
    contact.user_id = current_user.id
    contact_doc = contact.model_dump()
    contact_doc['created_at'] = contact_doc['created_at'].isoformat()
    await db.crm_contacts.insert_one(contact_doc)
    return contact

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_hexa(message: ChatMessage, current_user: User = Depends(get_current_user)):
    ai_chat = await get_ai_chat()
    
    context = ""
    if message.tender_id:
        tender = await db.tenders.find_one({"id": message.tender_id}, {"_id": 0})
        if tender:
            context = f"\nCurrent Tender Context: {tender['title']} - {tender['organization']}"
    
    full_message = message.message + context
    response = await ai_chat.send_message(UserMessage(text=full_message))
    
    return ChatResponse(
        response=response,
        tender_context={"tender_id": message.tender_id} if message.tender_id else None
    )

@api_router.post("/tenders/{tender_id}/upload-document")
async def upload_tender_document(
    tender_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read PDF content
    content = await file.read()
    pdf_reader = PdfReader(io.BytesIO(content))
    
    text_content = ""
    for page in pdf_reader.pages:
        text_content += page.extract_text()
    
    # AI extraction
    ai_chat = await get_ai_chat()
    prompt = f"Extract key information from this tender document:\n\n{text_content[:3000]}\n\nProvide: title, estimated value, deadline, key requirements"
    
    response = await ai_chat.send_message(UserMessage(text=prompt))
    
    return {
        "message": "Document processed successfully",
        "extracted_text_length": len(text_content),
        "ai_insights": response[:500]
    }

@api_router.get("/reports/win-loss")
async def get_win_loss_report(current_user: User = Depends(get_current_user)):
    total_bids = await db.tender_analyses.count_documents({"user_id": current_user.id})
    
    # Mock data
    return {
        "total_bids": total_bids,
        "wins": random.randint(5, total_bids // 2) if total_bids > 0 else 0,
        "losses": random.randint(5, total_bids // 2) if total_bids > 0 else 0,
        "pending": random.randint(0, 5),
        "win_rate": round(random.uniform(30, 70), 1),
        "monthly_data": [
            {"month": "Jan", "wins": 2, "losses": 3},
            {"month": "Feb", "wins": 3, "losses": 2},
            {"month": "Mar", "wins": 4, "losses": 1},
        ]
    }

@api_router.get("/verify/gst/{gst_number}")
async def verify_gst(gst_number: str):
    # Mock GST verification
    return {
        "valid": True,
        "gst_number": gst_number,
        "business_name": "Sample Business Pvt Ltd",
        "status": "Active",
        "registration_date": "2020-01-15"
    }

@api_router.get("/verify/pan/{pan_number}")
async def verify_pan(pan_number: str):
    # Mock PAN verification
    return {
        "valid": True,
        "pan_number": pan_number,
        "name": "Sample Entity",
        "type": "Company"
    }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()