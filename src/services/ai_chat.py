"""
AI Chat Service - Context-aware conversational AI
This is where DigniLife's AI makes decisions and provides help
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID


class AIChat:
    """
    AI Chat Service - Context-aware assistant
    Handles: Task guidance, earning tips, platform help, problem solving
    """
    
    @staticmethod
    async def process_message(
        user_message: str,
        user_context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Process user message with full context awareness
        
        Args:
            user_message: User's message
            user_context: User data (tier, earnings, streak, etc.)
            conversation_history: Previous messages in conversation
        
        Returns:
            AI response with actions and suggestions
        """
        
        # Build context for AI decision making
        context = AIChat._build_context(user_message, user_context, conversation_history)
        
        # Analyze intent
        intent = AIChat._analyze_intent(user_message, context)
        
        # Generate response based on intent
        response = await AIChat._generate_response(intent, context, user_context)
        
        return response
    
    @staticmethod
    def _build_context(
        message: str,
        user_context: Dict[str, Any],
        history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Build complete context for AI"""
        return {
            "user_tier": user_context.get("subscription_tier", "free"),
            "total_earnings": user_context.get("total_earnings_usd", 0),
            "available_balance": user_context.get("available_balance_usd", 0),
            "current_streak": user_context.get("current_streak_days", 0),
            "tasks_completed_today": user_context.get("tasks_today", 0),
            "is_verified": user_context.get("is_verified", False),
            "kyc_verified": user_context.get("kyc_verified", False),
            "conversation_history": history or [],
            "current_message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def _analyze_intent(message: str, context: Dict[str, Any]) -> str:
        """Analyze user intent from message"""
        message_lower = message.lower()
        
        # Intent classification (simple keyword-based for now)
        if any(word in message_lower for word in ["help", "how", "what", "guide"]):
            return "help_request"
        elif any(word in message_lower for word in ["task", "work", "earn"]):
            return "task_inquiry"
        elif any(word in message_lower for word in ["withdraw", "payout", "money", "cash"]):
            return "withdrawal_inquiry"
        elif any(word in message_lower for word in ["upgrade", "premium", "pro", "subscription"]):
            return "subscription_inquiry"
        elif any(word in message_lower for word in ["problem", "issue", "error", "not working"]):
            return "problem_report"
        elif any(word in message_lower for word in ["suggestion", "improve", "feature", "idea"]):
            return "suggestion"
        else:
            return "general_conversation"
    
    @staticmethod
    async def _generate_response(
        intent: str,
        context: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI response based on intent"""
        
        responses = {
            "help_request": AIChat._handle_help_request,
            "task_inquiry": AIChat._handle_task_inquiry,
            "withdrawal_inquiry": AIChat._handle_withdrawal_inquiry,
            "subscription_inquiry": AIChat._handle_subscription_inquiry,
            "problem_report": AIChat._handle_problem_report,
            "suggestion": AIChat._handle_suggestion,
            "general_conversation": AIChat._handle_general,
        }
        
        handler = responses.get(intent, AIChat._handle_general)
        return handler(context, user_context)
    
    @staticmethod
    def _handle_help_request(context: Dict, user_context: Dict) -> Dict[str, Any]:
        """Handle help requests"""
        return {
            "message": f"""👋 Hi! I'm your DigniLife AI assistant!

I can help you with:

🎯 **Tasks & Earning**
- Find the best tasks for you
- Tips to maximize earnings
- Understand quality bonuses

💰 **Withdrawals**
- Withdrawal process
- Fee structure (Your tier: {context['user_tier'].upper()} - {['15%', '10%', '5%'][['free', 'pro', 'premium'].index(context['user_tier'])]} fee)
- Payout methods

📊 **Account**
- Track your progress
- Upgrade subscription
- Manage profile

What would you like help with?""",
            "intent": "help_request",
            "suggestions": [
                "Show me available tasks",
                "How can I earn more?",
                "Tell me about withdrawals",
                "Upgrade my subscription"
            ],
            "actions": []
        }
    
    @staticmethod
    def _handle_task_inquiry(context: Dict, user_context: Dict) -> Dict[str, Any]:
        """Handle task-related inquiries"""
        streak = context['current_streak']
        
        return {
            "message": f"""🎯 **Task Information**

📈 Your Current Stats:
- Streak: {streak} days ({min(streak, 30)}% bonus!)
- Today's Tasks: {context['tasks_completed_today']}
- Balance: ${context['available_balance']:.2f}

💡 **Tips to Maximize Earnings:**
1. ⚡ Complete tasks faster for speed bonus (up to 20%)
2. ✅ High quality work = quality bonus (up to 50%)
3. 🔥 Keep your streak going! ({min(streak, 30)}% bonus)
4. 🚀 Upgrade to PRO/PREMIUM for higher multipliers

Would you like me to find the best tasks for you?""",
            "intent": "task_inquiry",
            "suggestions": [
                "Show me high-paying tasks",
                "What's my earning potential?",
                "How to improve my quality score?"
            ],
            "actions": [
                {
                    "type": "navigate",
                    "target": "/tasks",
                    "label": "Browse Tasks"
                }
            ]
        }
    
    @staticmethod
    def _handle_withdrawal_inquiry(context: Dict, user_context: Dict) -> Dict[str, Any]:
        """Handle withdrawal inquiries"""
        tier = context['user_tier']
        fee_rates = {"free": 15, "pro": 10, "premium": 5}
        fee = fee_rates[tier]
        balance = context['available_balance']
        
        return {
            "message": f"""💰 **Withdrawal Information**

Your Balance: **${balance:.2f}**
Your Tier: **{tier.upper()}**
Withdrawal Fee: **{fee}%** (AUTO-CUT)

🏦 **Available Payout Methods:**
- Wave Money, KBZ Pay, CB Pay (Myanmar) - Min $5
- AYA Pay, OnePay (Myanmar) - Min $5
- PayPal (Global) - Min $10
- Western Union, MoneyGram - Min $20
- Bank Transfer - Min $50

💡 **Want to save on fees?**
Upgrade to PRO (10% fee) or PREMIUM (5% fee)!

Net amount after {fee}% fee: **${balance * (1 - fee/100):.2f}**""",
            "intent": "withdrawal_inquiry",
            "suggestions": [
                "Request withdrawal",
                "Calculate withdrawal fee",
                "Upgrade to reduce fees"
            ],
            "actions": [
                {
                    "type": "navigate",
                    "target": "/withdrawals/request",
                    "label": "Request Withdrawal"
                }
            ]
        }
    
    @staticmethod
    def _handle_subscription_inquiry(context: Dict, user_context: Dict) -> Dict[str, Any]:
        """Handle subscription inquiries"""
        current_tier = context['user_tier']
        
        tiers_info = {
            "free": {
                "next": "PRO",
                "benefits": "10% withdrawal fee (vs 15%), 1.2x earning multiplier"
            },
            "pro": {
                "next": "PREMIUM",
                "benefits": "5% withdrawal fee (vs 10%), 1.5x earning multiplier"
            },
            "premium": {
                "next": None,
                "benefits": "You're at the highest tier!"
            }
        }
        
        info = tiers_info[current_tier]
        
        if info["next"]:
            message = f"""⭐ **Subscription Upgrade**

Current Tier: **{current_tier.upper()}**

Upgrade to **{info["next"]}** and get:
{info["benefits"]}

💰 Example: On $100 withdrawal
- Current ({current_tier.upper()}): You get ${100 * (1 - [15, 10, 5][['free', 'pro', 'premium'].index(current_tier)]/100):.2f}
- After upgrade ({info["next"]}): You get ${100 * (1 - [15, 10, 5][['free', 'pro', 'premium'].index(info["next"].lower())]/100):.2f}

Ready to upgrade?"""
        else:
            message = f"""⭐ **Subscription Status**

You're on **{current_tier.upper()}** - the highest tier! 🎉

You enjoy:
- Only 5% withdrawal fee
- 1.5x earning multiplier
- Priority support

Keep earning! 💪"""
        
        return {
            "message": message,
            "intent": "subscription_inquiry",
            "suggestions": [
                "Upgrade now" if info["next"] else "Check my earnings",
                "Compare all tiers",
                "Calculate savings"
            ],
            "actions": [
                {
                    "type": "upgrade",
                    "target": info["next"],
                    "label": f"Upgrade to {info['next']}"
                }
            ] if info["next"] else []
        }
    
    @staticmethod
    def _handle_problem_report(context: Dict, user_context: Dict) -> Dict[str, Any]:
        """Handle problem reports"""
        return {
            "message": """😟 I'm sorry you're experiencing an issue!

I can help you with:

1. 🐛 **Technical Issues**
   - App not working
   - Can't submit tasks
   - Payment problems

2. 💬 **Create Support Ticket**
   - Get human help
   - Track your issue
   - Priority support (for PRO/PREMIUM)

What kind of problem are you facing?""",
            "intent": "problem_report",
            "suggestions": [
                "Can't submit task",
                "Withdrawal not received",
                "Create support ticket",
                "Talk to human agent"
            ],
            "actions": [
                {
                    "type": "navigate",
                    "target": "/support/create-ticket",
                    "label": "Create Support Ticket"
                }
            ]
        }
    
    @staticmethod
    def _handle_suggestion(context: Dict, user_context: Dict) -> Dict[str, Any]:
        """Handle user suggestions"""
        return {
            "message": """💡 **We Love Your Ideas!**

Your suggestions help us improve DigniLife!

🎁 **Suggestion Rewards:**
- Get rewarded if your idea is implemented
- Influence platform development
- Help the community

What's your suggestion?""",
            "intent": "suggestion",
            "suggestions": [
                "Submit my suggestion",
                "View past suggestions",
                "See what's being worked on"
            ],
            "actions": [
                {
                    "type": "navigate",
                    "target": "/ai-proposals/create",
                    "label": "Submit Suggestion"
                }
            ]
        }
    
    @staticmethod
    def _handle_general(context: Dict, user_context: Dict) -> Dict[str, Any]:
        """Handle general conversation"""
        return {
            "message": f"""👋 Hello! I'm here to help you succeed on DigniLife!

📊 Quick Stats:
- Your Balance: ${context['available_balance']:.2f}
- Streak: {context['current_streak']} days 🔥
- Tier: {context['user_tier'].upper()}

How can I assist you today?""",
            "intent": "general_conversation",
            "suggestions": [
                "Show me tasks",
                "How to earn more?",
                "Withdraw money",
                "Get help"
            ],
            "actions": []
        }