from flask import render_template, request, redirect, url_for, flash, session, jsonify, abort
from datetime import datetime, timedelta
from sqlalchemy import text
from app import app, db
from models import User, SmartLink, Click, LoginToken, CustomDomain
from forms import LoginForm, SmartLinkForm, CustomDomainForm
from utils import (
    is_bot_user_agent, get_platform_from_referrer, get_platform_from_user_agent,
    is_suspicious_request, send_magic_link_email, truncate_ip,
    verify_domain_ownership, get_domain_from_request, is_custom_domain,
    is_tiktok_bot, detect_platform_from_request, analyze_request_fingerprint
)
from detection_engine import enhanced_bot_detection, is_sophisticated_tiktok_bot
from vercel_api import get_vercel_manager

@app.route('/')
def index():
    """Landing page - handles both main domain and custom domains"""
    current_domain = get_domain_from_request()
    
    # Check if this is a custom domain
    if is_custom_domain(current_domain):
        # This is a customer's custom domain
        custom_domain = CustomDomain.query.filter_by(domain=current_domain, is_verified=True, is_active=True).first()
        
        if custom_domain:
            # Show custom domain landing page
            return render_template('custom_domain_index.html', domain=custom_domain)
        else:
            # Custom domain not found or not verified
            abort(404, description=f"Domain {current_domain} not found or not properly configured.")
    
    # This is your main SmartTicker domain - show normal homepage
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with magic link"""
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        
        # Get or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            db.session.add(user)
            db.session.commit()
        
        # Create login token
        token = LoginToken(user_id=user.id)
        db.session.add(token)
        db.session.commit()
        
        # Development mode: Skip email and auto-login
        if app.config.get('ENV') == 'development' or not app.config.get('MAIL_USERNAME'):
            flash(f'Development mode: Auto-logged in as {email}', 'success')
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        
        # Send magic link
        if send_magic_link_email(email, token.token):
            flash('Check your email for a magic link to sign in!', 'success')
        else:
            flash('Email service not configured. Development login: Click login again to auto-sign in.', 'warning')
            # Auto-login on second attempt when email fails
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        
        return redirect(url_for('login'))
    
    return render_template('login.html', form=form)

@app.route('/auth/verify/<token>')
def verify_login(token):
    """Verify magic link token"""
    login_token = LoginToken.query.filter_by(token=token, used=False).first()
    
    if not login_token or login_token.expires_at < datetime.utcnow():
        flash('Invalid or expired login link.', 'error')
        return redirect(url_for('login'))
    
    # Mark token as used
    login_token.used = True
    db.session.commit()
    
    # Log in user
    session['user_id'] = login_token.user_id
    flash('Successfully logged in!', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

def login_required(f):
    """Decorator to require login"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get user's smart links
    smart_links = SmartLink.query.filter_by(user_id=user_id).all()
    
    # Calculate stats for each link
    links_with_stats = []
    total_human_clicks = 0
    total_bot_clicks = 0
    total_all_clicks = 0
    
    for link in smart_links:
        total_clicks = Click.query.filter_by(smart_link_id=link.id).count()
        human_clicks = Click.query.filter_by(smart_link_id=link.id, click_type='human').count()
        bot_clicks = Click.query.filter_by(smart_link_id=link.id, click_type='bot').count()
        
        links_with_stats.append({
            'link': link,
            'total_clicks': total_clicks,
            'human_clicks': human_clicks,
            'bot_clicks': bot_clicks
        })
        
        total_human_clicks += human_clicks
        total_bot_clicks += bot_clicks
        total_all_clicks += total_clicks
    
    stats = {
        'total_links': len(smart_links),
        'total_clicks': total_all_clicks,
        'human_clicks': total_human_clicks,
        'bot_clicks': total_bot_clicks
    }
    
    return render_template('dashboard.html', user=user, links_with_stats=links_with_stats, stats=stats)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_link():
    """Create new smart link"""
    form = SmartLinkForm()
    
    # Get user's verified custom domains
    user_id = session['user_id']
    verified_domains = CustomDomain.query.filter_by(
        user_id=user_id,
        is_verified=True,
        is_active=True
    ).all()
    
    # Set up domain choices - use string values to avoid coercion issues
    domain_choices = [('', 'Default Domain (SmartLink)')] + [
        (str(domain.id), domain.domain) for domain in verified_domains
    ]
    form.custom_domain_id.choices = domain_choices
    
    if form.validate_on_submit():
        # Handle domain selection
        custom_domain_id = form.custom_domain_id.data if form.custom_domain_id.data else None
        
        smart_link = SmartLink(
            user_id=session['user_id'],
            custom_domain_id=custom_domain_id,
            title=form.title.data,
            description=form.description.data,
            target_url=form.target_url.data,
            safe_url=form.safe_url.data if form.safe_url.data else None,
            use_js_challenge=form.use_js_challenge.data,
            direct_from_tiktok=form.direct_from_tiktok.data
        )
        
        db.session.add(smart_link)
        db.session.commit()
        
        # Generate appropriate success message with full URL
        full_url = smart_link.get_full_url(request.host)
        flash(f'Smart link created! URL: {full_url}', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('create_link.html', form=form, verified_domains=verified_domains)

@app.route('/analytics/<short_code>')
@login_required
def analytics(short_code):
    """Analytics for a specific smart link"""
    user_id = session['user_id']
    smart_link = SmartLink.query.filter_by(short_code=short_code, user_id=user_id).first()
    
    if not smart_link:
        abort(404)
    
    # Get click analytics for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Daily clicks
    daily_clicks = db.session.query(
        db.func.date(Click.created_at).label('date'),
        db.func.count(Click.id).label('total'),
        db.func.sum(db.case((Click.click_type == 'human', 1), else_=0)).label('human'),
        db.func.sum(db.case((Click.click_type == 'bot', 1), else_=0)).label('bot'),
        db.func.sum(db.case((Click.click_type == 'suspect', 1), else_=0)).label('suspect')
    ).filter(
        Click.smart_link_id == smart_link.id,
        Click.created_at >= thirty_days_ago
    ).group_by(db.func.date(Click.created_at)).order_by('date').all()
    
    # Platform breakdown
    platform_clicks = db.session.query(
        Click.platform,
        db.func.count(Click.id).label('count')
    ).filter(
        Click.smart_link_id == smart_link.id,
        Click.created_at >= thirty_days_ago
    ).group_by(Click.platform).all()
    
    return render_template('analytics.html', 
                         smart_link=smart_link, 
                         daily_clicks=daily_clicks,
                         platform_clicks=platform_clicks)

@app.route('/<short_code>')
def smart_redirect(short_code):
    """Smart redirect endpoint - core functionality"""
    # Get the current domain from the request
    current_domain = request.host
    
    # Find the smart link by short code
    smart_link = SmartLink.query.filter_by(short_code=short_code, is_active=True).first()
    
    if not smart_link:
        abort(404)
    
    # Check if this request is coming from a custom domain
    if smart_link.custom_domain and smart_link.custom_domain.domain != current_domain:
        # If the link has a custom domain but request is from different domain, redirect to correct domain
        if smart_link.custom_domain.is_verified and smart_link.custom_domain.is_active:
            protocol = 'https' if smart_link.custom_domain.ssl_enabled else 'http'
            correct_url = f"{protocol}://{smart_link.custom_domain.domain}/{short_code}"
            return redirect(correct_url, code=301)
    
    # Get request details
    user_agent = request.headers.get('User-Agent', '')
    referrer = request.headers.get('Referer', '')
    ip_address = request.remote_addr
    
    # Advanced detection engine analysis
    detection_result = enhanced_bot_detection(user_agent, ip_address)
    
    # Legacy detection methods for fallback
    is_bot_legacy = is_bot_user_agent(user_agent)
    is_tiktok_legacy = is_tiktok_bot(user_agent, ip_address)
    is_suspicious = is_suspicious_request()
    
    # Enhanced detection with confidence scoring
    is_bot = detection_result.is_bot or is_bot_legacy
    is_tiktok = is_sophisticated_tiktok_bot(user_agent, ip_address) or is_tiktok_legacy
    platform = detection_result.platform
    confidence_score = detection_result.confidence_score
    risk_level = detection_result.risk_level
    
    # Platform-specific routing logic
    if is_bot or is_tiktok:
        # Bot detected - send to platform-specific safe page
        click_type = 'bot'
        target_reached = 'safe'
        
        # Use platform-specific safe page if available
        if platform == 'tiktok':
            redirect_url = url_for('safe_page_tiktok', short_code=short_code, _external=True)
        elif platform in ['instagram', 'facebook']:
            redirect_url = url_for('safe_page_instagram', short_code=short_code, _external=True)
        else:
            # Fallback to custom safe URL or generic safe page
            redirect_url = smart_link.safe_url or url_for('safe_page', short_code=short_code, _external=True)
            
    elif is_suspicious and smart_link.use_js_challenge:
        # Suspicious request - JavaScript challenge
        click_type = 'suspect'
        target_reached = 'challenge'
        redirect_url = url_for('js_challenge', short_code=short_code, _external=True)
    else:
        # Human user - direct to target (OnlyFans/target URL)
        click_type = 'human'
        target_reached = 'target'
        redirect_url = smart_link.target_url
    
    # Log the click with enhanced analytics
    import json
    click = Click(
        smart_link_id=smart_link.id,
        ip_address=truncate_ip(ip_address),
        user_agent=user_agent[:500] if user_agent else None,
        referrer=referrer[:500] if referrer else None,
        click_type=click_type,
        target_reached=target_reached,
        platform=platform,
        confidence_score=confidence_score,
        risk_level=risk_level,
        detection_methods=json.dumps(detection_result.detection_methods)
    )
    db.session.add(click)
    db.session.commit()
    
    return redirect(redirect_url)

@app.route('/safe/<short_code>')
def safe_page(short_code):
    """Generic safe landing page for bots"""
    smart_link = SmartLink.query.filter_by(short_code=short_code, is_active=True).first()
    
    if not smart_link:
        abort(404)
    
    return render_template('safe_page.html', smart_link=smart_link)

@app.route('/safe/tiktok/<short_code>')
def safe_page_tiktok(short_code):
    """TikTok-optimized safe landing page"""
    smart_link = SmartLink.query.filter_by(short_code=short_code, is_active=True).first()
    
    if not smart_link:
        abort(404)
    
    return render_template('safe_page_tiktok.html', smart_link=smart_link)

@app.route('/safe/instagram/<short_code>')
def safe_page_instagram(short_code):
    """Instagram-optimized safe landing page"""
    smart_link = SmartLink.query.filter_by(short_code=short_code, is_active=True).first()
    
    if not smart_link:
        abort(404)
    
    return render_template('safe_page_instagram.html', smart_link=smart_link)

@app.route('/challenge/<short_code>')
def js_challenge(short_code):
    """JavaScript challenge page for suspicious requests"""
    smart_link = SmartLink.query.filter_by(short_code=short_code, is_active=True).first()
    
    if not smart_link:
        abort(404)
    
    return render_template('js_challenge.html', smart_link=smart_link)

@app.route('/challenge/<short_code>/verify', methods=['POST'])
def verify_js_challenge(short_code):
    """Verify JavaScript challenge completion"""
    smart_link = SmartLink.query.filter_by(short_code=short_code, is_active=True).first()
    
    if not smart_link:
        abort(404)
    
    # Get challenge response
    challenge_response = request.json.get('challenge_response')
    expected_response = request.json.get('expected_response')
    
    # Verify the challenge
    if challenge_response == expected_response:
        # Challenge passed - redirect to target
        return jsonify({
            'success': True,
            'redirect_url': smart_link.target_url
        })
    else:
        # Challenge failed - send to safe page
        return jsonify({
            'success': False,
            'redirect_url': url_for('safe_page', short_code=short_code, _external=True)
        })

@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard stats"""
    user_id = session['user_id']
    
    # Get overall stats for user
    total_links = SmartLink.query.filter_by(user_id=user_id).count()
    total_clicks = db.session.query(db.func.count(Click.id)).join(SmartLink).filter(SmartLink.user_id == user_id).scalar()
    human_clicks = db.session.query(db.func.count(Click.id)).join(SmartLink).filter(
        SmartLink.user_id == user_id, Click.click_type == 'human'
    ).scalar()
    
    return jsonify({
        'total_links': total_links or 0,
        'total_clicks': total_clicks or 0,
        'human_clicks': human_clicks or 0,
        'bot_clicks': (total_clicks or 0) - (human_clicks or 0)
    })

@app.route('/domains')
@login_required
def manage_domains():
    """Manage custom domains"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    domains = CustomDomain.query.filter_by(user_id=user_id).all()
    
    return render_template('domains.html', user=user, domains=domains)

@app.route('/domains/add', methods=['GET', 'POST'])
@login_required
def add_domain():
    """Add a new custom domain"""
    form = CustomDomainForm()
    
    if form.validate_on_submit():
        domain = form.domain.data.lower().strip()
        
        # Check if domain already exists
        existing_domain = CustomDomain.query.filter_by(domain=domain).first()
        if existing_domain:
            flash('This domain is already registered.', 'error')
            return redirect(url_for('add_domain'))
        
        # Create new domain
        custom_domain = CustomDomain(
            user_id=session['user_id'],
            domain=domain
        )
        
        db.session.add(custom_domain)
        db.session.commit()
        
        flash(f'Domain {domain} added! Please verify ownership to activate it.', 'success')
        return redirect(url_for('verify_domain', domain_id=custom_domain.id))
    
    return render_template('add_domain.html', form=form)

@app.route('/domains/<int:domain_id>/verify')
@login_required
def verify_domain(domain_id):
    """Show domain verification instructions"""
    user_id = session['user_id']
    domain = CustomDomain.query.filter_by(id=domain_id, user_id=user_id).first()
    
    if not domain:
        abort(404)
    
    return render_template('verify_domain_simple.html', domain=domain)

@app.route('/domains/<int:domain_id>/check', methods=['POST'])
@login_required
def check_domain_verification(domain_id):
    """Check if domain verification is complete and auto-add to Railway"""
    user_id = session['user_id']
    domain = CustomDomain.query.filter_by(id=domain_id, user_id=user_id).first()
    
    if not domain:
        abort(404)
    
    # Verify domain ownership using the configured method
    verification_method = domain.verification_method or 'dns'
    if verify_domain_ownership(domain.domain, domain.verification_token, verification_method):
        domain.is_verified = True
        domain.verified_at = datetime.utcnow()
        
        # 🚀 AUTO-ADD TO VERCEL
        try:
            vercel_manager = get_vercel_manager()
            vercel_result = vercel_manager.add_custom_domain(domain.domain)
            
            if vercel_result:
                status = vercel_result.get('status', 'unknown')
                domain_id = vercel_result.get('id')
                
                if status == 'existing':
                    # Domain already exists in Vercel
                    domain.ssl_enabled = True
                    app.logger.info(f"Domain {domain.domain} already exists in Vercel")
                    flash(f'Domain {domain.domain} successfully verified! The domain is already configured.', 'success')
                elif status == 'verified':
                    # Domain successfully added and verified
                    domain.ssl_enabled = True
                    app.logger.info(f"Domain {domain.domain} added to Vercel with ID {domain_id}")
                    flash(f'Domain {domain.domain} successfully verified and activated! SSL enabled automatically.', 'success')
                elif status == 'pending_verification':
                    # Domain added but needs Vercel verification
                    app.logger.info(f"Domain {domain.domain} added to Vercel, pending platform verification")
                    flash(f'Domain {domain.domain} added! Vercel is verifying the domain configuration. This may take a few minutes.', 'info')
                else:
                    # Unknown status
                    app.logger.warning(f"Unknown status for domain {domain.domain}: {status}")
                    flash(f'Domain {domain.domain} processed with status: {status}', 'warning')
            else:
                app.logger.warning(f"Domain {domain.domain} verified but Vercel setup failed")
                flash(f'Domain {domain.domain} verified but automatic setup failed. Please contact support.', 'warning')
                
        except Exception as e:
            app.logger.error(f"Vercel API error for domain {domain.domain}: {str(e)}")
            flash(f'Domain {domain.domain} verified but automatic setup failed: {str(e)}', 'warning')
        
        db.session.commit()
        return redirect(url_for('manage_domains'))
    else:
        method_name = 'DNS TXT record' if verification_method == 'dns' else 'verification file'
        flash(f'Domain verification failed. Please check your {method_name}.', 'error')
        return redirect(url_for('verify_domain', domain_id=domain.id))

@app.route('/domains/<int:domain_id>/delete', methods=['POST'])
@login_required
def delete_domain(domain_id):
    """Delete a custom domain and remove from Railway"""
    user_id = session['user_id']
    domain = CustomDomain.query.filter_by(id=domain_id, user_id=user_id).first()
    
    if not domain:
        abort(404)
    
    # Remove from Railway if it was added there
    # TODO: Implement Railway domain deletion after storing railway_domain_id
    try:
        app.logger.info(f"Domain {domain.domain} being deleted - Railway cleanup may be needed")
    except Exception as e:
        app.logger.error(f"Error during domain deletion for {domain.domain}: {str(e)}")
    
    db.session.delete(domain)
    db.session.commit()
    
    flash(f'Domain {domain.domain} deleted successfully.', 'success')
    return redirect(url_for('manage_domains'))

@app.route('/test')
def test_domain():
    """Test endpoint to check if custom domain routing is working"""
    current_domain = request.host
    return f"""
    <h1>SmartLink Domain Test</h1>
    <p><strong>Current Domain:</strong> {current_domain}</p>
    <p><strong>Status:</strong> ✅ Domain routing is working!</p>
    <p>If you can see this page on your custom domain, the routing is configured correctly.</p>
    <hr>
    <small>Now create a SmartLink using this domain and test the short URLs.</small>
    """

@app.route('/health')
def health_check():
    """Health check endpoint for deployment monitoring"""
    import os
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        db_status = "✅ Connected"
    except Exception as e:
        db_status = f"❌ Error: {str(e)[:100]}"
    
    return {
        "status": "ok",
        "database": db_status,
        "environment": os.environ.get('FLASK_ENV', 'unknown'),
        "version": "1.0.0"
    }

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404
