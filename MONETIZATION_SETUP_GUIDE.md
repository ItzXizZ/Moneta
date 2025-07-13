# 💰 Moneta Monetization System Setup Guide

## 🎯 Overview

This guide will help you implement a complete monetization system for your Moneta memory application with:

- **Free Tier**: 50 messages/month using `gpt-4o-mini` (cheapest OpenAI model)
- **Premium Tier**: $20/month, unlimited messages using `gpt-3.5-turbo` (better quality)
- **Usage Tracking**: Real-time monitoring of API calls and message limits
- **Subscription Management**: Complete user dashboard and plan management

## 📋 Setup Steps

### Step 1: Create Database Tables

1. **Go to your Supabase dashboard**: https://pquleppdqequfjwlcmbn.supabase.co
2. **Navigate to SQL Editor**
3. **Copy and paste the contents of `create_subscription_tables.sql`**
4. **Click "Run" to execute the SQL**

This creates:
- `subscription_plans` table (stores plan details)
- `user_subscriptions` table (tracks user subscriptions)
- `user_usage` table (tracks monthly usage)
- Helper functions for subscription management

### Step 2: Update Your Main Application

Add these imports to your main `app.py`:

```python
from api.subscription_routes import register_subscription_routes

# Register routes
register_subscription_routes(app)
```

### Step 3: Add Subscription Route to Dashboard

Update your `templates/dashboard.html` to include a subscription link:

```html
<a href="/subscription" class="nav-link">
    <i class="fas fa-credit-card"></i>
    Subscription
</a>
```

### Step 4: Add Subscription Page Route

Add this route to your main Flask app:

```python
@app.route('/subscription')
def subscription_page():
    return render_template('subscription.html')
```

### Step 5: Test the System

1. **Start your application**
2. **Login to your existing account**
3. **Navigate to `/subscription`**
4. **You should see:**
   - Current plan status (Free by default)
   - Usage statistics (messages used this month)
   - Available plans (Free and Premium)
   - Upgrade options

## 🤖 AI Model Costs Comparison

| Model | Input Cost (1M tokens) | Output Cost (1M tokens) | Quality | Best For |
|-------|------------------------|-------------------------|---------|----------|
| **gpt-4o-mini** | $0.15 | $0.60 | Good | Free tier |
| **gpt-3.5-turbo** | $0.50 | $1.50 | Better | Premium tier |
| **gpt-4o** | $2.50 | $10.00 | Best | Enterprise |

## 💡 Alternative Cheaper Models

If you want even cheaper options for free tier:

### Google Gemini Flash 1.5
- **Cost**: ~$0.075/1M input tokens, $0.30/1M output tokens
- **Setup**: Use Google AI Studio API
- **Benefits**: Cheapest option available

### Claude 3 Haiku
- **Cost**: ~$0.25/1M input tokens, $1.25/1M output tokens
- **Setup**: Use Anthropic API
- **Benefits**: Good quality, reasonable cost

## 📊 Subscription Plans Structure

### Free Plan
- **Price**: $0/month
- **Messages**: 50/month
- **AI Model**: gpt-4o-mini
- **Features**: Basic chat, Memory storage (100 memories)
- **Memory Limit**: 100 memories

### Premium Plan
- **Price**: $20/month
- **Messages**: Unlimited
- **AI Model**: gpt-3.5-turbo
- **Features**: Advanced chat, Unlimited memory, Priority support
- **Memory Limit**: No limit

## 🔧 Key Features Implemented

### 1. Usage Tracking
- Real-time message counting
- Monthly usage limits
- API call tracking
- Token usage monitoring

### 2. Model Switching
- Automatic model selection based on subscription
- Free users get gpt-4o-mini
- Premium users get gpt-3.5-turbo
- Easy to configure different models per tier

### 3. Subscription Management
- User dashboard with current plan
- Usage statistics visualization
- Plan upgrade/downgrade
- Payment integration ready (Stripe compatible)

### 4. Database Functions
- `get_user_subscription()`: Get user's current plan
- `check_user_limits()`: Check if user can use service
- `track_user_usage()`: Record API usage
- Automatic usage reset monthly

## 🔐 Security Features

- **Row Level Security**: Each user can only see their own data
- **JWT Authentication**: Secure API access
- **Usage Validation**: Server-side limit checking
- **Rate Limiting**: Prevents abuse

## 📱 Frontend Features

### Subscription Dashboard
- Current plan display
- Usage progress bars
- AI model information
- Upgrade/downgrade buttons

### Real-time Updates
- Usage tracking updates immediately
- Plan changes reflected instantly
- Error handling and user feedback

## 🚀 Going Live

### 1. Payment Integration
To accept payments, integrate with Stripe:

```javascript
// In your subscription.html
async function subscribeToPlan(planName) {
    // Create Stripe checkout session
    const response = await fetch('/api/subscription/create-checkout', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ plan_name: planName })
    });
    
    const { checkout_url } = await response.json();
    window.location.href = checkout_url;
}
```

### 2. Environment Variables
Make sure you have these in your `.env`:

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
STRIPE_SECRET_KEY=your_stripe_secret_key  # For payments
STRIPE_WEBHOOK_SECRET=your_webhook_secret  # For webhooks
```

### 3. Usage Monitoring
Monitor your costs:
- Set up alerts for high usage
- Track per-user costs
- Monitor model performance

## 🎨 Customization Options

### 1. Change Plan Prices
Update in `create_subscription_tables.sql`:

```sql
INSERT INTO subscription_plans (name, price_cents, monthly_message_limit, features, ai_model) VALUES
('free', 0, 50, '{"features": ["basic_chat"]}', 'gpt-4o-mini'),
('premium', 1999, NULL, '{"features": ["unlimited_chat"]}', 'gpt-3.5-turbo'),
('enterprise', 4999, NULL, '{"features": ["priority_support"]}', 'gpt-4o');
```

### 2. Add New Features
In `subscription_service.py`:

```python
def has_feature(self, user_id: str, feature_name: str) -> bool:
    """Check if user has access to a specific feature"""
    subscription = self.get_user_subscription(user_id)
    features = subscription.get('features', {}).get('features', [])
    return feature_name in features
```

### 3. Different Message Limits
Update plans with different limits:

```python
# In create_subscription_tables.sql
('starter', 999, 100, '{"features": ["basic_chat"]}', 'gpt-4o-mini'),
('professional', 2999, 500, '{"features": ["advanced_chat"]}', 'gpt-3.5-turbo'),
```

## 📈 Analytics and Monitoring

### Track Key Metrics
- Monthly Recurring Revenue (MRR)
- User conversion rates
- Average usage per user
- Cost per user
- Churn rate

### Database Queries for Analytics
```sql
-- Monthly revenue
SELECT 
    date_trunc('month', created_at) as month,
    SUM(sp.price_cents) as revenue_cents
FROM user_subscriptions us
JOIN subscription_plans sp ON us.plan_id = sp.id
WHERE us.status = 'active'
GROUP BY month
ORDER BY month;

-- User usage patterns
SELECT 
    sp.name as plan_name,
    AVG(uu.messages_used) as avg_messages,
    AVG(uu.api_calls_used) as avg_api_calls
FROM user_usage uu
JOIN user_subscriptions us ON uu.user_id = us.user_id
JOIN subscription_plans sp ON us.plan_id = sp.id
WHERE us.status = 'active'
GROUP BY sp.name;
```

## 🔧 Troubleshooting

### Common Issues

1. **"Subscription service not found"**
   - Make sure you've added the import: `from services.subscription_service import subscription_service`

2. **"Database function not found"**
   - Ensure you've run the SQL script in Supabase
   - Check that all functions were created successfully

3. **"Usage not tracking"**
   - Verify the `track_usage()` call is in your OpenAI service
   - Check database permissions

4. **"Plans not loading"**
   - Verify subscription plans were inserted into the database
   - Check API routes are registered

## 🎯 Next Steps

1. **Run the SQL script** to create tables
2. **Update your main app** to include subscription routes
3. **Test the subscription flow** with your existing account
4. **Integrate payment processing** (Stripe recommended)
5. **Set up monitoring** for usage and costs
6. **Launch your monetized version**!

## 💰 Revenue Projections

With a $20/month Premium plan:
- **100 users** = $2,000/month
- **500 users** = $10,000/month
- **1,000 users** = $20,000/month

Even with a 10% conversion rate from free to premium:
- **1,000 free users** → **100 premium users** = $2,000/month

## 📞 Support

If you need help implementing this system:
1. Check the troubleshooting section
2. Review the SQL script for database setup
3. Verify all imports and route registrations
4. Test with a small number of users first

Your monetization system is now ready to generate revenue! 🚀 