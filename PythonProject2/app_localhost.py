from flask import Flask, request, jsonify, send_file, Response, stream_with_context, make_response, send_from_directory
from flask_cors import CORS
import pandas as pd
import io
import re
from datetime import datetime
import zipfile
import os
import logging
from collections import Counter
import werkzeug
from werkzeug.serving import make_server
from werkzeug.middleware.proxy_fix import ProxyFix
import signal
import sys
import threading
import queue
import json
import uuid
from io import BytesIO
import csv
import tempfile
import shutil
import traceback
import socket
from werkzeug.utils import secure_filename
from flask_cors import CORS

# Import payment mode routes
from routes.bdo_routes import bdo_bp
from routes.cebuana_routes import cebuana_bp
from routes.chinabank_routes import chinabank_bp
from routes.ecpay_routes import ecpay_bp
from routes.metrobank_routes import metrobank_bp
from routes.unionbank_routes import unionbank_bp
from routes.sm_routes import sm_bp
from routes.pnb_routes import pnb_bp
from routes.cis_routes import cis_bp
from routes.bancnet_routes import bancnet_bp
from routes.robinsons_routes import robinsons_bp
from routes.export_routes import export_bp

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the absolute path to the project root directory
project_root = os.path.abspath(os.path.dirname(__file__))
static_folder = os.path.join(project_root, 'dist')

app = Flask(__name__,
            static_folder=static_folder,
            static_url_path='')
app.wsgi_app = ProxyFix(app.wsgi_app)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Configure upload folder
UPLOAD_FOLDER = os.path.join(project_root, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max file size

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Store processing status and results
processing_status = {}
processing_results = {}

# Register payment mode blueprints
app.register_blueprint(bdo_bp, url_prefix='/api/bdo')
app.register_blueprint(cebuana_bp, url_prefix='/api/cebuana')
app.register_blueprint(chinabank_bp, url_prefix='/api/chinabank')
app.register_blueprint(ecpay_bp, url_prefix='/api/ecpay')
app.register_blueprint(metrobank_bp, url_prefix='/api/metrobank')
app.register_blueprint(unionbank_bp, url_prefix='/api/unionbank')
app.register_blueprint(sm_bp, url_prefix='/api/sm')
app.register_blueprint(pnb_bp, url_prefix='/api/pnb')
app.register_blueprint(cis_bp, url_prefix='/api/cis')
app.register_blueprint(bancnet_bp, url_prefix='/api/bancnet')
app.register_blueprint(robinsons_bp, url_prefix='/api/robinsons')
app.register_blueprint(export_bp, url_prefix='/api/export')

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Splitter API is running',
        'available_payment_modes': ['bdo', 'cebuana', 'chinabank', 'ecpay', 'metrobank', 'unionbank', 'sm', 'pnb', 'cis', 'bancnet', 'robinsons'],
        'version': '1.0.0'
    })

# Serve React app
@app.route('/')
def index():
    """Serve the React app"""
    try:
        return send_from_directory(static_folder, 'index.html')
    except FileNotFoundError:
        return jsonify({
            'message': 'Splitter API is running',
            'frontend': 'Not built yet - run npm run build in splitter/ directory',
            'endpoints': ['/api/health', '/api/bdo/*', '/api/cebuana/*', '/api/chinabank/*', '/api/ecpay/*']
        })

CORS(app, origins="*")

if __name__ == '__main__':
    print("Starting Splitter Backend on localhost...")
    print("Backend will be available at: http://localhost:5000")
    print("Health check: http://localhost:5000/api/health")
    print("Press Ctrl+C to stop the server")
    
    # Run on localhost only
    #pag irrun as localhost use host='127.0.0.1'
    app.run(host='127.0.0.1', port=5000, debug=False)
