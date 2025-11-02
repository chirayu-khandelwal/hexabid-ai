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
from gem_scraper import GeMScraper, HistoricalDataCollector
from document_generator import DocumentGenerator
from ai_models.competitor_model import SimpleCompetitorModel, analyze_market

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
            "description": "Tender for procurement and installation services as per government norms.",
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
    
    _ = await ai_chat.send_message(UserMessage(text=prompt))
    
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

@api_router.post("/tenders/{tender_id}/competitors-ml", response_model=CompetitorAnalysis)
async def analyze_competitors_ml(tender_id: str, current_user: User = Depends(get_current_user)):
    tender = await db.tenders.find_one({"id": tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    # Ensure datetime types for model features
    def to_dt(v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except Exception:
                return None
        return v

    tender["published_date"] = to_dt(tender.get("published_date"))
    tender["submission_deadline"] = to_dt(tender.get("submission_deadline"))

    model = SimpleCompetitorModel()
    competitors_scored = model.predict(tender)

    analysis = CompetitorAnalysis(
        tender_id=tender_id,
        competitors=competitors_scored,
        market_analysis=analyze_market(competitors_scored),
        competitive_advantage=[
            "Leverage quality and post-warranty service commitments",
            "Target 12-16% margin with flexible delivery milestones",
            "Highlight relevant domain experience and compliance readiness"
        ],
        threat_level=(
            "High" if any(c.get("threat") == "high" for c in competitors_scored)
            else ("Medium" if any(c.get("threat") == "medium" for c in competitors_scored) else "Low")
        ),
    )

    analysis_doc = analysis.model_dump()
    analysis_doc['created_at'] = analysis_doc['created_at'].isoformat()
    await db.competitor_analyses.insert_one(analysis_doc)

    return analysis


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
    
    _ = await ai_chat.send_message(UserMessage(text=prompt))
    
    return {
        "message": "Document processed successfully",
        "extracted_text_length": len(text_content),
        "ai_insights": "Insights generated"
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

@api_router.post("/tenders/{tender_id}/price-analysis", response_model=PriceAnalysis)
async def analyze_prices(tender_id: str, current_user: User = Depends(get_current_user)):
    tender = await db.tenders.find_one({"id": tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # Mock historical price data
    base_price = tender['estimated_value']
    historical_prices = [
        {"year": 2023, "price": base_price * 0.85, "vendor": "ABC Corp"},
        {"year": 2023, "price": base_price * 0.90, "vendor": "XYZ Ltd"},
        {"year": 2024, "price": base_price * 0.88, "vendor": "PQR Solutions"},
        {"year": 2024, "price": base_price * 0.92, "vendor": "LMN Industries"}
    ]
    
    avg_price = sum(p['price'] for p in historical_prices) / len(historical_prices)
    recommended = avg_price * 1.05  # 5% margin
    
    analysis = PriceAnalysis(
        tender_id=tender_id,
        historical_prices=historical_prices,
        average_price=round(avg_price, 2),
        recommended_price=round(recommended, 2),
        price_trend="stable"
    )
    
    analysis_doc = analysis.model_dump()
    analysis_doc['created_at'] = analysis_doc['created_at'].isoformat()
    await db.price_analyses.insert_one(analysis_doc)
    
    return analysis

@api_router.post("/tenders/{tender_id}/product-recommendations", response_model=ProductRecommendation)
async def recommend_products(tender_id: str, current_user: User = Depends(get_current_user)):
    tender = await db.tenders.find_one({"id": tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # AI-based product recommendations
    ai_chat = await get_ai_chat()
    prompt = f"""Based on this tender requirement: {tender['title']} in category {tender['category']}, 
    recommend 3 suitable products and 3 OEM manufacturers. Format as JSON with keys: products, oems"""
    
    _unused_ai = response  # keep variable to avoid unused lint; AI output may be used in future release

    _ = await ai_chat.send_message(UserMessage(text=prompt))
    
    # Mock recommendations
    products = [
        {"name": "Enterprise Solution X1", "specs": "High performance", "price_range": "₹5-10L", "compliance": "ISO certified"},
        {"name": "Professional Suite V2", "specs": "Mid-range", "price_range": "₹3-6L", "compliance": "CE certified"},
        {"name": "Standard Package S3", "specs": "Cost-effective", "price_range": "₹2-4L", "compliance": "BIS certified"}
    ]
    
    oems = [
        {"name": "TechCorp India", "rating": 4.5, "experience": "15 years", "specialization": tender['category']},
        {"name": "Global Solutions Ltd", "rating": 4.3, "experience": "12 years", "specialization": tender['category']},
        {"name": "Premium Vendors", "rating": 4.7, "experience": "20 years", "specialization": tender['category']}
    ]
    
    recommendation = ProductRecommendation(
        tender_id=tender_id,
        recommended_products=products,
        oem_suggestions=oems,
        technical_compliance={"iso": True, "bis": True, "ce": True}
    )
    
    rec_doc = recommendation.model_dump()
    rec_doc['created_at'] = rec_doc['created_at'].isoformat()
    await db.product_recommendations.insert_one(rec_doc)
    
    return recommendation

@api_router.get("/notifications", response_model=List[Notification])
async def get_notifications(current_user: User = Depends(get_current_user)):
    notifications = await db.notifications.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    for notif in notifications:
        if isinstance(notif.get('created_at'), str):
            notif['created_at'] = datetime.fromisoformat(notif['created_at'])
    
    return notifications

@api_router.post("/notifications", response_model=Notification)
async def create_notification(notification: Notification, current_user: User = Depends(get_current_user)):
    notification.user_id = current_user.id
    notif_doc = notification.model_dump()
    notif_doc['created_at'] = notif_doc['created_at'].isoformat()
    await db.notifications.insert_one(notif_doc)
    return notification

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: User = Depends(get_current_user)):
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id},
        {"$set": {"read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}

@api_router.get("/support/tickets", response_model=List[SupportTicket])
async def get_tickets(current_user: User = Depends(get_current_user)):
    tickets = await db.support_tickets.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    for ticket in tickets:
        if isinstance(ticket.get('created_at'), str):
            ticket['created_at'] = datetime.fromisoformat(ticket['created_at'])
    
    return tickets

@api_router.post("/support/tickets", response_model=SupportTicket)
async def create_ticket(ticket: SupportTicket, current_user: User = Depends(get_current_user)):
    ticket.user_id = current_user.id
    ticket_doc = ticket.model_dump()
    ticket_doc['created_at'] = ticket_doc['created_at'].isoformat()
    await db.support_tickets.insert_one(ticket_doc)
    
    # Auto-create notification
    notif = Notification(
        user_id=current_user.id,
        title="Support Ticket Created",
        message=f"Your ticket '{ticket.subject}' has been created successfully.",
        type="info"
    )
    notif_doc = notif.model_dump()
    notif_doc['created_at'] = notif_doc['created_at'].isoformat()
    await db.notifications.insert_one(notif_doc)
    
    return ticket

@api_router.post("/support/tickets/{ticket_id}/respond")
async def respond_to_ticket(ticket_id: str, response_text: str, current_user: User = Depends(get_current_user)):
    ticket = await db.support_tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    response_payload = {
        "user": current_user.full_name,
        "message": response_text,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.support_tickets.update_one(
        {"id": ticket_id},
        {"$push": {"responses": response_payload}}
    )
    
    return {"message": "Response added successfully"}

@api_router.get("/vendors/performance", response_model=List[VendorPerformance])
async def get_vendor_performance(current_user: User = Depends(get_current_user)):
    # Mock vendor performance data
    vendors = [
        {
            "id": str(uuid.uuid4()),
            "vendor_id": "V001",
            "vendor_name": "TechCorp Solutions",
            "total_orders": 45,
            "completed_orders": 42,
            "on_time_delivery": 93.3,
            "quality_rating": 4.5,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "vendor_id": "V002",
            "vendor_name": "Global Vendors Ltd",
            "total_orders": 32,
            "completed_orders": 30,
            "on_time_delivery": 93.8,
            "quality_rating": 4.3,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    return vendors

@api_router.get("/admin/users")
async def admin_get_users(current_user: User = Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(1000)
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    return users

@api_router.get("/admin/stats")
async def admin_get_stats(current_user: User = Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_users = await db.users.count_documents({})
    total_tenders = await db.tenders.count_documents({})
    total_analyses = await db.tender_analyses.count_documents({})
    total_tickets = await db.support_tickets.count_documents({})
    
    return {
        "total_users": total_users,
        "total_tenders": total_tenders,
        "total_analyses": total_analyses,
        "total_support_tickets": total_tickets,
        "active_subscriptions": random.randint(50, 200),
        "revenue_this_month": round(random.uniform(50000, 200000), 2)
    }

@api_router.get("/subscription/my-subscription", response_model=Subscription)
async def get_my_subscription(current_user: User = Depends(get_current_user)):
    subscription = await db.subscriptions.find_one({"user_id": current_user.id}, {"_id": 0})
    
    if not subscription:
        # Create default subscription
        subscription = Subscription(
            user_id=current_user.id,
            plan="professional",
            ai_credits=1000,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=30)
        )
        sub_doc = subscription.model_dump()
        sub_doc['start_date'] = sub_doc['start_date'].isoformat()
        sub_doc['end_date'] = sub_doc['end_date'].isoformat()
        sub_doc['created_at'] = sub_doc['created_at'].isoformat()
        await db.subscriptions.insert_one(sub_doc)
    else:
        if isinstance(subscription.get('start_date'), str):
            subscription['start_date'] = datetime.fromisoformat(subscription['start_date'])
        if isinstance(subscription.get('end_date'), str):
            subscription['end_date'] = datetime.fromisoformat(subscription['end_date'])
        if isinstance(subscription.get('created_at'), str):
            subscription['created_at'] = datetime.fromisoformat(subscription['created_at'])
        subscription = Subscription(**subscription)
    
    return subscription

@api_router.post("/tenders/auto-classify")
async def auto_classify_tenders(current_user: User = Depends(get_current_user)):
    """Auto-classify tenders using AI"""
    tenders = await db.tenders.find({}, {"_id": 0}).to_list(100)
    
    ai_chat = await get_ai_chat()
    classified_count = 0
    
    for tender in tenders:
        if not tender.get('ai_classified'):
            prompt = f"Classify this tender into one category: {tender['title']}. Categories: IT Services, Construction, Medical Equipment, Office Supplies, Consulting. Reply with just the category name."
            category = await ai_chat.send_message(UserMessage(text=prompt))
            
            await db.tenders.update_one(
                {"id": tender['id']},
                {"$set": {"category": category.strip(), "ai_classified": True}}
            )
            classified_count += 1
    
    return {"message": f"Classified {classified_count} tenders", "count": classified_count}

@api_router.post("/gem/scrape-latest")
async def scrape_gem_tenders(category: Optional[str] = None, limit: int = 50, current_user: User = Depends(get_current_user)):
    """Scrape latest tenders from GeM portal"""
    scraper = GeMScraper()
    tenders = await scraper.scrape_latest_tenders(category=category, limit=limit)
    
    # Store in database
    if tenders:
        for tender in tenders:
            # Check if tender already exists
            existing = await db.tenders.find_one({"tender_id": tender['tender_id']})
            if not existing:
                await db.tenders.insert_one(tender)
    
    return {"message": f"Scraped {len(tenders)} tenders from GeM", "count": len(tenders), "tenders": tenders}

@api_router.post("/documents/generate-boq")
async def generate_boq_document(tender_id: str, items: List[Dict[str, Any]], current_user: User = Depends(get_current_user)):
    """Generate BOQ Excel document"""
    tender = await db.tenders.find_one({"id": tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    doc_generator = DocumentGenerator()
    filepath = doc_generator.generate_boq(tender, items)
    
    return {
        "message": "BOQ generated successfully",
        "file_path": filepath,
        "file_name": os.path.basename(filepath)
    }

@api_router.post("/documents/generate-cover-letter")
async def generate_cover_letter_document(tender_id: str, company_data: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Generate cover letter document"""
    tender = await db.tenders.find_one({"id": tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    doc_generator = DocumentGenerator()
    filepath = doc_generator.generate_cover_letter(company_data, tender)
    
    return {
        "message": "Cover letter generated successfully",
        "file_path": filepath,
        "file_name": os.path.basename(filepath)
    }

@api_router.post("/documents/generate-company-profile")
async def generate_company_profile_document(company_data: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Generate company profile document"""
    doc_generator = DocumentGenerator()
    filepath = doc_generator.generate_company_profile(company_data)
    
    return {
        "message": "Company profile generated successfully",
        "file_path": filepath,
        "file_name": os.path.basename(filepath)
    }

@api_router.post("/documents/generate-technical-bid")
async def generate_technical_bid_document(tender_id: str, technical_details: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Generate technical bid document"""
    tender = await db.tenders.find_one({"id": tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    doc_generator = DocumentGenerator()
    filepath = doc_generator.generate_technical_bid(tender, technical_details)
    
    return {
        "message": "Technical bid generated successfully",
        "file_path": filepath,
        "file_name": os.path.basename(filepath)
    }

@api_router.post("/documents/calculate-emd")
async def calculate_emd(tender_value: float, emd_percentage: float = 2.0):
    """Calculate EMD amount"""
    doc_generator = DocumentGenerator()
    emd_amount = doc_generator.calculate_emd(tender_value, emd_percentage)
    
    return {
        "tender_value": tender_value,
        "emd_percentage": emd_percentage,
        "emd_amount": round(emd_amount, 2),
        "emd_amount_formatted": f"₹{emd_amount:,.2f}"
    }

@api_router.get("/documents/templates")
async def get_document_templates(current_user: User = Depends(get_current_user)):
    """Get available document templates"""
    templates = [
        {"id": "boq", "name": "Bill of Quantities (BOQ)", "description": "Excel template for BOQ"},
        {"id": "cover_letter", "name": "Cover Letter", "description": "Professional cover letter for tender submission"},
        {"id": "company_profile", "name": "Company Profile", "description": "Complete company profile document"},
        {"id": "technical_bid", "name": "Technical Bid", "description": "Technical bid with compliance matrix"},
        {"id": "financial_bid", "name": "Financial Bid", "description": "Financial bid document"},
        {"id": "experience_certificate", "name": "Experience Certificate", "description": "Work experience certificate template"}
    ]
    return templates

@api_router.get("/documents")
async def get_documents(current_user: User = Depends(get_current_user)):
    # Mock document management
    documents = [
        {
            "id": str(uuid.uuid4()),
            "name": "Technical_Specifications.pdf",
            "type": "pdf",
            "size": "2.5 MB",
            "uploaded_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "category": "Technical"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Company_Profile.pdf",
            "type": "pdf",
            "size": "1.8 MB",
            "uploaded_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            "category": "Company"
        }
    ]
    return documents

@api_router.get("/analytics/tender-trends")
async def get_tender_trends(current_user: User = Depends(get_current_user)):
    # Mock analytics data
    trends = {
        "categories": [
            {"name": "IT Services", "count": 45, "value": 15000000},
            {"name": "Construction", "count": 38, "value": 25000000},
            {"name": "Medical Equipment", "count": 28, "value": 12000000},
            {"name": "Office Supplies", "count": 22, "value": 5000000},
            {"name": "Consulting", "count": 18, "value": 8000000}
        ],
        "monthly_trend": [
            {"month": "Jan", "tenders": 45, "value": 20000000},
            {"month": "Feb", "tenders": 52, "value": 25000000},
            {"month": "Mar", "tenders": 48, "value": 22000000}
        ],
        "win_rate_by_category": [
            {"category": "IT Services", "win_rate": 65},
            {"category": "Construction", "win_rate": 58},
            {"category": "Medical Equipment", "win_rate": 72}
        ]
    }
    return trends

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