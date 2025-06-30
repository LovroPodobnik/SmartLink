"""Simple health check endpoint for Railway"""
from flask import jsonify
from app import app, db

@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    try:
        # Simple database connectivity check
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'service': 'SmartTicker',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'SmartTicker',
            'database': 'error',
            'error': str(e)
        }), 503