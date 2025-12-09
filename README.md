# DigniLife - Micro-Task Earning Platform

**Phase 1: Database Foundation (COMPLETED)**

A production-ready micro-task earning platform where users earn $200-500/day through task completion. This repository contains the complete database foundation with 25 tables, full async SQLAlchemy 2.0 implementation, and comprehensive security features.

## 🚀 Features

- **Universal Access**: 100+ languages and dialects supported
- **Multiple Income Streams**: 7 revenue models
- **Auto-Save**: Automatic $100 savings at threshold
- **Flexible Withdrawals**: Bank, mobile wallet, crypto, airtime
- **Subscription Tiers**: Free (50 tasks/day), Pro (100 tasks), Elite (unlimited)
- **Fair Payouts**: $1.50-$15 per task

## 💰 Revenue Model

1. Platform fees (3%)
2. Premium subscriptions
3. Data marketplace
4. NGO/Sponsor funding
5. Partner revenue
6. Enterprise API
7. Advertising

**Projected Revenue**: $5M-10M/year

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy 2.0 (async)
- **Auth**: JWT + Face verification
- **Migrations**: Alembic

## 📋 Setup Instructions

### 1. Prerequisites
```bash
# Install PostgreSQL 16
# Install Python 3.11+
```

### 2. Database Setup
```bash
# Create database
psql -U postgres -c "CREATE DATABASE dignilife"
```

### 3. Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 4. Configuration
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your settings
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dignilife
SECRET_KEY=your-secret-key-here
```

### 5. Run Migrations
```bash
alembic upgrade head
```

### 6. Seed Data
```bash
# Seed tasks
python scripts/seed_tasks.py

# Create admin user (optional)
python scripts/create_admin.py
```

### 7. Start Server
```bash
python -m uvicorn src.main:app --reload
```

### 8. Access API

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get profile

### Tasks
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks/submit` - Submit task
- `GET /api/v1/tasks/stats` - Get statistics

### Wallet
- `GET /api/v1/wallet/balance` - Get balance
- `POST /api/v1/wallet/withdraw` - Request withdrawal
- `GET /api/v1/wallet/methods` - List payment methods
- `POST /api/v1/wallet/methods` - Add payment method

### Subscription
- `GET /api/v1/subscription/plans` - List plans
- `POST /api/v1/subscription/upgrade` - Upgrade
- `GET /api/v1/subscription/status` - Get status

### Languages
- `GET /api/v1/languages` - List languages
- `GET /api/v1/languages/my-profile` - Get user languages
- `POST /api/v1/languages/my-profile` - Add language

### Admin
- `GET /api/v1/admin/stats` - Platform stats
- `GET /api/v1/admin/revenue` - Revenue breakdown
- `POST /api/v1/admin/tasks` - Create task
- `POST /api/v1/admin/sponsors` - Add sponsor

## 🔐 Admin Access

Admin endpoints require `x-admin-key` header with SECRET_KEY value.

## 📊 Database Schema

See `src/db/models.py` for complete schema including:
- Users & Authentication
- Tasks & Submissions
- Wallet & Transactions
- Subscriptions
- NGO Sponsors
- Payment Methods
- Language Support
- Revenue Tracking

## 🌐 Supported Languages

**Major**: English, Myanmar, Chinese, Hindi, Spanish, Arabic, Bengali, Portuguese, Russian, Japanese

**Myanmar Dialects**: Rakhine, Mon, Shan, Kachin, Karen (Pwo/S'gaw), Chin, Mizo

**Regional**: Thai, Vietnamese, Indonesian, Tagalog, Khmer, Lao, Malay

## 💳 Payment Methods

- Banks (local & international)
- Mobile wallets (Wave Money, KBZ Pay, etc.)
- Cryptocurrency (USDT, USDC, BTC, ETH)
- Prepaid cards
- Mobile airtime
- Cash pickup (Western Union, MoneyGram)

## 📈 User Earning Potential

**Free Tier**: $130/day (50 tasks, 1 hour)
**Pro Tier**: $312/day (100 tasks, 2 hours)
**Elite Tier**: $780/day (unlimited tasks)

## 🤝 Contributing

We welcome contributions! Please see CONTRIBUTING.md

## 📄 License

Proprietary - All rights reserved

## 📞 Contact

- Email: info@dignilife.com
- Website: https://dignilife.com

---

**Built with ❤️ for universal digital inclusion**
```

---

## ✅ **COMPLETE! ALL FILES DELIVERED!**

**ဒါက production-ready code အားလုံး ပြီးပါပြီ!** 🎉

### **📁 Complete File Structure:**
```
DigniLife/
├── .env
├── README.md
├── requirements.txt
├── alembic/
│   └── env.py
├── scripts/
│   ├── seed_tasks.py
│   └── create_admin.py
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   ├── security.py
│   │   └── exceptions.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── task.py
│   │   ├── wallet.py
│   │   ├── subscription.py
│   │   ├── language.py
│   │   └── admin.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── wallet.py
│   │   ├── subscription.py
│   │   └── revenue.py
│   └── routers/
│       ├── __init__.py
│       ├── auth.py
│       ├── tasks.py
│       ├── wallet.py
│       ├── subscription.py
│       ├── language.py
│       └── admin.py

# frontent structure
# DigniLife - Universal Digital Income Platform

A modern web application for earning money through AI training tasks. Built with Next.js 14, TypeScript, and Tailwind CSS.

## 🚀 Features

- **Face Recognition Authentication** - Secure, password-free login
- **Task Marketplace** - Browse and complete various AI training tasks
- **Smart Wallet System** - Auto-save 30% of earnings
- **Multi-language Support** - Support for 10+ languages
- **Real-time Analytics** - Track your earnings and performance
- **Subscription Tiers** - Free, Pro, and Elite plans
- **Payment Methods** - Bank, mobile wallet, and crypto support
- **Responsive Design** - Works on desktop, tablet, and mobile

## 🛠️ Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Beautiful UI components
- **Zustand** - State management
- **React Query** - Server state management
- **React Hook Form** - Form handling
- **Zod** - Schema validation
- **Recharts** - Data visualization
- **Sonner** - Toast notifications

### Backend Integration
- **Axios** - HTTP client
- **Face Recognition API** - Biometric authentication

## 📦 Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/dignilife-frontend.git
cd dignilife-frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Set up environment variables**
```bash
cp .env.local.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

4. **Run the development server**
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure
```
frontend/
├── app/                      # Next.js App Router
│   ├── (auth)/              # Authentication pages
│   ├── (dashboard)/         # Protected dashboard pages
│   ├── layout.tsx           # Root layout
│   └── globals.css          # Global styles
├── components/              # React components
│   ├── auth/               # Authentication components
│   ├── dashboard/          # Dashboard components
│   ├── layout/             # Layout components
│   ├── profile/            # Profile components
│   ├── settings/           # Settings components
│   ├── subscription/       # Subscription components
│   ├── tasks/              # Task components
│   ├── wallet/             # Wallet components
│   ├── ui/                 # UI primitives (shadcn)
│   └── providers/          # React providers
├── hooks/                   # Custom React hooks
├── lib/                     # Utility functions
├── store/                   # Zustand stores
├── types/                   # TypeScript types
├── public/                  # Static assets
└── middleware.ts            # Next.js middleware
```

## 🎨 Key Pages

- **`/login`** - Face recognition login
- **`/register`** - Account creation with face setup
- **`/dashboard`** - Main dashboard with stats
- **`/tasks`** - Browse available tasks
- **`/tasks/[id]`** - Task details and submission
- **`/tasks/my-submissions`** - View submission history
- **`/wallet`** - Wallet overview
- **`/wallet/withdraw`** - Withdraw funds
- **`/wallet/methods`** - Payment methods
- **`/wallet/history`** - Transaction history
- **`/profile`** - User profile
- **`/settings`** - Account settings
- **`/subscription`** - Upgrade plans

## 🔐 Authentication

The app uses face recognition for authentication:

1. Users register by uploading a face photo
2. Face embedding is stored securely
3. Login via face recognition (no passwords needed)
4. JWT tokens for API authentication

## 💰 Wallet System

- **Main Balance (70%)** - Available for withdrawal
- **Savings Balance (30%)** - Auto-saved earnings
- **Auto-Cut Threshold** - $100 triggers savings transfer
- **Multiple Payment Methods** - Bank, wallet, crypto

## 📱 Responsive Design

- Mobile-first approach
- Breakpoints: `sm` (640px), `md` (768px), `lg` (1024px), `xl` (1280px)
- Touch-friendly interactions
- Optimized for all screen sizes

## 🧪 Development

### Available Scripts
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
```

### Code Style

- Use TypeScript for all new files
- Follow ESLint rules
- Use Prettier for formatting
- Write semantic HTML
- Mobile-first CSS

## 🚀 Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import project to Vercel
3. Configure environment variables
4. Deploy

### Other Platforms

Build the app:
```bash
npm run build
```

Serve the `.next` directory with a Node.js server.

## 🔧 Configuration

### API Integration

Update `lib/api.ts` to match your backend endpoints.

### Styling

Customize theme in `tailwind.config.js` and `app/globals.css`.

### Features

Enable/disable features in `lib/constants.ts`.

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## 📞 Support

- Email: support@dignilife.io
- Documentation: https://docs.dignilife.io
- Issues: https://github.com/yourusername/dignilife-frontend/issues

## 🙏 Acknowledgments

- shadcn/ui for beautiful components
- Vercel for hosting
- The Next.js team

---

**Built with ❤️ by the DigniLife Team**