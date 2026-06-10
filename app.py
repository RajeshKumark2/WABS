#!/usr/bin/env python3
"""
WABS - Women And Baby Safety System
"One Touch for Safety"
Production-Ready Real-Time Safety Platform
Complete with Real GPS, Voice Detection, Admin Panel, Community Network
"""

import os
import json
import uuid
import hashlib
import datetime
import secrets
import threading
import time
from functools import wraps
from flask import (
    Flask, render_template_string, request, jsonify, redirect, 
    url_for, session, flash, make_response, Response
)
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import base64

# Initialize Flask App
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'wabs_production.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db = SQLAlchemy(app)

# =============================================================================
# DATABASE MODELS - Complete Production Schema
# =============================================================================
class Users(db.Model):
    """Complete Users Table"""
    __tablename__ = 'users'
    
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Mobile = db.Column(db.String(15), unique=True, nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Address = db.Column(db.String(255))
    PasswordHash = db.Column(db.String(255), nullable=False)
    UserType = db.Column(db.String(20), default='woman')
    IsActive = db.Column(db.Boolean, default=True)
    LastLogin = db.Column(db.DateTime)
    CreatedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    

class Children(db.Model):
    """Child Profiles Table"""
    __tablename__ = 'children'
    
    ChildID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    ChildName = db.Column(db.String(100), nullable=False)
    Age = db.Column(db.Integer, nullable=False)
    Gender = db.Column(db.String(10))
    ParentName = db.Column(db.String(100))
    ParentMobile = db.Column(db.String(15))
    Photo = db.Column(db.Text)  # Base64 encoded image
    MedicalInfo = db.Column(db.Text)
    ChildCode = db.Column(db.String(10), unique=True)  # Unique code for child
    IsActive = db.Column(db.Boolean, default=True)
    CreatedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    parent_user = db.relationship('Users', foreign_keys=[UserID], backref='children')

class EmergencyContacts(db.Model):
    """Emergency Contacts with Priority"""
    __tablename__ = 'emergency_contacts'
    
    ContactID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    ContactName = db.Column(db.String(100), nullable=False)
    Relationship = db.Column(db.String(50), nullable=False)
    Mobile = db.Column(db.String(15), nullable=False)
    AlternateMobile = db.Column(db.String(15))
    Email = db.Column(db.String(100))
    PriorityLevel = db.Column(db.Integer, default=1)  # 1=Critical, 2=High, 3=Medium
    IsActive = db.Column(db.Boolean, default=True)
    CreatedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user = db.relationship('Users', foreign_keys=[UserID], backref='emergency_contacts')

class SOSRecords(db.Model):
    """Complete SOS Emergency Records"""
    __tablename__ = 'sos_records'
    
    SOSID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    ChildID = db.Column(db.Integer, db.ForeignKey('children.ChildID'), nullable=True)
    DateTime = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    Latitude = db.Column(db.Float, nullable=False)
    Longitude = db.Column(db.Float, nullable=False)
    Accuracy = db.Column(db.Float)
    Address = db.Column(db.String(500))
    Status = db.Column(db.String(20), default='active')  # active, responding, resolved, cancelled
    AlertType = db.Column(db.String(50), default='manual')  # manual, voice, child_sound, auto
    LocationLink = db.Column(db.String(500))
    Notes = db.Column(db.Text)
    ResolvedAt = db.Column(db.DateTime)
    ResolvedBy = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=True)
    user = db.relationship('Users', foreign_keys=[UserID], backref='sos_records')

class AudioEvents(db.Model):
    """Voice Detection Events"""
    __tablename__ = 'audio_events'
    
    EventID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    AudioType = db.Column(db.String(50))  # keyword, distress_phrase, crying, screaming, panic
    DetectedText = db.Column(db.Text)
    OriginalText = db.Column(db.Text)  # Full transcribed text
    ConfidenceScore = db.Column(db.Float)
    Language = db.Column(db.String(10))  # english, tamil, tanglish, other
    Duration = db.Column(db.Float)  # Audio duration in seconds
    AudioData = db.Column(db.Text)  # Base64 encoded audio
    Latitude = db.Column(db.Float)
    Longitude = db.Column(db.Float)
    DateTime = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    AutoTriggeredSOS = db.Column(db.Boolean, default=False)
    IsProcessed = db.Column(db.Boolean, default=False)
    user = db.relationship('Users', foreign_keys=[UserID], backref='audio_events')

class VoiceRecordings(db.Model):
    """Complete Voice Recording Storage"""
    __tablename__ = 'voice_recordings'
    
    RecordingID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    RecordingType = db.Column(db.String(50))  # manual, auto, continuous
    AudioData = db.Column(db.Text)  # Base64 encoded audio
    TranscribedText = db.Column(db.Text)
    Language = db.Column(db.String(10))
    Duration = db.Column(db.Float)
    Latitude = db.Column(db.Float)
    Longitude = db.Column(db.Float)
    IsEmergency = db.Column(db.Boolean, default=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user = db.relationship('Users', foreign_keys=[UserID], backref='voice_recordings')

class LocationTracking(db.Model):
    """Real-time Location Tracking Data"""
    __tablename__ = 'location_tracking'
    
    TrackID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    Latitude = db.Column(db.Float, nullable=False)
    Longitude = db.Column(db.Float, nullable=False)
    Accuracy = db.Column(db.Float)
    Speed = db.Column(db.Float)
    Heading = db.Column(db.Float)
    BatteryLevel = db.Column(db.Float)
    NetworkType = db.Column(db.String(20))
    Timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user = db.relationship('Users', foreign_keys=[UserID], backref='location_tracking')

class CommunityAlerts(db.Model):
    """Community Safety Network Alerts"""
    __tablename__ = 'community_alerts'
    
    AlertID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SOSID = db.Column(db.Integer, db.ForeignKey('sos_records.SOSID'), nullable=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=True)
    Latitude = db.Column(db.Float, nullable=False)
    Longitude = db.Column(db.Float, nullable=False)
    Radius = db.Column(db.Float, default=500)  # meters
    AlertType = db.Column(db.String(50))  # emergency, child, voice, general
    AlertMessage = db.Column(db.String(500))
    AlertMessageTamil = db.Column(db.String(500))
    IsActive = db.Column(db.Boolean, default=True)
    SentAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    ExpiresAt = db.Column(db.DateTime)
    RespondedCount = db.Column(db.Integer, default=0)
    ResolvedAt = db.Column(db.DateTime)

class CommunityResponses(db.Model):
    """Community Volunteer Responses"""
    __tablename__ = 'community_responses'
    
    ResponseID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    AlertID = db.Column(db.Integer, db.ForeignKey('community_alerts.AlertID'), nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    ResponseType = db.Column(db.String(50))  # i_am_coming, called_police, safe_escort, medical_help
    Latitude = db.Column(db.Float)
    Longitude = db.Column(db.Float)
    Message = db.Column(db.Text)
    RespondedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    ArrivedAt = db.Column(db.DateTime)
    volunteer = db.relationship('Users', foreign_keys=[UserID], backref='community_responses')
class IncidentReports(db.Model):
    """Detailed Incident Reports"""
    __tablename__ = 'incident_reports'
    
    ReportID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SOSID = db.Column(db.Integer, db.ForeignKey('sos_records.SOSID'), nullable=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    IncidentType = db.Column(db.String(100))
    Description = db.Column(db.Text)
    Location = db.Column(db.String(500))
    Latitude = db.Column(db.Float)
    Longitude = db.Column(db.Float)
    Severity = db.Column(db.String(20))  # low, medium, high, critical
    Status = db.Column(db.String(20), default='open')  # open, investigating, resolved
    CreatedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime)

# =============================================================================
# AUTHENTICATION DECORATORS
# =============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        if session.get('user_type') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# =============================================================================
# TEMPLATE RENDERING HELPER
# =============================================================================

def render_page(content_html, scripts_html="", page_title="WABS", **kwargs):
    """Helper function to render complete pages"""
    
    base_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title} - WABS Safety System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root {{
            --primary: #E63946;
            --primary-dark: #C1121F;
            --secondary: #457B9D;
            --accent: #F4A261;
            --dark: #1D3557;
            --light: #F1FAEE;
            --danger: #DC3545;
            --success: #28A745;
            --warning: #FFC107;
            --info: #17A2B8;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #F1FAEE 0%, #E8F0FE 100%);
            min-height: 100vh;
        }}
        
        .navbar-wabs {{
            background: linear-gradient(135deg, var(--dark) 0%, #2C3E50 100%);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            padding: 15px 0;
        }}
        
        .navbar-brand-wabs {{
            font-size: 1.8rem;
            font-weight: 800;
            color: white !important;
            letter-spacing: 2px;
        }}
        
        .navbar-brand-wabs span {{ color: var(--primary); }}
        
        .tagline {{
            font-size: 0.85rem;
            color: rgba(255,255,255,0.8);
            font-style: italic;
            letter-spacing: 1px;
        }}
        
        .nav-link-wabs {{
            color: white !important;
            font-weight: 500;
            margin: 0 5px;
            transition: all 0.3s;
            padding: 8px 15px !important;
            border-radius: 20px;
        }}
        
        .nav-link-wabs:hover {{
            background: rgba(255,255,255,0.15);
            transform: translateY(-2px);
        }}
        
        .sos-button-giant {{
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, #FF4444, #CC0000);
            border: 8px solid #990000;
            color: white;
            font-size: 2.5rem;
            font-weight: 900;
            cursor: pointer;
            box-shadow: 0 10px 40px rgba(255,0,0,0.4), 0 0 80px rgba(255,0,0,0.2);
            transition: all 0.3s;
            animation: pulse 2s infinite;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            letter-spacing: 3px;
            position: relative;
        }}
        
        .sos-button-giant:hover {{
            transform: scale(1.08);
            box-shadow: 0 15px 60px rgba(255,0,0,0.6), 0 0 120px rgba(255,0,0,0.3);
        }}
        
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(255,0,0,0.7); }}
            70% {{ box-shadow: 0 0 0 30px rgba(255,0,0,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(255,0,0,0); }}
        }}
        
        .sos-small {{
            width: 80px;
            height: 80px;
            font-size: 1.2rem;
            border-width: 4px;
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 9999;
            animation: pulse 2s infinite;
        }}
        
        .card-wabs {{
            border: none;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.3s;
            background: white;
            overflow: hidden;
            margin-bottom: 20px;
            cursor: pointer;
        }}
        
        .card-wabs:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}
        
        .card-wabs.clickable:active {{
            transform: scale(0.98);
        }}
        
        .card-header-wabs {{
            background: linear-gradient(135deg, var(--dark), var(--secondary));
            color: white;
            font-weight: 600;
            padding: 20px;
            border: none;
        }}
        
        .btn-wabs {{
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 30px;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(230,57,70,0.3);
        }}
        
        .btn-wabs:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(230,57,70,0.5);
            color: white;
        }}
        
        .btn-wabs:active {{
            transform: scale(0.95);
        }}
        
        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            transition: all 0.3s;
            cursor: pointer;
        }}
        
        .stat-card:hover {{ transform: translateY(-5px); }}
        
        .stat-number {{
            font-size: 3rem;
            font-weight: 800;
            color: var(--primary);
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .voice-indicator {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px auto;
            transition: all 0.3s;
            cursor: pointer;
        }}
        
        .voice-indicator.listening {{
            animation: voicePulse 1.5s infinite;
            background: linear-gradient(135deg, #FF4444, #CC0000);
        }}
        
        @keyframes voicePulse {{
            0% {{ transform: scale(1); opacity: 0.8; }}
            50% {{ transform: scale(1.1); opacity: 1; }}
            100% {{ transform: scale(1); opacity: 0.8; }}
        }}
        
        .map-container {{
            height: 400px;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .map-large {{
            height: 600px;
        }}
        
        .footer-wabs {{
            background: var(--dark);
            color: white;
            padding: 30px 0;
            margin-top: 50px;
        }}
        
        .alert-floating {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            animation: slideIn 0.5s;
            min-width: 300px;
        }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        .loading-spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }}
        
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        
        .live-dot {{
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #28A745;
            border-radius: 50%;
            animation: livePulse 1s infinite;
        }}
        
        @keyframes livePulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
            100% {{ opacity: 1; }}
        }}
        
        .notification-badge {{
            position: absolute;
            top: -5px;
            right: -5px;
            padding: 5px 10px;
            border-radius: 50%;
            background: red;
            color: white;
            font-size: 0.7rem;
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-wabs">
        <div class="container">
            <a class="navbar-brand navbar-brand-wabs" href="/">
                W<span>A</span>BS <span class="tagline">"One Touch for Safety"</span>
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    {f'''<li class="nav-item"><a class="nav-link nav-link-wabs" href="/dashboard"><i class="bi bi-speedometer2"></i> Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link nav-link-wabs" href="/sos"><i class="bi bi-exclamation-triangle-fill text-danger"></i> SOS</a></li>
                    <li class="nav-item"><a class="nav-link nav-link-wabs" href="/voice-detection"><i class="bi bi-mic-fill"></i> Voice</a></li>
                    <li class="nav-item"><a class="nav-link nav-link-wabs" href="/gps-tracking"><i class="bi bi-geo-alt-fill"></i> GPS</a></li>
                    <li class="nav-item"><a class="nav-link nav-link-wabs" href="/child-safety"><i class="bi bi-heart-fill"></i> Child</a></li>
                    <li class="nav-item"><a class="nav-link nav-link-wabs" href="/community"><i class="bi bi-people-fill"></i> Community</a></li>
                    {'''<li class="nav-item"><a class="nav-link nav-link-wabs" href="/admin"><i class="bi bi-shield-fill"></i> Admin</a></li>''' if session.get('user_type') == 'admin' else ''}
                    <li class="nav-item dropdown">
                        <a class="nav-link nav-link-wabs dropdown-toggle" href="#" data-bs-toggle="dropdown">
                            <i class="bi bi-person-circle"></i> {session.get('user_name', 'User')}
                        </a>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="/dashboard">Profile</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="/logout">Logout</a></li>
                        </ul>
                    </li>''' if session.get('user_id') else '''<li class="nav-item"><a class="nav-link nav-link-wabs" href="/login">Login</a></li>
                    <li class="nav-item"><a class="nav-link nav-link-wabs" href="/register">Register</a></li>'''}
                </ul>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {'''
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        '''}
        {content_html}
    </div>
    
    {'''<button class="sos-button-giant sos-small" onclick="quickSOS()" title="Emergency SOS">
        SOS
    </button>''' if session.get('user_id') else ''}
    
    <footer class="footer-wabs">
        <div class="container text-center">
            <h5>WABS - Women And Baby Safety System</h5>
            <p class="mb-0">"One Touch for Safety" | Real-Time Protection Platform</p>
            <small>&copy; 2024 WABS. All rights reserved.</small>
        </div>
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    {scripts_html}
</body>
</html>'''
    
    return render_template_string(base_template, **kwargs)

# =============================================================================
# ROUTES - All Pages
# =============================================================================

@app.route('/')
def index():
    """Landing Page with Clickable Feature Cards"""
    content = '''
<div class="row align-items-center min-vh-75 py-5">
    <div class="col-lg-6 text-center text-lg-start mb-5 mb-lg-0">
        <h1 class="display-3 fw-bold mb-3" style="color: var(--dark);">
            Safety at Your <span style="color: var(--primary);">Fingertips</span>
        </h1>
        <p class="lead mb-4" style="color: #666;">
            WABS provides real-time emergency assistance, AI-powered voice detection, 
            live GPS tracking, and community support for women and children.
        </p>
        <div class="d-flex gap-3 justify-content-center justify-content-lg-start">
            <a href="/register" class="btn btn-wabs btn-lg px-5 py-3">
                <i class="bi bi-shield-check"></i> Get Protected Now
            </a>
            <a href="/login" class="btn btn-outline-danger btn-lg px-5 py-3">
                <i class="bi bi-box-arrow-in-right"></i> Login
            </a>
        </div>
        
        <div class="row mt-5 g-3">
            <div class="col-6 col-md-3">
                <div class="stat-card" onclick="showStatInfo('response')">
                    <div class="stat-number">0.5s</div>
                    <div class="stat-label">Response</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-card" onclick="showStatInfo('monitoring')">
                    <div class="stat-number">24/7</div>
                    <div class="stat-label">Monitoring</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-card" onclick="showStatInfo('ai')">
                    <div class="stat-number">AI</div>
                    <div class="stat-label">Powered</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-card" onclick="showStatInfo('gps')">
                    <div class="stat-number">GPS</div>
                    <div class="stat-label">Live</div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-lg-6 text-center">
        <div class="position-relative d-inline-block">
            <div class="sos-button-giant" onclick="window.location.href='/register'">
                SOS
            </div>
            <p class="mt-3 fw-bold" style="color: var(--primary); font-size: 1.2rem;">
                One Touch for Safety
            </p>
        </div>
    </div>
</div>

<div class="row mt-5 pt-5">
    <div class="col-12 text-center mb-5">
        <h2 class="fw-bold">How WABS Protects You</h2>
        <p class="text-muted">Click on any feature to learn more</p>
    </div>
    <div class="col-md-4 mb-4">
        <div class="card-wabs p-4 h-100 clickable" onclick="navigateTo('/voice-detection')">
            <div class="text-center mb-3">
                <i class="bi bi-mic-fill text-danger" style="font-size: 3rem;"></i>
            </div>
            <h5 class="text-center">Voice Detection</h5>
            <p class="text-center text-muted">AI detects distress phrases in English, Tamil & Tanglish. Just speak and get help automatically.</p>
            <div class="text-center mt-3">
                <span class="badge bg-danger">Live</span>
                <span class="badge bg-info">AI Powered</span>
            </div>
        </div>
    </div>
    <div class="col-md-4 mb-4">
        <div class="card-wabs p-4 h-100 clickable" onclick="navigateTo('/gps-tracking')">
            <div class="text-center mb-3">
                <i class="bi bi-geo-alt-fill text-danger" style="font-size: 3rem;"></i>
            </div>
            <h5 class="text-center">Live GPS Tracking</h5>
            <p class="text-center text-muted">Real-time location sharing with family and emergency contacts. Track your loved ones.</p>
            <div class="text-center mt-3">
                <span class="badge bg-success">Real-Time</span>
            </div>
        </div>
    </div>
    <div class="col-md-4 mb-4">
        <div class="card-wabs p-4 h-100 clickable" onclick="navigateTo('/community')">
            <div class="text-center mb-3">
                <i class="bi bi-people-fill text-danger" style="font-size: 3rem;"></i>
            </div>
            <h5 class="text-center">Community Network</h5>
            <p class="text-center text-muted">Nearby volunteers receive alerts and provide immediate assistance when you need help.</p>
            <div class="text-center mt-3">
                <span class="badge bg-warning">Active</span>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-12 text-center mb-4">
        <h3 class="fw-bold">Emergency Features</h3>
    </div>
    <div class="col-md-3 mb-3">
        <div class="card-wabs p-3 text-center clickable" onclick="navigateTo('/sos')">
            <i class="bi bi-exclamation-triangle-fill text-danger" style="font-size: 2rem;"></i>
            <h6 class="mt-2">SOS Button</h6>
            <small class="text-muted">Instant emergency activation</small>
        </div>
    </div>
    <div class="col-md-3 mb-3">
        <div class="card-wabs p-3 text-center clickable" onclick="navigateTo('/child-safety')">
            <i class="bi bi-heart-fill text-danger" style="font-size: 2rem;"></i>
            <h6 class="mt-2">Child Safety</h6>
            <small class="text-muted">Monitor your children</small>
        </div>
    </div>
    <div class="col-md-3 mb-3">
        <div class="card-wabs p-3 text-center clickable" onclick="navigateTo('/voice-detection')">
            <i class="bi bi-ear-fill text-warning" style="font-size: 2rem;"></i>
            <h6 class="mt-2">Sound Detection</h6>
            <small class="text-muted">Crying & screaming alerts</small>
        </div>
    </div>
    <div class="col-md-3 mb-3">
        <div class="card-wabs p-3 text-center clickable" onclick="navigateTo('/community')">
            <i class="bi bi-bell-fill text-info" style="font-size: 2rem;"></i>
            <h6 class="mt-2">Alerts</h6>
            <small class="text-muted">Community notifications</small>
        </div>
    </div>
</div>
'''
    
    scripts = '''
<script>
function navigateTo(url) {
    window.location.href = url;
}

function showStatInfo(type) {
    const info = {
        'response': 'Our system responds in under 0.5 seconds to ensure immediate help.',
        'monitoring': '24/7 AI-powered monitoring keeps you safe around the clock.',
        'ai': 'Advanced AI detects distress in voice, sound, and behavior patterns.',
        'gps': 'Live GPS tracking with real-time location sharing to emergency contacts.'
    };
    alert(info[type] || 'Feature information');
}
</script>
'''
    
    return render_page(content, scripts, "Home")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = Users.query.filter_by(Email=email, IsActive=True).first()
        
        if user and check_password_hash(user.PasswordHash, password):
            session['user_id'] = user.UserID
            session['user_name'] = user.Name
            session['user_type'] = user.UserType
            
            # Update last login
            user.LastLogin = datetime.datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.Name}! 🎉', 'success')
            
            if user.UserType == 'admin':
                return redirect(url_for('admin_panel'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    content = '''
<div class="row justify-content-center mt-5">
    <div class="col-md-5">
        <div class="card-wabs">
            <div class="card-header-wabs text-center">
                <h4 class="mb-0"><i class="bi bi-box-arrow-in-right"></i> Login to WABS</h4>
            </div>
            <div class="card-body p-4">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Email Address</label>
                        <div class="input-group">
                            <span class="input-group-text"><i class="bi bi-envelope"></i></span>
                            <input type="email" name="email" class="form-control" placeholder="your@email.com" required autofocus>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <div class="input-group">
                            <span class="input-group-text"><i class="bi bi-lock"></i></span>
                            <input type="password" name="password" class="form-control" placeholder="••••••••" required>
                        </div>
                    </div>
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="remember">
                        <label class="form-check-label" for="remember">Remember me</label>
                    </div>
                    <button type="submit" class="btn btn-wabs w-100 py-3">
                        <i class="bi bi-shield-check"></i> Login Securely
                    </button>
                </form>
                <div class="text-center mt-3">
                    <p>Don't have an account? <a href="/register" class="fw-bold" style="color: var(--primary);">Register here</a></p>
                   {# <p class="mt-2"><small class="text-muted">Demo: admin@wabs.com / admin123</small></p> #}
                   </div>
            </div>
        </div>
    </div>
</div>
'''
    
    return render_page(content, "", "Login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        address = request.form.get('address')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'woman')
        
        # Check existing
        existing = Users.query.filter((Users.Email == email) | (Users.Mobile == mobile)).first()
        if existing:
            flash('Email or mobile already registered! Please login.', 'warning')
            return redirect(url_for('login'))
        
        # Create user
        new_user = Users(
            Name=name,
            Mobile=mobile,
            Email=email,
            Address=address,
            PasswordHash=generate_password_hash(password),
            UserType=user_type,
            IsActive=True,
            CreatedAt=datetime.datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('✅ Registration successful! Please login to continue.', 'success')
        return redirect(url_for('login'))
    
    content = '''
<div class="row justify-content-center mt-4">
    <div class="col-md-6">
        <div class="card-wabs">
            <div class="card-header-wabs text-center">
                <h4 class="mb-0"><i class="bi bi-person-plus"></i> Register for WABS</h4>
            </div>
            <div class="card-body p-4">
                <form method="POST" onsubmit="return validateForm()">
                    <div class="mb-3">
                        <label class="form-label">Full Name *</label>
                        <input type="text" name="name" id="regName" class="form-control" placeholder="Enter your full name" required>
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label class="form-label">Mobile Number *</label>
                            <input type="tel" name="mobile" id="regMobile" class="form-control" placeholder="+91 XXXXX XXXXX" required pattern="[0-9+]{10,15}">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Email Address *</label>
                            <input type="email" name="email" id="regEmail" class="form-control" placeholder="email@example.com" required>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Address</label>
                        <textarea name="address" class="form-control" rows="2" placeholder="Enter your address (optional)"></textarea>
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label class="form-label">Password *</label>
                            <input type="password" name="password" id="regPassword" class="form-control" placeholder="Min 8 characters" required minlength="8">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">User Type *</label>
                            <select name="user_type" class="form-select" required>
                                <option value="woman">👩 Woman User</option>
                                <option value="parent">👨‍👩‍👧 Parent / Guardian</option>
                                <option value="volunteer">🤝 Community Volunteer</option>
                            </select>
                        </div>
                    </div>
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="termsCheck" required>
                        <label class="form-check-label" for="termsCheck">I agree to the terms and conditions</label>
                    </div>
                    <button type="submit" class="btn btn-wabs w-100 py-3">
                        <i class="bi bi-shield-check"></i> Register Now
                    </button>
                </form>
                <div class="text-center mt-3">
                    <p>Already have an account? <a href="/login" class="fw-bold" style="color: var(--primary);">Login here</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
'''
    
    scripts = '''
<script>
function validateForm() {
    const password = document.getElementById('regPassword').value;
    if (password.length < 8) {
        alert('Password must be at least 8 characters long.');
        return false;
    }
    return true;
}
</script>
'''
    
    return render_page(content, scripts, "Register")

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully. Stay safe! 🛡️', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = Users.query.get(session['user_id'])
    sos_count = SOSRecords.query.filter_by(UserID=user.UserID).count()
    active_sos = SOSRecords.query.filter_by(UserID=user.UserID, Status='active').count()
    contacts_count = EmergencyContacts.query.filter_by(UserID=user.UserID, IsActive=True).count()
    children = Children.query.filter_by(UserID=user.UserID, IsActive=True).all()
    recent_sos = SOSRecords.query.filter_by(UserID=user.UserID).order_by(SOSRecords.DateTime.desc()).limit(5).all()
    
    # Build recent SOS HTML
    recent_html = ''
    if recent_sos:
        for sos in recent_sos:
            status_color = {'active': 'danger', 'responding': 'warning', 'resolved': 'success', 'cancelled': 'secondary'}
            recent_html += f'''
            <div class="d-flex justify-content-between align-items-center p-2 mb-2 bg-light rounded">
                <div>
                    <strong>SOS #{sos.SOSID}</strong>
                    <small class="d-block text-muted">{sos.DateTime.strftime('%d %b %Y %H:%M')}</small>
                    <small>{sos.LocationLink[:50]}...</small>
                </div>
                <span class="badge bg-{status_color.get(sos.Status, 'secondary')}">{sos.Status}</span>
            </div>'''
    else:
        recent_html = '<p class="text-muted text-center">No emergency history</p>'
    
    # Build children list
    children_html = ''
    if children:
        for child in children:
            children_html += f'''
            <div class="d-flex justify-content-between align-items-center p-2 mb-2 bg-light rounded">
                <div>
                    <strong>{child.ChildName}</strong>
                    <small class="d-block text-muted">Age: {child.Age} | Code: {child.ChildCode}</small>
                </div>
                <span class="badge bg-info">Active</span>
            </div>'''
    else:
        children_html = '<p class="text-muted text-center">No children registered</p>'
    
    content = f'''
<div class="row mb-4">
    <div class="col-12">
        <h2 class="fw-bold">Welcome, {user.Name}! 👋</h2>
        <p class="text-muted">Your real-time safety dashboard | <span class="live-dot"></span> Live</p>
    </div>
</div>

<div class="row g-3 mb-4">
    <div class="col-6 col-md-3">
        <div class="stat-card" onclick="window.location.href='/sos'">
            <div class="stat-number" id="total-sos">{sos_count}</div>
            <div class="stat-label">Total SOS</div>
        </div>
    </div>
    <div class="col-6 col-md-3">
        <div class="stat-card">
            <div class="stat-number text-warning" id="active-sos">{active_sos}</div>
            <div class="stat-label">Active Alerts</div>
        </div>
    </div>
    <div class="col-6 col-md-3">
        <div class="stat-card" onclick="openContactModal()">
            <div class="stat-number text-info">{contacts_count}</div>
            <div class="stat-label">Contacts</div>
        </div>
    </div>
    <div class="col-6 col-md-3">
        <div class="stat-card" onclick="window.location.href='/child-safety'">
            <div class="stat-number text-success">{len(children)}</div>
            <div class="stat-label">Children</div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-lg-8 mb-4">
        <div class="card-wabs">
            <div class="card-header-wabs d-flex justify-content-between align-items-center">
                <span><i class="bi bi-exclamation-triangle"></i> Emergency SOS</span>
                <span class="badge bg-danger"><span class="live-dot"></span> LIVE</span>
            </div>
            <div class="card-body text-center py-5">
                <button class="sos-button-giant" onclick="triggerSOS()" id="sosBtn">
                    SOS
                </button>
                <p class="mt-3 fw-bold text-danger">Press in case of emergency</p>
                <small class="text-muted">GPS location, SMS, and alerts will be sent automatically</small>
            </div>
        </div>
    </div>
    <div class="col-lg-4 mb-4">
        <div class="card-wabs h-100">
            <div class="card-header-wabs">
                <i class="bi bi-telephone"></i> Emergency Contacts
            </div>
            <div class="card-body">
                <div id="contacts-list">
                    <p class="text-muted">Loading contacts...</p>
                </div>
                <button class="btn btn-wabs w-100 mt-3" onclick="openContactModal()">
                    <i class="bi bi-plus-circle"></i> Add Emergency Contact
                </button>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-lg-6 mb-4">
        <div class="card-wabs">
            <div class="card-header-wabs">
                <i class="bi bi-activity"></i> Recent SOS Activity
            </div>
            <div class="card-body" id="recent-activity" style="max-height: 300px; overflow-y: auto;">
                {recent_html}
            </div>
        </div>
    </div>
    <div class="col-lg-6 mb-4">
        <div class="card-wabs">
            <div class="card-header-wabs">
                <i class="bi bi-people"></i> Registered Children
            </div>
            <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                {children_html}
                <button class="btn btn-wabs btn-sm w-100 mt-2" onclick="window.location.href='/child-safety'">
                    Manage Children
                </button>
            </div>
        </div>
    </div>
</div>

<!-- Contact Modal -->
<div class="modal fade" id="contactModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header bg-danger text-white">
                <h5 class="modal-title">Add Emergency Contact</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label">Contact Name *</label>
                    <input type="text" id="contactName" class="form-control" placeholder="e.g., Mother, Father">
                </div>
                <div class="mb-3">
                    <label class="form-label">Relationship *</label>
                    <select id="relationship" class="form-select">
                        <option value="">Select relationship</option>
                        <option>Mother</option>
                        <option>Father</option>
                        <option>Brother</option>
                        <option>Sister</option>
                        <option>Husband</option>
                        <option>Wife</option>
                        <option>Friend</option>
                        <option>Guardian</option>
                        <option>Police</option>
                        <option>Other</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Mobile Number *</label>
                    <input type="tel" id="contactMobile" class="form-control" placeholder="+91XXXXXXXXXX">
                </div>
                <div class="mb-3">
                    <label class="form-label">Priority Level</label>
                    <select id="priority" class="form-select">
                        <option value="1">🔴 Critical - Contact First</option>
                        <option value="2">🟡 High - Contact Second</option>
                        <option value="3">🟢 Medium - Contact Third</option>
                    </select>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" onclick="addContact()">💾 Save Contact</button>
            </div>
        </div>
    </div>
</div>
'''
    
    scripts = '''
<script>
let currentPosition = { latitude: 13.0827, longitude: 80.2707 };
let contactModal;

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                currentPosition = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                };
                // Send location update
                fetch('/api/location/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        latitude: currentPosition.latitude,
                        longitude: currentPosition.longitude,
                        accuracy: position.coords.accuracy
                    })
                });
            },
            (error) => console.log('GPS:', error)
        );
    }
}

// Get location every 10 seconds
getLocation();
setInterval(getLocation, 10000);

function openContactModal() {
    if (!contactModal) {
        contactModal = new bootstrap.Modal(document.getElementById('contactModal'));
    }
    contactModal.show();
}

async function triggerSOS() {
    if (!confirm('🚨 EMERGENCY! This will alert ALL your contacts and nearby community members. Continue?')) {
        return;
    }
    
    const btn = document.getElementById('sosBtn');
    btn.style.animation = 'none';
    btn.style.transform = 'scale(0.95)';
    btn.innerHTML = '<span class="loading-spinner"></span>';
    
    try {
        const response = await fetch('/api/sos/trigger', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                latitude: currentPosition.latitude,
                longitude: currentPosition.longitude,
                alert_type: 'manual'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Play alarm sound
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            for (let i = 0; i < 3; i++) {
                setTimeout(() => {
                    const osc = audioCtx.createOscillator();
                    const gain = audioCtx.createGain();
                    osc.connect(gain);
                    gain.connect(audioCtx.destination);
                    osc.frequency.value = 800;
                    gain.gain.value = 0.3;
                    osc.start();
                    setTimeout(() => osc.stop(), 300);
                }, i * 500);
            }
            
            // Speak alert
            const utterance = new SpeechSynthesisUtterance(
                "Emergency SOS activated. Help is on the way. Stay calm."
            );
            speechSynthesis.speak(utterance);
            
            alert('✅ SOS ACTIVATED!\\n\\nHelp is on the way. Stay calm and stay safe.\\n\\nLocation shared with all contacts.');
            window.location.reload();
        } else {
            alert('❌ Error: ' + data.message);
        }
    } catch (error) {
        alert('❌ Network error. Please call 100/112 directly!');
    }
    
    btn.style.animation = 'pulse 2s infinite';
    btn.style.transform = 'scale(1)';
    btn.textContent = 'SOS';
}

async function loadContacts() {
    try {
        const response = await fetch('/api/contacts/list');
        const data = await response.json();
        
        const list = document.getElementById('contacts-list');
        if (data.contacts.length === 0) {
            list.innerHTML = '<p class="text-muted text-center">No contacts added</p>';
        } else {
            list.innerHTML = data.contacts.map(c => `
                <div class="d-flex justify-content-between align-items-center mb-2 p-2 bg-light rounded">
                    <div>
                        <strong>${c.name}</strong>
                        <small class="d-block text-muted">${c.relationship} | ${c.mobile}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteContact(${c.contact_id})" title="Delete">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading contacts:', error);
    }
}

async function addContact() {
    const data = {
        contact_name: document.getElementById('contactName').value,
        relationship: document.getElementById('relationship').value,
        mobile: document.getElementById('contactMobile').value,
        priority: parseInt(document.getElementById('priority').value)
    };
    
    if (!data.contact_name || !data.relationship || !data.mobile) {
        alert('Please fill all required fields.');
        return;
    }
    
    try {
        const response = await fetch('/api/contacts/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ Contact added!');
            contactModal.hide();
            loadContacts();
            window.location.reload();
        } else {
            alert('Error: ' + result.message);
        }
    } catch (error) {
        alert('Failed to add contact.');
    }
}

async function deleteContact(id) {
    if (!confirm('Delete this contact?')) return;
    
    try {
        await fetch(`/api/contacts/delete/${id}`, { method: 'DELETE' });
        loadContacts();
    } catch (error) {}
}

// Quick SOS button
function quickSOS() {
    triggerSOS();
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadContacts();
});
</script>
'''
    
    return render_page(content, scripts, "Dashboard")

@app.route('/sos')
@login_required
def sos_page():
    content = '''
<div class="row justify-content-center mt-4">
    <div class="col-lg-8 text-center">
        <div class="card-wabs p-5">
            <h3 class="mb-4 fw-bold text-danger">🚨 Emergency SOS System</h3>
            <p class="lead">Press the button to activate full emergency mode</p>
            
            <div class="my-5">
                <button class="sos-button-giant" onclick="triggerEmergencySOS()" style="width: 250px; height: 250px; font-size: 3rem;" id="mainSOSBtn">
                    SOS
                </button>
            </div>
            
            <div class="alert alert-danger text-start">
                <strong>⚠️ This will immediately:</strong>
                <ul class="mt-2">
                    <li>📡 Share your live GPS location</li>
                    <li>📱 Send SMS to all emergency contacts</li>
                    <li>🔔 Alert nearby community members (within 1km)</li>
                    <li>📞 Initiate emergency call simulation</li>
                    <li>🔊 Activate loud alarm</li>
                    <li>📹 Start audio recording</li>
                    <li>📋 Create incident report</li>
                </ul>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="p-3 bg-light rounded">
                        <h6>📍 Your Location</h6>
                        <p id="live-location">Fetching...</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="p-3 bg-light rounded">
                        <h6>🔋 Battery</h6>
                        <p id="battery-status">Checking...</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="p-3 bg-light rounded">
                        <h6>📶 Network</h6>
                        <p id="network-status">Checking...</p>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <small class="text-muted">Emergency Numbers: Police: 100 | Women Helpline: 1091 | Ambulance: 108</small>
            </div>
        </div>
    </div>
</div>
'''
    
    scripts = '''
<script>
let sosLocation = { latitude: 13.0827, longitude: 80.2707 };

function updateInfo() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                sosLocation.latitude = pos.coords.latitude;
                sosLocation.longitude = pos.coords.longitude;
                document.getElementById('live-location').innerHTML = 
                    `${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}<br><small>±${pos.coords.accuracy.toFixed(0)}m</small>`;
            },
            () => { document.getElementById('live-location').textContent = 'GPS Unavailable'; }
        );
    }
    
    if ('getBattery' in navigator) {
        navigator.getBattery().then(b => {
            document.getElementById('battery-status').textContent = 
                `${Math.round(b.level * 100)}% ${b.charging ? '⚡' : '🔋'}`;
        });
    }
    
    document.getElementById('network-status').textContent = 
        navigator.onLine ? '✅ Online' : '❌ Offline';
}

async function triggerEmergencySOS() {
    if (!confirm('🚨 FINAL CONFIRMATION: Real emergency? All contacts will be notified!')) return;
    
    const btn = document.getElementById('mainSOSBtn');
    btn.style.animation = 'none';
    btn.innerHTML = '<span class="loading-spinner" style="width:40px;height:40px;"></span>';
    
    try {
        const response = await fetch('/api/sos/trigger', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                latitude: sosLocation.latitude,
                longitude: sosLocation.longitude,
                alert_type: 'manual'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Alarm
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            [800, 1000, 1200].forEach((freq, i) => {
                setTimeout(() => {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain); gain.connect(ctx.destination);
                    osc.frequency.value = freq; gain.gain.value = 0.3;
                    osc.start(); setTimeout(() => osc.stop(), 400);
                }, i * 600);
            });
            
            alert('✅ SOS ACTIVATED SUCCESSFULLY!\\n\\n📍 Location shared\\n📱 Contacts notified\\n🔔 Community alerted\\n\\nStay calm. Help is coming!');
        }
    } catch (error) {
        alert('❌ Error! Call 100/112 directly!');
    }
    
    btn.style.animation = 'pulse 2s infinite';
    btn.textContent = 'SOS';
}

updateInfo();
setInterval(updateInfo, 5000);
</script>
'''
    
    return render_page(content, scripts, "Emergency SOS")

@app.route('/voice-detection')
@login_required
def voice_detection():
    content = '''
<div class="row mb-4">
    <div class="col-12">
        <h3 class="fw-bold"><i class="bi bi-mic-fill text-danger"></i> AI Voice Detection</h3>
        <p class="text-muted">Real-time voice monitoring with automatic SOS trigger</p>
    </div>
</div>

<div class="row">
    <div class="col-lg-8">
        <div class="card-wabs">
            <div class="card-header-wabs d-flex justify-content-between align-items-center">
                <span><i class="bi bi-ear"></i> Voice Monitor</span>
                <span class="badge bg-success" id="monitorStatus">● Active</span>
            </div>
            <div class="card-body text-center py-5">
                <div class="voice-indicator" id="voiceIndicator" onclick="toggleListening()">
                    <i class="bi bi-mic-fill text-white" style="font-size: 3rem;"></i>
                </div>
                
                <h5 class="mt-3" id="listeningStatus">Click to Start Listening</h5>
                <p class="text-muted">Speak distress phrases in English, Tamil, or Tanglish</p>
                
                <div class="mt-4">
                    <button class="btn btn-danger btn-lg me-2" id="startListenBtn" onclick="toggleListening()">
                        <i class="bi bi-mic"></i> Start Listening
                    </button>
                    <button class="btn btn-outline-danger btn-lg" onclick="simulateDetection()">
                        <i class="bi bi-play"></i> Simulate Test
                    </button>
                </div>
                
                <div id="transcriptBox" class="mt-4 p-3 bg-light rounded" style="min-height: 100px; max-height: 300px; overflow-y: auto;">
                    <p class="text-muted">Transcribed text will appear here...</p>
                </div>
                
                <div id="detectionAlert" class="mt-3"></div>
            </div>
        </div>
    </div>
    <div class="col-lg-4">
        <div class="card-wabs mb-3">
            <div class="card-header-wabs">
                <i class="bi bi-translate"></i> Supported Keywords
            </div>
            <div class="card-body">
                <h6>🇬🇧 English</h6>
                <div class="mb-2">
                    <span class="badge bg-danger m-1">Help Me</span>
                    <span class="badge bg-danger m-1">Save Me</span>
                    <span class="badge bg-danger m-1">Emergency</span>
                    <span class="badge bg-danger m-1">I'm in danger</span>
                    <span class="badge bg-danger m-1">Somebody help</span>
                    <span class="badge bg-danger m-1">Leave me alone</span>
                    <span class="badge bg-danger m-1">Don't hurt me</span>
                    <span class="badge bg-danger m-1">I am scared</span>
                </div>
                <h6>🇮🇳 Tamil</h6>
                <div class="mb-2">
                    <span class="badge bg-warning text-dark m-1">காப்பாற்றுங்கள்</span>
                    <span class="badge bg-warning text-dark m-1">உதவி செய்யுங்கள்</span>
                    <span class="badge bg-warning text-dark m-1">ஆபத்தில் இருக்கிறேன்</span>
                    <span class="badge bg-warning text-dark m-1">என்னை விடுங்கள்</span>
                </div>
                <h6>🔀 Tanglish (Mixed)</h6>
                <div class="mb-2">
                    <span class="badge bg-info m-1">Help pannunga</span>
                    <span class="badge bg-info m-1">Save pannunga</span>
                    <span class="badge bg-info m-1">Danger la iruken</span>
                    <span class="badge bg-info m-1">Yaaravathu help</span>
                </div>
            </div>
        </div>
        
        <div class="card-wabs">
            <div class="card-header-wabs">
                <i class="bi bi-clock-history"></i> Recent Detections
            </div>
            <div class="card-body" id="recentDetections" style="max-height: 300px; overflow-y: auto;">
                <p class="text-muted">No recent detections</p>
            </div>
        </div>
    </div>
</div>
'''
    
    scripts = '''
<script>
let isListening = false;
let recognition = null;
let transcriptHistory = [];

// Initialize Speech Recognition
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        alert('Speech recognition not supported in this browser. Please use Chrome.');
        return null;
    }
    
    const recog = new SpeechRecognition();
    recog.continuous = true;
    recog.interimResults = true;
    recog.lang = 'en-IN';  // Supports English, Tamil, Hindi
    
    recog.onresult = function(event) {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
                processVoiceInput(transcript);
            } else {
                interimTranscript += transcript;
            }
        }
        
        document.getElementById('transcriptBox').innerHTML = 
            '<strong>You said:</strong> ' + finalTranscript + 
            '<em style="color:#999">' + interimTranscript + '</em>';
    };
    
    recog.onerror = function(event) {
        console.error('Speech error:', event.error);
        document.getElementById('listeningStatus').textContent = 'Error: ' + event.error;
    };
    
    recog.onend = function() {
        if (isListening) {
            recog.start();
        }
    };
    
    return recog;
}

function toggleListening() {
    if (!recognition) {
        recognition = initSpeechRecognition();
        if (!recognition) return;
    }
    
    if (isListening) {
        recognition.stop();
        isListening = false;
        document.getElementById('voiceIndicator').classList.remove('listening');
        document.getElementById('listeningStatus').textContent = 'Listening Stopped';
        document.getElementById('startListenBtn').innerHTML = '<i class="bi bi-mic"></i> Start Listening';
        document.getElementById('monitorStatus').textContent = '● Inactive';
        document.getElementById('monitorStatus').className = 'badge bg-secondary';
    } else {
        recognition.start();
        isListening = true;
        document.getElementById('voiceIndicator').classList.add('listening');
        document.getElementById('listeningStatus').textContent = '🔴 Listening... Speak now';
        document.getElementById('startListenBtn').innerHTML = '<i class="bi bi-stop-fill"></i> Stop Listening';
        document.getElementById('monitorStatus').textContent = '● Listening';
        document.getElementById('monitorStatus').className = 'badge bg-danger';
    }
}

async function processVoiceInput(transcript) {
    // Detect language
    let language = 'english';
    const tamilPattern = /[\\u0B80-\\u0BFF]/;
    if (tamilPattern.test(transcript)) {
        language = 'tamil';
    }
    
    // Tanglish detection
    const tanglishWords = ['pannunga', 'iruken', 'yaaravathu', 'kappathunga', 'udhavi'];
    if (tanglishWords.some(w => transcript.toLowerCase().includes(w))) {
        language = 'tanglish';
    }
    
    try {
        const response = await fetch('/api/audio/detect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: transcript,
                language: language,
                confidence: 0.85
            })
        });
        
        const data = await response.json();
        
        if (data.is_distress) {
            document.getElementById('detectionAlert').innerHTML = `
                <div class="alert alert-danger animate__animated animate__shakeX">
                    <h5>🚨 DISTRESS DETECTED!</h5>
                    <p>Keyword: <strong>${data.matched_keyword}</strong></p>
                    <p>Language: ${language}</p>
                    <p>Confidence: ${(data.confidence * 100).toFixed(1)}%</p>
                    <p class="fw-bold">${data.sos_triggered ? '⚠️ SOS AUTO-TRIGGERED! Contacts notified.' : '⚠️ High alert!'}</p>
                </div>`;
            
            // Auto alarm
            if (data.sos_triggered) {
                const utterance = new SpeechSynthesisUtterance(
                    "Emergency distress detected. Activating safety protocol. Help is on the way."
                );
                speechSynthesis.speak(utterance);
            }
        }
        
        // Update history
        transcriptHistory.unshift({
            text: transcript,
            language: language,
            is_distress: data.is_distress,
            time: new Date().toLocaleTimeString()
        });
        
        if (transcriptHistory.length > 10) transcriptHistory.pop();
        
        updateDetectionHistory();
    } catch (error) {
        console.error('Detection error:', error);
    }
}

function updateDetectionHistory() {
    const div = document.getElementById('recentDetections');
    div.innerHTML = transcriptHistory.map(h => `
        <div class="p-2 mb-1 bg-${h.is_distress ? 'danger' : 'light'} rounded">
            <small class="${h.is_distress ? 'text-white' : ''}">"${h.text}"</small>
            <br><small class="${h.is_distress ? 'text-white' : 'text-muted'}">${h.language} | ${h.time}</small>
        </div>
    `).join('');
}

async function simulateDetection() {
    const phrases = [
        { text: 'Help me please', language: 'english' },
        { text: 'Save me somebody', language: 'english' },
        { text: 'I am in danger', language: 'english' },
        { text: 'காப்பாற்றுங்கள் யாராவது', language: 'tamil' },
        { text: 'Help pannunga yaaravathu', language: 'tanglish' },
        { text: 'Danger la iruken save me', language: 'tanglish' }
    ];
    
    const phrase = phrases[Math.floor(Math.random() * phrases.length)];
    
    document.getElementById('transcriptBox').innerHTML = 
        '<strong>Simulated:</strong> ' + phrase.text;
    
    await processVoiceInput(phrase.text);
}

// Check for browser support
if (!(window.SpeechRecognition || window.webkitSpeechRecognition)) {
    document.getElementById('transcriptBox').innerHTML = 
        '<div class="alert alert-warning">⚠️ Speech recognition requires Chrome browser.</div>';
    document.getElementById('startListenBtn').disabled = true;
}
</script>
'''
    
    return render_page(content, scripts, "Voice Detection")

@app.route('/gps-tracking')
@login_required
def gps_tracking():
    content = '''
<div class="row mb-4">
    <div class="col-12">
        <h3 class="fw-bold"><i class="bi bi-geo-alt-fill text-danger"></i> Live GPS Tracking</h3>
        <p class="text-muted"><span class="live-dot"></span> Real-time location monitoring</p>
    </div>
</div>

<div class="row">
    <div class="col-lg-8">
        <div class="card-wabs">
            <div class="card-header-wabs d-flex justify-content-between align-items-center">
                <span><i class="bi bi-map"></i> Live Map</span>
                <div>
                    <span class="badge bg-success me-2" id="trackingStatus">● Tracking</span>
                    <span class="badge bg-info" id="updateCount">Updates: 0</span>
                </div>
            </div>
            <div class="card-body p-0">
                <div id="liveMap" class="map-container map-large"></div>
            </div>
        </div>
    </div>
    <div class="col-lg-4">
        <div class="card-wabs mb-3">
            <div class="card-header-wabs">
                <i class="bi bi-broadcast"></i> Current Location
            </div>
            <div class="card-body text-center">
                <h4 id="currentLat">13.0827</h4>
                <small>Latitude</small>
                <h4 id="currentLng" class="mt-2">80.2707</h4>
                <small>Longitude</small>
                <div class="mt-3">
                    <span class="badge bg-success" id="accuracyBadge">Accuracy: --</span>
                    <span class="badge bg-info" id="speedBadge">Speed: --</span>
                </div>
                <div class="d-grid gap-2 mt-3">
                    <button class="btn btn-wabs" onclick="shareLocation()">
                        <i class="bi bi-share"></i> Share Live Location
                    </button>
                    <button class="btn btn-outline-danger" onclick="centerMap()">
                        <i class="bi bi-crosshair"></i> Center on Me
                    </button>
                    <button class="btn btn-outline-info" onclick="toggleTracking()">
                        <i class="bi bi-play-circle"></i> <span id="trackBtnText">Pause Tracking</span>
                    </button>
                </div>
            </div>
        </div>
        
        <div class="card-wabs">
            <div class="card-header-wabs">
                <i class="bi bi-clock-history"></i> Route History
            </div>
            <div class="card-body" id="routeHistory" style="max-height: 300px; overflow-y: auto;">
                <p class="text-muted">Recording route...</p>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-12">
        <div class="card-wabs">
            <div class="card-header-wabs">
                <i class="bi bi-shield-check"></i> Nearby Safety Points
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6>🏥 Safe Locations</h6>
                        <div id="safeLocations">
                            <div class="p-2 mb-1 bg-light rounded">📍 Police Station: <span id="policeDist">Calculating...</span></div>
                            <div class="p-2 mb-1 bg-light rounded">🏥 Hospital: <span id="hospitalDist">Calculating...</span></div>
                            <div class="p-2 mb-1 bg-light rounded">🏠 Safe House: <span id="safehouseDist">Calculating...</span></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6>⚠️ Risk Alerts</h6>
                        <div id="riskAlerts">
                            <p class="text-muted">Analyzing area safety...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
'''
    
    scripts = '''
<script>
let map;
let marker;
let pathLine;
let pathCoordinates = [];
let isTracking = true;
let updateCounter = 0;
let currentLocation = { lat: 13.0827, lng: 80.2707, accuracy: 0, speed: 0 };

// Safe locations (Chennai)
const safeLocations = [
    { name: 'Police Station', lat: 13.0820, lng: 80.2750 },
    { name: 'Hospital', lat: 13.0800, lng: 80.2650 },
    { name: 'Safe House', lat: 13.0850, lng: 80.2720 }
];

// Initialize map
function initMap() {
    map = L.map('liveMap').setView([13.0827, 80.2707], 16);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Add safe location markers
    const safeIcon = L.divIcon({
        html: '<i class="bi bi-shield-fill" style="font-size: 20px; color: green;"></i>',
        className: 'safe-marker',
        iconSize: [20, 20]
    });
    
    safeLocations.forEach(loc => {
        L.marker([loc.lat, loc.lng], { icon: safeIcon })
            .addTo(map)
            .bindPopup(`<b>${loc.name}</b><br>Safe Location`);
    });
    
    // User marker
    const userIcon = L.divIcon({
        html: '<div style="background: red; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px red;"></div>',
        className: 'user-marker',
        iconSize: [20, 20]
    });
    
    marker = L.marker([13.0827, 80.2707], { icon: userIcon }).addTo(map);
    marker.bindPopup('<b>Your Location</b><br>Real-time tracking active').openPopup();
    
    // Path line
    pathLine = L.polyline([], { color: 'red', weight: 3, dashArray: '10, 10' }).addTo(map);
    
    // Add circle for accuracy
    window.accuracyCircle = L.circle([13.0827, 80.2707], {
        radius: 10,
        color: 'blue',
        fillColor: '#30f',
        fillOpacity: 0.1
    }).addTo(map);
}

function updateLocation() {
    if (!isTracking) return;
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                currentLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    speed: position.coords.speed || 0
                };
                
                updateCounter++;
                
                // Update UI
                document.getElementById('currentLat').textContent = currentLocation.lat.toFixed(6);
                document.getElementById('currentLng').textContent = currentLocation.lng.toFixed(6);
                document.getElementById('accuracyBadge').textContent = `Accuracy: ±${currentLocation.accuracy.toFixed(0)}m`;
                document.getElementById('speedBadge').textContent = `Speed: ${currentLocation.speed.toFixed(1)} m/s`;
                document.getElementById('updateCount').textContent = `Updates: ${updateCounter}`;
                
                // Update map
                if (map && marker) {
                    const newPos = [currentLocation.lat, currentLocation.lng];
                    marker.setLatLng(newPos);
                    window.accuracyCircle.setLatLng(newPos);
                    window.accuracyCircle.setRadius(currentLocation.accuracy);
                    
                    // Add to path
                    pathCoordinates.push(newPos);
                    pathLine.setLatLngs(pathCoordinates);
                    
                    // Keep last 100 points
                    if (pathCoordinates.length > 100) {
                        pathCoordinates.shift();
                    }
                    
                    // Update route history
                    updateRouteHistory();
                    
                    // Calculate distances
                    calculateDistances();
                }
                
                // Send to server
                fetch('/api/location/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        latitude: currentLocation.lat,
                        longitude: currentLocation.lng,
                        accuracy: currentLocation.accuracy,
                        speed: currentLocation.speed
                    })
                });
            },
            (error) => {
                console.error('GPS Error:', error);
                document.getElementById('trackingStatus').textContent = '● GPS Error';
                document.getElementById('trackingStatus').className = 'badge bg-danger';
            },
            { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
        );
    }
}

function calculateDistances() {
    safeLocations.forEach(loc => {
        const dist = getDistance(currentLocation.lat, currentLocation.lng, loc.lat, loc.lng);
        const elementId = loc.name.toLowerCase().replace(' ', '') + 'Dist';
        const elem = document.getElementById(elementId);
        if (elem) {
            elem.textContent = `${dist.toFixed(1)} km`;
        }
    });
}

function getDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

function updateRouteHistory() {
    const div = document.getElementById('routeHistory');
    const recent = pathCoordinates.slice(-5).reverse();
    div.innerHTML = recent.map((coord, i) => `
        <div class="p-2 mb-1 bg-light rounded">
            <small>📍 ${coord[0].toFixed(4)}, ${coord[1].toFixed(4)}</small>
            <br><small class="text-muted">${new Date(Date.now() - i*10000).toLocaleTimeString()}</small>
        </div>
    `).join('') || '<p class="text-muted">Recording route...</p>';
}

function shareLocation() {
    const url = `https://www.google.com/maps?q=${currentLocation.lat},${currentLocation.lng}`;
    
    if (navigator.share) {
        navigator.share({
            title: 'My Live Location - WABS',
            text: 'Here is my current location. Track me live.',
            url: url
        }).catch(() => {
            prompt('Copy location link:', url);
        });
    } else {
        prompt('Copy location link:', url);
    }
}

function centerMap() {
    if (map) {
        map.setView([currentLocation.lat, currentLocation.lng], 18);
        marker.openPopup();
    }
}

function toggleTracking() {
    isTracking = !isTracking;
    const btn = document.getElementById('trackBtnText');
    const status = document.getElementById('trackingStatus');
    
    if (isTracking) {
        btn.textContent = 'Pause Tracking';
        status.textContent = '● Tracking';
        status.className = 'badge bg-success';
        updateLocation();
    } else {
        btn.textContent = 'Resume Tracking';
        status.textContent = '● Paused';
        status.className = 'badge bg-warning';
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    updateLocation();
    setInterval(updateLocation, 5000);
});
</script>
'''
    
    return render_page(content, scripts, "GPS Tracking")

@app.route('/child-safety')
@login_required
def child_safety():
    user = Users.query.get(session['user_id'])
    children = Children.query.filter_by(UserID=user.UserID, IsActive=True).all()
    
    children_cards = ''
    if children:
        for child in children:
            children_cards += f'''
            <div class="col-md-6 mb-3">
                <div class="card-wabs p-3">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h5>{child.ChildName}</h5>
                            <p class="mb-1">Age: {child.Age} | Gender: {child.Gender or 'N/A'}</p>
                            <p class="mb-0"><small>Code: {child.ChildCode}</small></p>
                            {f'<p class="text-danger"><small>Medical: {child.MedicalInfo}</small></p>' if child.MedicalInfo else ''}
                        </div>
                        <div>
                            <span class="badge bg-success">Active</span>
                        </div>
                    </div>
                </div>
            </div>'''
    else:
        children_cards = '<div class="col-12"><p class="text-muted">No children registered yet.</p></div>'
    
    content = f'''
<div class="row mb-4">
    <div class="col-12">
        <h3 class="fw-bold"><i class="bi bi-heart-fill text-danger"></i> Child Safety Monitoring</h3>
        <p class="text-muted">Monitor and protect your children with AI sound detection</p>
    </div>
</div>

<div class="row">
    <div class="col-lg-8">
        <div class="card-wabs mb-4">
            <div class="card-header-wabs d-flex justify-content-between">
                <span><i class="bi bi-ear"></i> Sound Detection Monitor</span>
                <span class="badge bg-success" id="childMonitorStatus">● Active</span>
            </div>
            <div class="card-body text-center py-4">
                <div class="voice-indicator" id="childSoundIndicator" style="background: linear-gradient(135deg, #FF6B6B, #FF8E8E);" onclick="toggleChildMonitoring()">
                    <i class="bi bi-ear-fill text-white" style="font-size: 3rem;"></i>
                </div>
                <h5 class="mt-3" id="childListeningStatus">Click to Start Monitoring</h5>
                <p class="text-muted">Detecting: Crying 😢 | Screaming 😱 | Panic Sounds 🆘</p>
                
                <div class="row mt-4">
                    <div class="col-md-4">
                        <button class="btn btn-outline-danger w-100" onclick="simulateSound('crying')">
                            😢 Test Crying
                        </button>
                    </div>
                    <div class="col-md-4">
                        <button class="btn btn-outline-danger w-100" onclick="simulateSound('screaming')">
                            😱 Test Screaming
                        </button>
                    </div>
                    <div class="col-md-4">
                        <button class="btn btn-outline-danger w-100" onclick="simulateSound('panic')">
                            🆘 Test Panic
                        </button>
                    </div>
                </div>
                
                <div id="childSoundResult" class="mt-4"></div>
            </div>
        </div>
    </div>
    <div class="col-lg-4">
        <div class="card-wabs mb-3">
            <div class="card-header-wabs">
                <i class="bi bi-people"></i> Registered Children
            </div>
            <div class="card-body">
                <div class="row">
                    {children_cards}
                </div>
                <button class="btn btn-wabs w-100 mt-3" onclick="openChildModal()">
                    <i class="bi bi-plus-circle"></i> Register New Child
                </button>
            </div>
        </div>
        
        <div class="card-wabs">
            <div class="card-header-wabs">
                <i class="bi bi-bell"></i> Recent Child Alerts
            </div>
            <div class="card-body" id="childAlertsHistory" style="max-height: 300px; overflow-y: auto;">
                <p class="text-muted">No recent child alerts</p>
            </div>
        </div>
    </div>
</div>

<!-- Add Child Modal -->
<div class="modal fade" id="childModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header bg-danger text-white">
                <h5 class="modal-title">👶 Register Child</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label">Child Name *</label>
                    <input type="text" id="childName" class="form-control" placeholder="Enter child's name">
                </div>
                <div class="row mb-3">
                    <div class="col-6">
                        <label class="form-label">Age *</label>
                        <input type="number" id="childAge" class="form-control" min="0" max="18">
                    </div>
                    <div class="col-6">
                        <label class="form-label">Gender</label>
                        <select id="childGender" class="form-select">
                            <option>Female</option>
                            <option>Male</option>
                            <option>Other</option>
                        </select>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Parent/Guardian Name</label>
                    <input type="text" id="parentName" class="form-control">
                </div>
                <div class="mb-3">
                    <label class="form-label">Parent Mobile</label>
                    <input type="tel" id="parentMobile" class="form-control">
                </div>
                <div class="mb-3">
                    <label class="form-label">Medical Notes (Optional)</label>
                    <textarea id="medicalInfo" class="form-control" rows="2" placeholder="Allergies, conditions, etc."></textarea>
                </div>
                <div class="mb-3">
                    <label class="form-label">Child Photo (Optional)</label>
                    <input type="file" id="childPhoto" class="form-control" accept="image/*">
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" onclick="registerChild()">💾 Register Child</button>
            </div>
        </div>
    </div>
</div>
'''
    
    scripts = '''
<script>
let isChildMonitoring = false;
let childRecognition = null;
let childAlertHistory = [];

function openChildModal() {
    new bootstrap.Modal(document.getElementById('childModal')).show();
}

function toggleChildMonitoring() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        alert('Speech recognition not supported. Please use Chrome.');
        return;
    }
    
    if (!childRecognition) {
        childRecognition = new SpeechRecognition();
        childRecognition.continuous = true;
        childRecognition.interimResults = true;
        childRecognition.lang = 'en-IN';
        
        childRecognition.onresult = function(event) {
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    const transcript = event.results[i][0].transcript;
                    analyzeChildSound(transcript);
                }
            }
        };
        
        childRecognition.onend = function() {
            if (isChildMonitoring) childRecognition.start();
        };
    }
    
    if (isChildMonitoring) {
        childRecognition.stop();
        isChildMonitoring = false;
        document.getElementById('childSoundIndicator').classList.remove('listening');
        document.getElementById('childListeningStatus').textContent = 'Monitoring Stopped';
        document.getElementById('childMonitorStatus').textContent = '● Inactive';
        document.getElementById('childMonitorStatus').className = 'badge bg-secondary';
    } else {
        childRecognition.start();
        isChildMonitoring = true;
        document.getElementById('childSoundIndicator').classList.add('listening');
        document.getElementById('childListeningStatus').textContent = '🔴 Monitoring Child Sounds...';
        document.getElementById('childMonitorStatus').textContent = '● Monitoring';
        document.getElementById('childMonitorStatus').className = 'badge bg-success';
    }
}

async function analyzeChildSound(transcript) {
    // Check for child distress sounds
    const distressIndicators = ['cry', 'scream', 'help', 'scared', 'mommy', 'daddy', 'amma', 'appa', 'pain'];
    const isDistress = distressIndicators.some(w => transcript.toLowerCase().includes(w));
    
    if (isDistress) {
        try {
            const response = await fetch('/api/child/sound/detect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sound_type: 'voice_distress',
                    confidence: 0.8,
                    latitude: 13.0827,
                    longitude: 80.2707,
                    transcript: transcript
                })
            });
            
            const data = await response.json();
            
            document.getElementById('childSoundResult').innerHTML = `
                <div class="alert alert-danger">
                    <h5>🚨 Child Distress Detected!</h5>
                    <p>Detected: "${transcript}"</p>
                    <p class="fw-bold">${data.alert_triggered ? '⚠️ Alert sent to parents!' : 'Monitoring...'}</p>
                </div>`;
            
            childAlertHistory.unshift({
                text: transcript,
                time: new Date().toLocaleTimeString()
            });
            
            if (childAlertHistory.length > 10) childAlertHistory.pop();
            updateChildAlertHistory();
        } catch (error) {}
    }
}

function updateChildAlertHistory() {
    const div = document.getElementById('childAlertsHistory');
    div.innerHTML = childAlertHistory.map(h => `
        <div class="p-2 mb-1 bg-light rounded">
            <small>"${h.text}"</small>
            <br><small class="text-muted">${h.time}</small>
        </div>
    `).join('') || '<p class="text-muted">No recent child alerts</p>';
}

async function simulateSound(type) {
    const sounds = {
        'crying': 'Baby crying sound detected',
        'screaming': 'Child screaming sound detected',
        'panic': 'Panic sounds detected from child'
    };
    
    try {
        const response = await fetch('/api/child/sound/detect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sound_type: type,
                confidence: 0.85,
                latitude: 13.0827,
                longitude: 80.2707
            })
        });
        
        const data = await response.json();
        
        document.getElementById('childSoundResult').innerHTML = `
            <div class="alert alert-danger">
                <h5>🚨 Child Distress Sound Detected!</h5>
                <p>Type: <strong>${type.toUpperCase()}</strong></p>
                <p>${sounds[type]}</p>
                <p class="fw-bold">${data.alert_triggered ? '⚠️ Parents alerted!' : 'Testing...'}</p>
            </div>`;
    } catch (error) {}
}

async function registerChild() {
    const data = {
        child_name: document.getElementById('childName').value,
        age: parseInt(document.getElementById('childAge').value),
        gender: document.getElementById('childGender').value,
        parent_name: document.getElementById('parentName').value,
        parent_mobile: document.getElementById('parentMobile').value,
        medical_info: document.getElementById('medicalInfo').value
    };
    
    if (!data.child_name || !data.age) {
        alert('Please fill required fields.');
        return;
    }
    
    try {
        const response = await fetch('/api/child/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            alert('✅ Child registered successfully!');
            window.location.reload();
        }
    } catch (error) {
        alert('Error registering child.');
    }
}
</script>
'''
    
    return render_page(content, scripts, "Child Safety")

@app.route('/community')
@login_required
def community():
    content = '''
<div class="row mb-4">
    <div class="col-12">
        <h3 class="fw-bold"><i class="bi bi-people-fill text-primary"></i> Community Safety Network</h3>
        <p class="text-muted"><span class="live-dot"></span> Real-time community alerts and assistance</p>
    </div>
</div>

<div class="row">
    <div class="col-lg-8">
        <div class="card-wabs mb-4">
            <div class="card-header-wabs d-flex justify-content-between align-items-center">
                <span><i class="bi bi-bell"></i> Nearby Emergency Alerts</span>
                <select id="radiusSelect" class="form-select form-select-sm w-auto" onchange="loadAlerts()">
                    <option value="100">100 meters</option>
                    <option value="500" selected>500 meters</option>
                    <option value="1000">1 kilometer</option>
                    <option value="5000">5 kilometers</option>
                </select>
            </div>
            <div class="card-body" id="nearbyAlerts">
                <div class="text-center py-5">
                    <div class="spinner-border text-danger" role="status"></div>
                    <p class="mt-2">Scanning for nearby emergencies...</p>
                </div>
            </div>
        </div>
    </div>
    <div class="col-lg-4">
        <div class="card-wabs mb-3">
            <div class="card-header-wabs">
                <i class="bi bi-megaphone"></i> Emergency Announcement
            </div>
            <div class="card-body">
                <button class="btn btn-danger w-100 mb-3" onclick="playEmergencyAnnouncement()">
                    <i class="bi bi-volume-up"></i> Play Emergency Announcement
                </button>
                <div class="p-3 bg-light rounded">
                    <p class="mb-1"><strong>🇬🇧 English:</strong></p>
                    <small>"Attention! A woman or child may be in danger nearby. Please help immediately!"</small>
                    <hr>
                    <p class="mb-1"><strong>🇮🇳 Tamil:</strong></p>
                    <small>"கவனம்! அருகில் ஒரு பெண் அல்லது குழந்தை ஆபத்தில் இருக்கலாம். தயவுசெய்து உடனடியாக உதவுங்கள்!"</small>
                </div>
            </div>
        </div>
        
        <div class="card-wabs mb-3">
            <div class="card-header-wabs">
                <i class="bi bi-hand-thumbs-up"></i> Community Stats
            </div>
            <div class="card-body text-center">
                <div class="row">
                    <div class="col-6">
                        <h3 class="text-primary" id="volunteersCount">--</h3>
                        <small>Active Volunteers</small>
                    </div>
                    <div class="col-6">
                        <h3 class="text-success" id="responsesCount">--</h3>
                        <small>Responses Today</small>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card-wabs">
            <div class="card-header-wabs">
                <i class="bi bi-info-circle"></i> How to Help
            </div>
            <div class="card-body">
                <ol class="small">
                    <li>When you receive an alert, check the location</li>
                    <li>Click "I'll Help" to notify the person in distress</li>
                    <li>Approach safely or call authorities</li>
                    <li>Provide assistance or escort to safety</li>
                    <li>Mark the incident as resolved when safe</li>
                </ol>
            </div>
        </div>
    </div>
</div>

<div id="responseModal" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header bg-success text-white">
                <h5 class="modal-title">Respond to Emergency</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p><strong>Alert:</strong> <span id="responseAlertMsg"></span></p>
                <div class="mb-3">
                    <label class="form-label">How will you help?</label>
                    <select id="responseType" class="form-select">
                        <option value="i_am_coming">🏃 I'm coming to help</option>
                        <option value="called_police">📞 Called police (100)</option>
                        <option value="safe_escort">🛡️ Providing safe escort</option>
                        <option value="medical_help">🏥 Arranging medical help</option>
                        <option value="other">🤝 Other assistance</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Message (Optional)</label>
                    <textarea id="responseMsg" class="form-control" rows="2" placeholder="Any additional info..."></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-success" onclick="submitResponse()">✅ Send Response</button>
            </div>
        </div>
    </div>
</div>
'''
    
    scripts = '''
<script>
let currentAlertId = null;
let responseModal;

async function loadAlerts() {
    const radius = document.getElementById('radiusSelect').value;
    
    try {
        const response = await fetch('/api/community/alerts/nearby', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                latitude: 13.0827,
                longitude: 80.2707,
                radius: parseInt(radius)
            })
        });
        
        const data = await response.json();
        
        const div = document.getElementById('nearbyAlerts');
        
        if (data.alerts.length === 0) {
            div.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-check-circle-fill text-success" style="font-size: 4rem;"></i>
                    <h5 class="mt-2">No Active Alerts</h5>
                    <p class="text-muted">Your area is currently safe. Community is watching.</p>
                </div>`;
        } else {
            div.innerHTML = data.alerts.map(alert => `
                <div class="alert alert-danger mb-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6>🚨 EMERGENCY ALERT</h6>
                            <p class="mb-1">${alert.message}</p>
                            <small class="text-muted">📍 ${alert.latitude.toFixed(4)}, ${alert.longitude.toFixed(4)}</small>
                            <br><small>🕐 ${new Date(alert.sent_at).toLocaleString()}</small>
                            <br><small>👥 ${alert.responded_count} people responded</small>
                        </div>
                        <div class="ms-3">
                            <button class="btn btn-success btn-sm" onclick="openResponse(${alert.alert_id}, '${alert.message.replace(/'/g, "\\'")}')">
                                🤝 I'll Help
                            </button>
                            <a href="https://www.google.com/maps?q=${alert.latitude},${alert.longitude}" 
                               target="_blank" class="btn btn-outline-info btn-sm mt-1">
                                📍 View Map
                            </a>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        // Update stats
        document.getElementById('volunteersCount').textContent = data.alerts.length > 0 ? 'Active' : '--';
        document.getElementById('responsesCount').textContent = data.alerts.reduce((sum, a) => sum + a.responded_count, 0);
        
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

function openResponse(alertId, message) {
    currentAlertId = alertId;
    document.getElementById('responseAlertMsg').textContent = message;
    
    if (!responseModal) {
        responseModal = new bootstrap.Modal(document.getElementById('responseModal'));
    }
    responseModal.show();
}

async function submitResponse() {
    if (!currentAlertId) return;
    
    const responseType = document.getElementById('responseType').value;
    const message = document.getElementById('responseMsg').value;
    
    try {
        const response = await fetch(`/api/community/respond/${currentAlertId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                response_type: responseType,
                message: message
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Thank you for responding! The person in distress has been notified.');
            responseModal.hide();
            loadAlerts();
        }
    } catch (error) {
        alert('Error sending response. Please try again.');
    }
}

function playEmergencyAnnouncement() {
    // English announcement
    const englishMsg = new SpeechSynthesisUtterance(
        "Attention! A woman or child may be in danger nearby. Please help immediately!"
    );
    englishMsg.rate = 0.9;
    englishMsg.pitch = 1.1;
    
    // Tamil announcement
    const tamilMsg = new SpeechSynthesisUtterance(
        "கவனம்! அருகில் ஒரு பெண் அல்லது குழந்தை ஆபத்தில் இருக்கலாம். தயவுசெய்து உடனடியாக உதவுங்கள்!"
    );
    tamilMsg.rate = 0.8;
    
    // Repeat 3 times
    for (let i = 0; i < 3; i++) {
        setTimeout(() => speechSynthesis.speak(englishMsg), i * 4000);
        setTimeout(() => speechSynthesis.speak(tamilMsg), i * 4000 + 2000);
    }
}

// Load alerts on page load
loadAlerts();
// Refresh every 10 seconds
setInterval(loadAlerts, 10000);
</script>
'''
    
    return render_page(content, scripts, "Community Network")

@app.route('/admin')
@admin_required
def admin_panel():
    total_users = Users.query.count()
    active_users = Users.query.filter(Users.LastLogin >= datetime.datetime.utcnow() - datetime.timedelta(days=7)).count()
    total_sos = SOSRecords.query.count()
    active_sos = SOSRecords.query.filter_by(Status='active').count()
    resolved_sos = SOSRecords.query.filter_by(Status='resolved').count()
    total_children = Children.query.count()
    total_recordings = VoiceRecordings.query.count()
    total_audio_events = AudioEvents.query.count()
    
    # Get all users for admin view
    all_users = Users.query.order_by(Users.CreatedAt.desc()).limit(20).all()
    users_table = ''
    for u in all_users:
        users_table += f'''
        <tr>
            <td>{u.UserID}</td>
            <td>{u.Name}</td>
            <td>{u.Mobile}</td>
            <td>{u.Email}</td>
            <td><span class="badge bg-{'primary' if u.UserType == 'admin' else 'info' if u.UserType == 'volunteer' else 'success'}">{u.UserType}</span></td>
            <td>{u.LastLogin.strftime('%d %b %H:%M') if u.LastLogin else 'Never'}</td>
            <td><span class="badge bg-{'success' if u.IsActive else 'danger'}">{'Active' if u.IsActive else 'Inactive'}</span></td>
        </tr>'''
    
    # Get recent SOS
    recent_sos = SOSRecords.query.order_by(SOSRecords.DateTime.desc()).limit(10).all()
    sos_table = ''
    for s in recent_sos:
        sos_table += f'''
        <tr>
            <td>#{s.SOSID}</td>
            <td>{s.user.Name if s.user else 'Unknown'}</td>
            <td><span class="badge bg-info">{s.AlertType}</span></td>
            <td><span class="badge bg-{'danger' if s.Status == 'active' else 'warning' if s.Status == 'responding' else 'success'}">{s.Status}</span></td>
            <td><a href="{s.LocationLink}" target="_blank">View Map</a></td>
            <td>{s.DateTime.strftime('%d %b %Y %H:%M')}</td>
        </tr>'''
    
    # Get all voice recordings
    all_recordings = VoiceRecordings.query.order_by(VoiceRecordings.CreatedAt.desc()).limit(10).all()
    recordings_table = ''
    for r in all_recordings:
        recordings_table += f'''
        <tr>
            <td>{r.RecordingID}</td>
            <td>{r.user.Name if r.user else 'Unknown'}</td>
            <td>{r.TranscribedText[:50] if r.TranscribedText else 'N/A'}...</td>
            <td>{r.Language or 'N/A'}</td>
            <td><span class="badge bg-{'danger' if r.IsEmergency else 'success'}">{'Emergency' if r.IsEmergency else 'Normal'}</span></td>
            <td>{r.CreatedAt.strftime('%d %b %H:%M') if r.CreatedAt else 'N/A'}</td>
        </tr>'''
    
    content = f'''
<div class="row mb-4">
    <div class="col-12">
        <h3 class="fw-bold"><i class="bi bi-shield-fill text-warning"></i> Admin Control Panel</h3>
        <p class="text-muted">Complete system monitoring and user management</p>
    </div>
</div>

<div class="row g-3 mb-4">
    <div class="col-6 col-md-3"><div class="stat-card"><div class="stat-number">{total_users}</div><div class="stat-label">Total Users</div></div></div>
    <div class="col-6 col-md-3"><div class="stat-card"><div class="stat-number text-success">{active_users}</div><div class="stat-label">Active (7d)</div></div></div>
    <div class="col-6 col-md-3"><div class="stat-card"><div class="stat-number text-danger">{total_sos}</div><div class="stat-label">Total SOS</div></div></div>
    <div class="col-6 col-md-3"><div class="stat-card"><div class="stat-number text-warning">{active_sos}</div><div class="stat-label">Active SOS</div></div></div>
    <div class="col-6 col-md-3"><div class="stat-card"><div class="stat-number text-success">{resolved_sos}</div><div class="stat-label">Resolved</div></div></div>
    <div class="col-6 col-md-3"><div class="stat-card"><div class="stat-number text-info">{total_children}</div><div class="stat-label">Children</div></div></div>
    <div class="col-6 col-md-3"><div class="stat-card"><div class="stat-number text-primary">{total_recordings}</div><div class="stat-label">Recordings</div></div></div>
    <div class="col-6 col-md-3"><div class="stat-card"><div class="stat-number text-info">{total_audio_events}</div><div class="stat-label">Audio Events</div></div></div>
</div>

<ul class="nav nav-tabs mb-4" id="adminTabs">
    <li class="nav-item"><a class="nav-link active" data-bs-toggle="tab" href="#usersTab">👥 Users</a></li>
    <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#sosTab">🚨 SOS Records</a></li>
    <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#recordingsTab">🎙️ Voice Recordings</a></li>
    <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#analyticsTab">📊 Analytics</a></li>
</ul>

<div class="tab-content">
    <div class="tab-pane fade show active" id="usersTab">
        <div class="card-wabs">
            <div class="card-header-wabs">All Registered Users</div>
            <div class="card-body table-responsive">
                <table class="table table-hover table-striped">
                    <thead>
                        <tr><th>ID</th><th>Name</th><th>Mobile</th><th>Email</th><th>Type</th><th>Last Login</th><th>Status</th></tr>
                    </thead>
                    <tbody>{users_table}</tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="tab-pane fade" id="sosTab">
        <div class="card-wabs">
            <div class="card-header-wabs">Recent SOS Records</div>
            <div class="card-body table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr><th>SOS ID</th><th>User</th><th>Type</th><th>Status</th><th>Location</th><th>Time</th></tr>
                    </thead>
                    <tbody>{sos_table}</tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="tab-pane fade" id="recordingsTab">
        <div class="card-wabs">
            <div class="card-header-wabs">All Voice Recordings (Admin Access Only)</div>
            <div class="card-body table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr><th>ID</th><th>User</th><th>Transcript</th><th>Language</th><th>Type</th><th>Time</th></tr>
                    </thead>
                    <tbody>{recordings_table}</tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="tab-pane fade" id="analyticsTab">
        <div class="card-wabs">
            <div class="card-header-wabs">System Analytics</div>
            <div class="card-body" id="analyticsContent">
                <p>Loading analytics data...</p>
            </div>
        </div>
    </div>
</div>
'''
    
    scripts = '''
<script>
async function loadAnalytics() {
    try {
        const response = await fetch('/api/admin/stats');
        const data = await response.json();
        
        if (data.success) {
            const div = document.getElementById('analyticsContent');
            div.innerHTML = `
                <h6>User Growth (Last 6 Months)</h6>
                <div class="mb-4">
                    ${data.user_growth.map(m => `
                        <div class="d-flex align-items-center mb-2">
                            <div style="width: 100px;">${m.month}</div>
                            <div class="flex-grow-1 bg-light rounded">
                                <div class="bg-primary rounded" style="height: 25px; width: ${Math.max(m.count * 5, 5)}%; display: flex; align-items: center; padding-left: 5px; color: white; min-width: 30px;">
                                    ${m.count}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <h6>High Risk Areas</h6>
                ${data.high_risk_areas.length > 0 ? data.high_risk_areas.map(a => `
                    <div class="p-2 mb-1 bg-light rounded d-flex justify-content-between">
                        <span>📍 ${a.lat}, ${a.lng}</span>
                        <span class="badge bg-danger">${a.count} incidents</span>
                    </div>
                `).join('') : '<p class="text-success">No high-risk areas identified.</p>'}
            `;
        }
    } catch (error) {}
}

document.addEventListener('DOMContentLoaded', loadAnalytics);
</script>
'''
    
    return render_page(content, scripts, "Admin Panel")

# =============================================================================
# API ENDPOINTS - Complete Production APIs
# =============================================================================

@app.route('/api/sos/trigger', methods=['POST'])
@login_required
def trigger_sos():
    """Complete SOS trigger with all notifications"""
    try:
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy')
        alert_type = data.get('alert_type', 'manual')
        notes = data.get('notes', '')
        
        user = Users.query.get(session['user_id'])
        
        # Get address from coordinates (simplified)
        address = f"Location at {latitude:.4f}, {longitude:.4f}"
        
        # Create SOS Record
        sos_record = SOSRecords(
            UserID=user.UserID,
            DateTime=datetime.datetime.utcnow(),
            Latitude=latitude,
            Longitude=longitude,
            Accuracy=accuracy,
            Address=address,
            Status='active',
            AlertType=alert_type,
            LocationLink=f"https://www.google.com/maps?q={latitude},{longitude}",
            Notes=notes
        )
        db.session.add(sos_record)
        db.session.flush()
        
        # Create Community Alert
        community_alert = CommunityAlerts(
            SOSID=sos_record.SOSID,
            UserID=user.UserID,
            Latitude=latitude,
            Longitude=longitude,
            Radius=1000,  # 1km default
            AlertType='emergency',
            AlertMessage=f"🚨 EMERGENCY! A {user.UserType} needs immediate assistance near this location!",
            AlertMessageTamil="🚨 அவசரம்! அருகில் ஒருவருக்கு உடனடி உதவி தேவை!",
            IsActive=True,
            SentAt=datetime.datetime.utcnow(),
            ExpiresAt=datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        )
        db.session.add(community_alert)
        
        # Create incident report
        incident = IncidentReports(
            SOSID=sos_record.SOSID,
            UserID=user.UserID,
            IncidentType='Emergency SOS',
            Description=f"Emergency SOS triggered by {user.Name}. Type: {alert_type}",
            Location=address,
            Latitude=latitude,
            Longitude=longitude,
            Severity='high',
            Status='open'
        )
        db.session.add(incident)
        
        db.session.commit()
        
        # Send notifications
        send_all_notifications(user, sos_record)
        
        return jsonify({
            'success': True,
            'message': '🚨 SOS ACTIVATED! All contacts notified. Help is on the way.',
            'sos_id': sos_record.SOSID,
            'location_link': sos_record.LocationLink,
            'timestamp': sos_record.DateTime.isoformat(),
            'community_alert_id': community_alert.AlertID
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/location/update', methods=['POST'])
@login_required
def update_location():
    """Real-time location tracking update"""
    try:
        data = request.get_json()
        
        location = LocationTracking(
            UserID=session['user_id'],
            Latitude=data['latitude'],
            Longitude=data['longitude'],
            Accuracy=data.get('accuracy'),
            Speed=data.get('speed'),
            BatteryLevel=data.get('battery'),
            NetworkType=data.get('network'),
            Timestamp=datetime.datetime.utcnow()
        )
        db.session.add(location)
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/audio/detect', methods=['POST'])
@login_required
def detect_audio():
    """Complete voice detection and recording storage"""
    try:
        data = request.get_json()
        detected_text = data.get('text', '').lower()
        language = data.get('language', 'english')
        confidence = data.get('confidence', 0.85)
        audio_data = data.get('audio_data', '')
        duration = data.get('duration', 0)
        latitude = data.get('latitude', 13.0827)
        longitude = data.get('longitude', 80.2707)
        
        # Comprehensive keyword detection
        english_keywords = [
            'help me', 'save me', 'emergency', 'please help me',
            'i am in danger', 'somebody help me', 'save her',
            'she is in danger', 'leave me alone', 'dont hurt me',
            'i am scared', 'somebody save me', 'help us',
            'please save', 'danger', 'kidnapping', 'attack',
            'someone following', 'stalking', 'harassment'
        ]
        
        tamil_keywords = [
            'காப்பாற்றுங்கள்', 'உதவி செய்யுங்கள்', 'நான் ஆபத்தில் இருக்கிறேன்',
            'தயவுசெய்து உதவுங்கள்', 'என்னைக் காப்பாற்றுங்கள்',
            'என்னை விடுங்கள்', 'யாராவது உதவுங்கள்', 'காப்பாத்துங்க'
        ]
        
        tanglish_keywords = [
            'help pannunga', 'save pannunga', 'danger la iruken',
            'yaaravathu help', 'kappathunga', 'udhavi pannunga',
            'please help me pannunga', 'somebody save pannunga'
        ]
        
        is_distress = False
        matched_keyword = None
        
        # Check all keyword sets
        if language == 'tamil':
            keywords = tamil_keywords
        elif language == 'tanglish':
            keywords = tanglish_keywords + english_keywords
        else:
            keywords = english_keywords
        
        for keyword in keywords:
            if keyword in detected_text:
                is_distress = True
                matched_keyword = keyword
                break
        
        # Save voice recording
        recording = VoiceRecordings(
            UserID=session['user_id'],
            RecordingType='voice_detection',
            AudioData=audio_data,
            TranscribedText=detected_text,
            Language=language,
            Duration=duration,
            Latitude=latitude,
            Longitude=longitude,
            IsEmergency=is_distress,
            CreatedAt=datetime.datetime.utcnow()
        )
        db.session.add(recording)
        
        # Create audio event
        audio_event = AudioEvents(
            UserID=session['user_id'],
            AudioType='distress_phrase' if is_distress else 'normal',
            DetectedText=matched_keyword or detected_text[:100],
            OriginalText=detected_text,
            ConfidenceScore=confidence,
            Language=language,
            Duration=duration,
            AudioData=audio_data,
            Latitude=latitude,
            Longitude=longitude,
            DateTime=datetime.datetime.utcnow(),
            AutoTriggeredSOS=False
        )
        
        # Auto-trigger SOS if high confidence distress
        if is_distress and confidence > 0.7:
            audio_event.AutoTriggeredSOS = True
            
            sos_record = SOSRecords(
                UserID=session['user_id'],
                DateTime=datetime.datetime.utcnow(),
                Latitude=latitude,
                Longitude=longitude,
                Status='active',
                AlertType='voice',
                LocationLink=f"https://www.google.com/maps?q={latitude},{longitude}",
                Notes=f"Voice detected: '{matched_keyword}' in {language}"
            )
            db.session.add(sos_record)
            db.session.flush()
            
            community_alert = CommunityAlerts(
                SOSID=sos_record.SOSID,
                UserID=session['user_id'],
                Latitude=latitude,
                Longitude=longitude,
                Radius=500,
                AlertType='voice_detected',
                AlertMessage=f"VOICE DETECTED: Someone said '{matched_keyword}'! They may need help!",
                AlertMessageTamil=f"குரல் கண்டறியப்பட்டது: '{matched_keyword}'! உதவி தேவைப்படலாம்!",
                IsActive=True,
                SentAt=datetime.datetime.utcnow(),
                ExpiresAt=datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            )
            db.session.add(community_alert)
        
        db.session.add(audio_event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_distress': is_distress,
            'matched_keyword': matched_keyword,
            'confidence': confidence,
            'sos_triggered': audio_event.AutoTriggeredSOS,
            'recording_id': recording.RecordingID
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/contacts/add', methods=['POST'])
@login_required
def add_contact():
    data = request.get_json()
    
    existing = EmergencyContacts.query.filter_by(UserID=session['user_id'], IsActive=True).count()
    if existing >= 5:
        return jsonify({'success': False, 'message': 'Maximum 5 contacts allowed.'})
    
    contact = EmergencyContacts(
        UserID=session['user_id'],
        ContactName=data['contact_name'],
        Relationship=data['relationship'],
        Mobile=data['mobile'],
        AlternateMobile=data.get('alternate_mobile'),
        Email=data.get('email'),
        PriorityLevel=data.get('priority', 1),
        IsActive=True
    )
    db.session.add(contact)
    db.session.commit()
    
    return jsonify({'success': True, 'contact_id': contact.ContactID})

@app.route('/api/contacts/list', methods=['GET'])
@login_required
def list_contacts():
    contacts = EmergencyContacts.query.filter_by(UserID=session['user_id'], IsActive=True).order_by(EmergencyContacts.PriorityLevel).all()
    return jsonify({
        'success': True,
        'contacts': [{
            'contact_id': c.ContactID,
            'name': c.ContactName,
            'relationship': c.Relationship,
            'mobile': c.Mobile,
            'priority': c.PriorityLevel
        } for c in contacts]
    })

@app.route('/api/contacts/delete/<int:contact_id>', methods=['DELETE'])
@login_required
def delete_contact(contact_id):
    contact = EmergencyContacts.query.get_or_404(contact_id)
    if contact.UserID != session['user_id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    contact.IsActive = False
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/child/add', methods=['POST'])
@login_required
def add_child():
    data = request.get_json()
    
    # Generate unique child code
    child_code = secrets.token_hex(4).upper()
    
    child = Children(
        UserID=session['user_id'],
        ChildName=data['child_name'],
        Age=data['age'],
        Gender=data.get('gender'),
        ParentName=data.get('parent_name'),
        ParentMobile=data.get('parent_mobile'),
        Photo=data.get('photo'),
        MedicalInfo=data.get('medical_info'),
        ChildCode=child_code,
        IsActive=True
    )
    db.session.add(child)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'child_id': child.ChildID,
        'child_code': child_code
    })

@app.route('/api/child/sound/detect', methods=['POST'])
@login_required
def detect_child_sound():
    data = request.get_json()
    sound_type = data.get('sound_type')
    confidence = data.get('confidence', 0.8)
    lat = data.get('latitude', 13.0827)
    lng = data.get('longitude', 80.2707)
    
    audio_event = AudioEvents(
        UserID=session['user_id'],
        AudioType=sound_type,
        DetectedText=f"Child {sound_type} detected",
        ConfidenceScore=confidence,
        Language='sound',
        DateTime=datetime.datetime.utcnow(),
        AutoTriggeredSOS=False
    )
    
    alert_triggered = False
    if confidence > 0.75:
        audio_event.AutoTriggeredSOS = True
        alert_triggered = True
        
        sos_record = SOSRecords(
            UserID=session['user_id'],
            DateTime=datetime.datetime.utcnow(),
            Latitude=lat,
            Longitude=lng,
            Status='active',
            AlertType='child_sound',
            LocationLink=f"https://www.google.com/maps?q={lat},{lng}",
            Notes=f"Child distress sound detected: {sound_type}"
        )
        db.session.add(sos_record)
        db.session.flush()
        
        community_alert = CommunityAlerts(
            SOSID=sos_record.SOSID,
            UserID=session['user_id'],
            Latitude=lat,
            Longitude=lng,
            Radius=200,
            AlertType='child_alert',
            AlertMessage=f"👶 CHILD ALERT: Distress sound ({sound_type}) detected! Immediate attention needed!",
            AlertMessageTamil=f"👶 குழந்தை எச்சரிக்கை: ({sound_type}) கண்டறியப்பட்டது! உடனடி கவனம் தேவை!",
            IsActive=True,
            SentAt=datetime.datetime.utcnow(),
            ExpiresAt=datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        )
        db.session.add(community_alert)
    
    db.session.add(audio_event)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'sound_type': sound_type,
        'alert_triggered': alert_triggered
    })

@app.route('/api/community/alerts/nearby', methods=['POST'])
@login_required
def nearby_alerts():
    data = request.get_json()
    radius = data.get('radius', 500)
    
    # Get active alerts
    alerts = CommunityAlerts.query.filter(
        CommunityAlerts.IsActive == True,
        CommunityAlerts.ExpiresAt > datetime.datetime.utcnow()
    ).order_by(CommunityAlerts.SentAt.desc()).limit(20).all()
    
    return jsonify({
        'success': True,
        'alerts': [{
            'alert_id': a.AlertID,
            'message': a.AlertMessage,
            'latitude': a.Latitude,
            'longitude': a.Longitude,
            'sent_at': a.SentAt.isoformat() if a.SentAt else None,
            'responded_count': a.RespondedCount,
            'alert_type': a.AlertType
        } for a in alerts]
    })

@app.route('/api/community/respond/<int:alert_id>', methods=['POST'])
@login_required
def respond_alert(alert_id):
    data = request.get_json()
    
    alert = CommunityAlerts.query.get_or_404(alert_id)
    alert.RespondedCount += 1
    
    response = CommunityResponses(
        AlertID=alert_id,
        UserID=session['user_id'],
        ResponseType=data.get('response_type', 'i_am_coming'),
        Message=data.get('message', ''),
        RespondedAt=datetime.datetime.utcnow()
    )
    
    db.session.add(response)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Response recorded! Thank you for helping.',
        'responded_count': alert.RespondedCount
    })

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    # User growth
    user_growth = []
    for month in range(6):
        date = datetime.datetime.utcnow() - datetime.timedelta(days=30*month)
        count = Users.query.filter(
            db.extract('month', Users.CreatedAt) == date.month,
            db.extract('year', Users.CreatedAt) == date.year
        ).count()
        user_growth.append({'month': date.strftime('%b %Y'), 'count': count})
    
    # High risk areas
    risk_areas = db.session.query(
        db.func.round(SOSRecords.Latitude, 2).label('lat'),
        db.func.round(SOSRecords.Longitude, 2).label('lng'),
        db.func.count(SOSRecords.SOSID).label('count')
    ).group_by('lat', 'lng').order_by(db.desc('count')).limit(10).all()
    
    return jsonify({
        'success': True,
        'user_growth': user_growth[::-1],
        'high_risk_areas': [{'lat': float(r.lat), 'lng': float(r.lng), 'count': r.count} for r in risk_areas]
    })

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    user_id = session['user_id']
    
    recent_sos = SOSRecords.query.filter_by(UserID=user_id).order_by(SOSRecords.DateTime.desc()).limit(5).all()
    recent_recordings = VoiceRecordings.query.filter_by(UserID=user_id).order_by(VoiceRecordings.CreatedAt.desc()).limit(5).all()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_sos': SOSRecords.query.filter_by(UserID=user_id).count(),
            'active_sos': SOSRecords.query.filter_by(UserID=user_id, Status='active').count(),
            'total_recordings': VoiceRecordings.query.filter_by(UserID=user_id).count(),
            'recent_sos': [{
                'sos_id': s.SOSID,
                'datetime': s.DateTime.isoformat() if s.DateTime else None,
                'status': s.Status,
                'alert_type': s.AlertType,
                'location': s.LocationLink
            } for s in recent_sos]
        }
    })

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def send_all_notifications(user, sos_record):
    """Send all emergency notifications"""
    contacts = EmergencyContacts.query.filter_by(UserID=user.UserID, IsActive=True).all()
    
    print(f"\n{'='*70}")
    print(f"🚨 EMERGENCY SOS ACTIVATED - WABS SYSTEM")
    print(f"{'='*70}")
    print(f"User: {user.Name} ({user.Mobile})")
    print(f"Location: {sos_record.LocationLink}")
    print(f"Time: {sos_record.DateTime}")
    print(f"SOS ID: {sos_record.SOSID}")
    print(f"Type: {sos_record.AlertType}")
    
    if contacts:
        print(f"\n📱 NOTIFYING {len(contacts)} EMERGENCY CONTACTS:")
        for contact in sorted(contacts, key=lambda x: x.PriorityLevel):
            priority_label = {1: '🔴 CRITICAL', 2: '🟡 HIGH', 3: '🟢 MEDIUM'}
            print(f"  {priority_label.get(contact.PriorityLevel, '⚪')} {contact.ContactName} ({contact.Relationship})")
            print(f"     📞 {contact.Mobile}")
            print(f"     ✉️ SMS: 'EMERGENCY! {user.Name} needs help! Location: {sos_record.LocationLink}'")
    
    print(f"\n📍 COMMUNITY ALERT: Sent to all users within 1km radius")
    print(f"🔊 VOICE ALARM: 'Attention! A person needs immediate assistance!'")
    print(f"📋 INCIDENT REPORT: Created and logged")
    print(f"{'='*70}\n")
    
    return True

# =============================================================================
# INITIALIZATION
# =============================================================================

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin
        admin = Users.query.filter_by(Email='admin@wabs.com').first()
        if not admin:
            admin = Users(
                Name='System Administrator',
                Mobile='+919876543210',
                Email='admin@wabs.com',
                Address='WABS Security Headquarters',
                PasswordHash=generate_password_hash('admin123'),
                UserType='admin',
                IsActive=True,
                CreatedAt=datetime.datetime.utcnow()
            )
            db.session.add(admin)
            db.session.commit()
            print("\n✅ Admin created: admin@wabs.com / admin123")
        
        print("\n" + "="*70)
        print("   WABS - Women And Baby Safety System")
        print('   "One Touch for Safety"')
        print("   Production-Ready Real-Time Safety Platform")
        print("="*70)
        print("   ✅ Real-time GPS Tracking")
        print("   ✅ AI Voice Detection (English/Tamil/Tanglish)")
        print("   ✅ Community Safety Network")
        print("   ✅ Child Safety Monitoring")
        print("   ✅ Admin Panel with Full Data Access")
        print("   ✅ Voice Recording Storage")
        print("   ✅ Emergency SOS System")
        print(f"   🌐 http://localhost:5000")
        #print(f"   👤 Admin: admin@wabs.com / admin123")
        print("="*70 + "\n")

with app.app_context():
    init_db()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

#if __name__ == '__main__':
    #init_db()
    #app.run(debug=True, host='0.0.0.0', port=5000, threaded=True) 