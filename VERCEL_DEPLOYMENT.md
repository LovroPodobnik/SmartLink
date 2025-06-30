# Deploying SmartTicker to Vercel

## Why Vercel?
- **Automatic Custom Domain API**: Programmatically add customer domains
- **Python Support**: Full support for Flask applications
- **Global Edge Network**: Fast performance worldwide
- **Automatic SSL**: Free SSL certificates for all domains

## Prerequisites
1. Vercel account
2. External PostgreSQL database (Supabase, Neon, or keep using Railway's database)
3. Vercel CLI installed: `npm i -g vercel`

## Step 1: Database Setup
Since Vercel doesn't provide databases, you'll need an external PostgreSQL service:

### Option A: Use Supabase (Recommended)
1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Copy the connection string from Settings → Database

### Option B: Keep Railway Database
- Continue using your existing Railway PostgreSQL database
- Just copy the `DATABASE_URL` from Railway

## Step 2: Vercel API Token
1. Go to [vercel.com/account/tokens](https://vercel.com/account/tokens)
2. Create new token with full access
3. Save the token for environment variables

## Step 3: Deploy to Vercel

### Via CLI:
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Follow prompts to:
# - Link to existing project or create new
# - Configure project settings
```

### Via GitHub:
1. Push code to GitHub
2. Import project at [vercel.com/new](https://vercel.com/new)
3. Configure environment variables

## Step 4: Environment Variables
Add these in Vercel Dashboard → Settings → Environment Variables:

```env
# Flask
FLASK_SECRET_KEY=generate-a-secure-key
SESSION_SECRET=generate-another-secure-key

# Database (from Supabase/Neon/Railway)
DATABASE_URL=postgresql://...

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Vercel API (for custom domains)
VERCEL_API_TOKEN=your-vercel-api-token
VERCEL_PROJECT_ID=prj_xxxxx (from Vercel dashboard)
VERCEL_APP_DOMAIN=your-app.vercel.app

# Production
FLASK_ENV=production
DEBUG=False
```

## Step 5: Update Domain Instructions
Your customers will need to point their domains to:
- **CNAME**: `cname.vercel-dns.com`

## Step 6: Test Custom Domain Flow
1. Login to your app
2. Add a custom domain
3. Follow DNS verification
4. Domain should be automatically added to Vercel!

## Advantages Over Railway
1. **Programmatic Domain API**: Full API support for custom domains
2. **No Manual Steps**: Customers' domains are added automatically
3. **Better Documentation**: Comprehensive API docs
4. **Scalability**: Vercel's edge network handles any traffic

## Migration Checklist
- [ ] Set up external PostgreSQL database
- [ ] Create Vercel account and API token
- [ ] Deploy application to Vercel
- [ ] Configure all environment variables
- [ ] Update DNS for your main domain
- [ ] Test custom domain automation
- [ ] Migrate existing custom domains

## API Usage
The Vercel API integration in `vercel_api.py` handles:
- Automatic domain addition
- SSL certificate provisioning
- Domain verification status
- Domain removal

No manual intervention required!