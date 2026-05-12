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

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Increase the maximum content length to 1GB
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB in bytes

# Increase the timeout to 30 minutes
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1800  # 30 minutes

# Disable signal handling that might cause abortions
signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)

# Create a queue for processing results
processing_queue = queue.Queue()

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

# Test SM endpoint
@app.route('/api/sm/test')
def test_sm():
    return jsonify({
        'status': 'SM endpoint is working',
        'message': 'SM blueprint is properly registered'
    })

# Serve React app
@app.route('/')
def serve():
    """Serve the React app"""
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return jsonify({'error': 'Could not serve the application'}), 500

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from the dist folder"""
    try:
        return send_from_directory(app.static_folder, path)
    except Exception as e:
        logger.error(f"Error serving static file {path}: {str(e)}")
        return jsonify({'error': 'Could not serve the file'}), 404

if __name__ == '__main__':
    # Get your computer's IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"\nAccess the application from other computers using:")
    print(f"http://{local_ip}:5000")
    print(f"\nMake sure your firewall allows connections on port 5000")
    print(f"Project root: {project_root}")
    print(f"Static folder path: {static_folder}")
    print(f"Static folder exists: {os.path.exists(static_folder)}")
    print(f"Index.html exists: {os.path.exists(os.path.join(static_folder, 'index.html'))}")

    # Create a custom server with increased timeout and thread support
    server = make_server('0.0.0.0', 5000, app)
    server.timeout = 1800  # 30 minutes timeout

    # Set server options to handle large files
    server.max_request_body_size = 1024 * 1024 * 1024  # 1GB
    server.max_request_header_size = 1024 * 1024  # 1MB

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        sys.exit(0)
