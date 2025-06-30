#!/bin/bash
# Startup script for Railway deployment
# Runs database migrations before starting the app

echo "🚀 Starting SmartTicker deployment..."

# Run database migrations
echo "📊 Running database migrations..."
python migrate_database.py

# Check if migrations succeeded
if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed, but continuing with deployment..."
fi

# Start the application
echo "🌐 Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT main:app