# HexaBid ERP - AI-Powered Tender Bidding System

![HexaBid Logo](https://via.placeholder.com/800x200/3b82f6/ffffff?text=HexaBid+ERP+v3.0)

## Overview

HexaBid ERP is a comprehensive, AI-powered tender bidding and management system designed to automate tender discovery, analysis, competitor intelligence, and bid strategy for contractors, vendors, OEMs, and consultants.

## Features

### Core Modules

✅ **User & Role Management**
- Multi-company and multi-user support
- Role-based access control (Super Admin, Contractor, Vendor, OEM, Consultant)
- KYC verification system

✅ **Tender Dashboard**
- Real-time analytics and KPIs
- Active tender overview
- Performance metrics

✅ **Tender Search & Discovery**
- AI-powered tender import from GeM and other sources
- Advanced filtering and search
- Category-based organization

✅ **AI Tender Analysis**
- Automated requirement extraction
- Risk identification
- Opportunity assessment
- Compliance gap detection
- Effort estimation

✅ **Competitor Analysis**
- Historical bidder tracking
- Competitor win rate analysis
- Market positioning insights
- Threat level assessment

✅ **Win Probability Prediction**
- AI-driven win probability calculation
- Recommended bid margin suggestions
- Success factor analysis

✅ **Technical Review & Recommendations**
- Specification analysis
- Product matching
- OEM recommendations

✅ **BOQ (Bill of Quantities) Builder**
- Automated BOQ generation
- Cost calculation with GST
- Price analysis

✅ **CRM & Vendor Management**
- Contact database
- Vendor categorization
- Relationship tracking

✅ **Reports & Analytics**
- Win/loss ratio tracking
- Monthly performance trends
- Exportable insights

✅ **AI Chat Assistant (Ask Hexa)**
- Conversational AI for bidding advice
- Tender-specific guidance
- Market insights

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Authentication**: JWT + OAuth2
- **AI Integration**: OpenAI GPT-4 via Emergent LLM Key
- **PDF Processing**: PyPDF2

### Frontend
- **Framework**: React 19
- **Routing**: React Router DOM
- **UI Components**: Shadcn/UI (Radix UI)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Notifications**: Sonner

### AI Features
- **LLM Integration**: Emergent Integrations library
- **Models**: OpenAI GPT-4o
- **Use Cases**: Document analysis, prediction, recommendations, chatbot

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB 5.0+
- Yarn package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/hexatechpl/hexabid-erp.git
cd hexabid-erp
```

2. **Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd frontend
yarn install
```

4. **Configure Environment**

Backend `.env`:
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="hexabid_erp"
JWT_SECRET_KEY="your-secret-key"
EMERGENT_LLM_KEY="sk-emergent-6909dD1Ad8eD016450"
CORS_ORIGINS="*"
```

Frontend `.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

5. **Run the Application**

Backend:
```bash
cd backend
source venv/bin/activate
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

Frontend:
```bash
cd frontend
yarn start
```

Access at: `http://localhost:3000`

## API Documentation

Once the backend is running, access interactive API docs at:
- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

## Key API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Tenders
- `GET /api/tenders` - List all tenders
- `GET /api/tenders/{id}` - Get tender details
- `POST /api/tenders/import` - Import tenders from sources
- `POST /api/tenders/{id}/analyze` - AI analysis
- `POST /api/tenders/{id}/competitors` - Competitor analysis
- `POST /api/tenders/{id}/win-prediction` - Win probability

### CRM
- `GET /api/crm/contacts` - List contacts
- `POST /api/crm/contacts` - Add contact

### Reports
- `GET /api/reports/win-loss` - Win/loss report

### AI Chat
- `POST /api/chat` - Chat with Hexa AI

## Project Structure

```
hexabid-erp/
├── backend/
│   ├── server.py          # Main FastAPI application
│   ├── requirements.txt   # Python dependencies
│   └── .env              # Environment variables
├── frontend/
│   ├── src/
│   │   ├── App.js        # Main React component
│   │   ├── pages/        # Page components
│   │   │   ├── LoginPage.js
│   │   │   ├── Dashboard.js
│   │   │   ├── TendersPage.js
│   │   │   ├── TenderDetailPage.js
│   │   │   ├── CRMPage.js
│   │   │   ├── ReportsPage.js
│   │   │   └── ChatPage.js
│   │   └── components/   # Reusable components
│   ├── package.json      # Node dependencies
│   └── .env             # Frontend environment
├── DEPLOYMENT_GUIDE.md
└── README.md
```

## Screenshots

### Dashboard
Real-time analytics with tender statistics, win rates, and quick actions.

### Tender Listing
Comprehensive tender search with filters, categories, and deadline tracking.

### AI Analysis
Deep tender analysis with key requirements, risks, opportunities, and compliance gaps.

### Competitor Intelligence
Detailed competitor profiling with win rates, threat levels, and market positioning.

### Win Prediction
AI-powered probability calculation with recommended bid margins.

### AI Chat Assistant
Conversational AI for bidding advice and market insights.

## Deployment

For detailed production deployment instructions, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

### Quick Deploy Summary

1. Clone repository to your VPN server
2. Install dependencies
3. Configure environment variables
4. Build frontend: `yarn build`
5. Setup Nginx reverse proxy
6. Create systemd service for backend
7. Setup SSL with Let's Encrypt
8. Start services

## Mock Data vs Production

### Current Implementation (Mock Data)
- GeM tender import (mock data)
- MSME verification (mock)
- GST validation (mock)
- PAN verification (mock)
- Aadhaar validation (mock)
- Payment gateway (mock)
- WhatsApp notifications (mock)

### For Production
Replace mock implementations with actual API integrations:
1. Obtain API credentials from respective portals
2. Update backend endpoints
3. Add credentials to environment variables

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

## License

Copyright © 2025 HexaTech eSecurity Solutions Pvt. Ltd.

All rights reserved. This is proprietary software.

## Support

- **Email**: support@hexabid.co.in
- **Website**: https://hexabid.co.in
- **GitHub**: https://github.com/hexatechpl/hexabid-erp
- **Documentation**: https://docs.hexabid.co.in

## Acknowledgments

- OpenAI for GPT-4 integration
- Emergent for LLM key management
- Shadcn/UI for component library
- FastAPI for backend framework
- React community for frontend ecosystem

---

**Built with ❤️ by HexaTech eSecurity Solutions**

**Version**: 3.0 | **Last Updated**: January 2025
