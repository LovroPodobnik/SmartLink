from flask import render_template, request, redirect, url_for, flash, session, jsonify, abort
from datetime import datetime, timedelta
from app import app, db
from models import User, SmartLink, Click, LoginToken, CustomDomain
from forms import LoginForm, SmartLinkForm, CustomDomainForm
from utils import (
    is_bot_user_agent, get_platform_from_referrer, get_platform_from_user_agent,
    is_suspicious_request, send_magic_link_email, truncate_ip,
    verify_domain_ownership, get_domain_from_request, is_custom_domain
)

@app.route('/')
def index():
    """Landing page"""
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
    smart_link = SmartLink.query.filter_by(short_code=short_code, is_active=True).first()
    
    if not smart_link:
        abort(404)
    
    # Get request details
    user_agent = request.headers.get('User-Agent', '')
    referrer = request.headers.get('Referer', '')
    ip_address = request.remote_addr
    
    # Determine platform and click type
    platform = get_platform_from_referrer(referrer) or get_platform_from_user_agent(user_agent)
    
    # Decision logic
    is_bot = is_bot_user_agent(user_agent)
    is_suspicious = is_suspicious_request()
    
    # Determine redirect target and click type
    if is_bot:
        # Bot detected - send to safe page
        click_type = 'bot'
        target_reached = 'safe'
        redirect_url = smart_link.safe_url or url_for('safe_page', short_code=short_code, _external=True)
    elif is_suspicious and smart_link.use_js_challenge:
        # Suspicious request - JavaScript challenge
        click_type = 'suspect'
        target_reached = 'challenge'
        redirect_url = url_for('js_challenge', short_code=short_code, _external=True)
    else:
        # Human user - direct to target
        click_type = 'human'
        target_reached = 'target'
        redirect_url = smart_link.target_url
    
    # Log the click
    click = Click(
        smart_link_id=smart_link.id,
        ip_address=truncate_ip(ip_address),
        user_agent=user_agent[:500] if user_agent else None,
        referrer=referrer[:500] if referrer else None,
        click_type=click_type,
        target_reached=target_reached,
        platform=platform
    )
    db.session.add(click)
    db.session.commit()
    
    return redirect(redirect_url)

@app.route('/safe/<short_code>')
def safe_page(short_code):
    """Safe landing page for bots"""
    smart_link = SmartLink.query.filter_by(short_code=short_code, is_active=True).first()
    
    if not smart_link:
        abort(404)
    
    return render_template('safe_page.html', smart_link=smart_link)

@app.route('/challenge/<short_code>')
def js_challenge(short_code):
    """JavaScript challenge page for suspicious requests"""
    smart_link = SmartLink.query.filter_by(short_code=short_code, is_active=True).first()
    
    if not smart_link:
        abort(404)
    
    # For now, redirect to safe page
    # In production, this would show a JS challenge
    return redirect(url_for('safe_page', short_code=short_code))

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
    
    return render_template('verify_domain.html', domain=domain)

@app.route('/domains/<int:domain_id>/check', methods=['POST'])
@login_required
def check_domain_verification(domain_id):
    """Check if domain verification is complete"""
    user_id = session['user_id']
    domain = CustomDomain.query.filter_by(id=domain_id, user_id=user_id).first()
    
    if not domain:
        abort(404)
    
    # Verify domain ownership
    if verify_domain_ownership(domain.domain, domain.verification_token):
        domain.is_verified = True
        domain.verified_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Domain {domain.domain} successfully verified!', 'success')
        return redirect(url_for('manage_domains'))
    else:
        flash('Domain verification failed. Please check your verification file.', 'error')
        return redirect(url_for('verify_domain', domain_id=domain.id))

@app.route('/domains/<int:domain_id>/delete', methods=['POST'])
@login_required
def delete_domain(domain_id):
    """Delete a custom domain"""
    user_id = session['user_id']
    domain = CustomDomain.query.filter_by(id=domain_id, user_id=user_id).first()
    
    if not domain:
        abort(404)
    
    db.session.delete(domain)
    db.session.commit()
    
    flash(f'Domain {domain.domain} deleted successfully.', 'success')
    return redirect(url_for('manage_domains'))

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404
