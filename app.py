from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import random
from werkzeug.security import generate_password_hash, check_password_hash
from data_loader import ConversationDataLoader
from flask_migrate import Migrate
# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sih-2025-mental-health-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///mental_health.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# Configure Gemini AI with error handling
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')
    GEMINI_AVAILABLE = True
    print("✅ Gemini AI configured successfully!")
except Exception as e:
    print(f"⚠️ Gemini AI not available: {e}")
    print("📝 The platform will work with fallback responses")
    GEMINI_AVAILABLE = False

# Crisis detection keywords
CRISIS_KEYWORDS = [
    'suicide', 'kill myself', 'end my life', 'hurt myself', 'self harm',
    'better off dead', 'no point living', 'want to die', 'ending it all',
    'आत्महत्या', 'मर जाना', 'जीने का मन नहीं', 'खुद को नुकसान', 'जान देना',
    'death', 'die', 'harm', 'cut myself', 'overdose', 'jump', 'hanging'
]

def detect_crisis(message):
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in CRISIS_KEYWORDS)

def get_gemini_response(user_message):
    if not GEMINI_AVAILABLE:
        return get_fallback_response(user_message)
    
    prompt = f"""
    You are "Sahayak" (सहायक), a compassionate AI mental health counselor for Indian college students.
    Respond with empathy and cultural sensitivity. Use both English and Hindi naturally.
    
    User message: {user_message}
    
    Guidelines:
    - Be warm, supportive, and non-judgmental
    - Include Hindi phrases like "आप अकेले नहीं हैं" (You are not alone)
    - Suggest practical coping strategies for Indian students
    - For crisis messages, provide immediate help resources
    - Keep responses under 200 words
    - Address common issues like exam stress, family pressure, homesickness
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return get_fallback_response(user_message)

def get_fallback_response(user_message):
    message_lower = user_message.lower()
    
    if detect_crisis(user_message):
        return """🚨 मुझे आपकी बहुत चिंता हो रही है। आपकी जिंदगी बहुत कीमती है। 

Please reach out immediately:
📞 Campus Counselor Dr. Priya Sharma: 9152987821
📞 24/7 Crisis Helpline: 1800-599-0019
📞 Emergency: 112

आप अकेले नहीं हैं। Help is available."""

    elif any(word in message_lower for word in ['exam', 'test', 'study', 'परीक्षा', 'पढ़ाई']):
        return """मैं समझ सकता हूँ कि परीक्षा का समय कितना तनावपूर्ण होता है। आप अकेले नहीं हैं।

Here are some helpful tips:
• Break study into smaller chunks (छोटे भागों में बांटें)
• Practice deep breathing (गहरी सांस लें)
• Take regular breaks (नियमित विश्राम करें)
• Sleep well (अच्छी नींद लें)

आप कर सकते हैं! You've got this!"""

    elif any(word in message_lower for word in ['lonely', 'alone', 'friends', 'अकेला', 'दोस्त']):
        return """कॉलेज में अकेलापन महसूस करना बहुत आम बात है। आप इसमें अकेले नहीं हैं।

Some suggestions:
• Join campus clubs/activities (कैंपस activities में भाग लें)
• Attend peer support groups (peer support groups में जाएं)
• Start small conversations (छोटी बातचीत शुरू करें)
• Be patient with yourself (अपने साथ धैर्य रखें)

Making friends takes time. यह समय भी गुजर जाएगा।"""

    elif any(word in message_lower for word in ['home', 'miss', 'family', 'घर', 'याद']):
        return """घर की याद आना बिल्कुल normal है। आप बहुत मजबूत हैं।

Coping strategies:
• Video call family regularly (परिवार से video call करें)
• Keep photos/memories close (तस्वीरें पास रखें)
• Find comfort foods nearby (अपना पसंदीदा खाना ढूंढें)
• Connect with students from your region (अपने क्षेत्र के students से मिलें)

यह feeling temporary है। आप adapt कर जाएंगे।"""

    else:
        return """नमस्ते! मैं यहाँ आपकी बात सुनने के लिए हूँ। आप अकेले नहीं हैं।

I'm here to support you through:
• Academic stress (शैक्षणिक तनाव)
• Social anxiety (सामाजिक चिंता)
• Homesickness (घर की याद)
• General mental health concerns

Feel free to share what's on your mind. आप बेझिझक अपनी बात कह सकते हैं।

Emergency contacts:
📞 Dr. Priya Sharma: 9152987821
📞 Crisis Helpline: 1800-599-0019"""

# Enhanced Database Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), default='Not specified')
    location = db.Column(db.String(100), default='Not specified')
    hostel_resident = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(15), default='')
    emergency_contact = db.Column(db.String(15), default='')
    anonymous_id = db.Column(db.String(50), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    screening_results = db.relationship('ScreeningResult', backref='student', lazy=True)
    chat_conversations = db.relationship('ChatConversation', backref='student', lazy=True)
    forum_posts = db.relationship('ForumPost', backref='student', lazy=True)
    crisis_incidents = db.relationship('CrisisIncident', backref='student', lazy=True)
    dark_mode = db.Column(db.Boolean, default=False)

    bio = db.Column(db.Text, default='')
    college = db.Column(db.String(255), default='')
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    push_notifications = db.Column(db.Boolean, default=True)
    profile_public = db.Column(db.Boolean, default=False)
    show_online_status = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='Asia/Kolkata')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScreeningResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    phq9_score = db.Column(db.Integer, nullable=False)
    gad7_score = db.Column(db.Integer, nullable=False)
    phq9_responses = db.Column(db.Text, nullable=False)  # JSON string
    gad7_responses = db.Column(db.Text, nullable=False)  # JSON string
    phq9_category = db.Column(db.String(50), nullable=False)
    gad7_category = db.Column(db.String(50), nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    recommendations = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatConversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    crisis_detected = db.Column(db.Boolean, default=False)
    sentiment_score = db.Column(db.Float, default=0.0)
    response_time = db.Column(db.Float, default=0.0)  # Response time in seconds
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(20), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    language = db.Column(db.String(20), default='English')
    author = db.Column(db.String(100), default='')
    duration = db.Column(db.String(20), default='')  # For videos/audio
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='General')
    anonymous_id = db.Column(db.String(50), nullable=False)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    replies = db.relationship('ForumReply', backref='post', lazy=True)

class ForumReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    anonymous_id = db.Column(db.String(50), nullable=False)
    likes = db.Column(db.Integer, default=0)
    is_helpful = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='forum_replies')

class CrisisIncident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='open')
    counselor_assigned = db.Column(db.String(100), default='')
    counselor_notified = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime)
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

class Counselor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.Text, nullable=False)
    languages = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    office_location = db.Column(db.String(200), nullable=False)
    availability = db.Column(db.Text, nullable=False)
    current_caseload = db.Column(db.Integer, default=0)
    max_capacity = db.Column(db.Integer, default=50)
    is_available = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Float, default=5.0)

class MoodTracker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    energy_level = db.Column(db.Integer, nullable=False)  # 1-10 scale
    stress_level = db.Column(db.Integer, nullable=False)  # 1-10 scale
    sleep_hours = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='mood_entries')

# Routes
@app.route('/')
def home():
    total_students = Student.query.filter_by(is_admin=False).count()
    total_sessions = ChatConversation.query.count()
    active_crises = CrisisIncident.query.filter_by(status='open').count()
    
    return render_template('home.html', 
                         total_students=total_students,
                         total_sessions=total_sessions,
                         active_crises=active_crises)

@app.route('/game_zone')
def game_zone():
    # Main landing page for games
    return render_template('game_zone.html')

# Add these imports at the top if not already present

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'student_id' not in session:
        flash('Please log in to access your profile.', 'error')
        return redirect(url_for('login'))

    user = Student.query.get(session['student_id'])
    if not user:
        flash('User not found.', 'error')
        session.clear()
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Update user profile using SQLAlchemy ORM
        user.name = request.form.get('name', user.name)
        user.phone = request.form.get('phone', user.phone or '')
        user.location = request.form.get('college', user.location or '')  # Using existing location field
        # Note: bio field doesn't exist in your Student model, you may need to add it
        
        try:
            db.session.commit()
            session['student_name'] = user.name  # Update session
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
            return redirect(url_for('profile'))

    # Calculate user statistics
    chat_sessions = ChatConversation.query.filter_by(student_id=user.id).count()
    assessments_taken = ScreeningResult.query.filter_by(student_id=user.id).count()
    days_active = (datetime.utcnow() - user.created_at).days + 1

    # Add calculated stats to user object for template
    user.chat_sessions = chat_sessions
    user.assessments_taken = assessments_taken
    user.days_active = days_active

    return render_template('profile.html', user=user)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'student_id' not in session:
        flash('Please log in to access settings.', 'error')
        return redirect(url_for('login'))

    user = Student.query.get(session['student_id'])
    if not user:
        flash('User not found.', 'error')
        session.clear()
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Handle dark mode toggle
        user.dark_mode = 'dark_mode' in request.form
        user.email_notifications = 'email_notifications' in request.form
        user.sms_notifications = 'sms_notifications' in request.form
        user.push_notifications = 'push_notifications' in request.form
        user.profile_public = 'profile_public' in request.form
        user.show_online_status = 'show_online_status' in request.form
        user.language = request.form.get('language', 'en')
        user.timezone = request.form.get('timezone', 'Asia/Kolkata')
        
        try:
            db.session.commit()
            # Update session to reflect dark mode change
            session['dark_mode'] = user.dark_mode
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'error')
            return redirect(url_for('settings'))

    return render_template('settings.html', user=user)


# Individual game routes -- add these
@app.route('/games/<game_name>')
def game_page(game_name):
    valid_games = [
        'breathing_buddy', 'meditation_garden', 'chakra_balance', 'stress_ball_squeeze', 'exam_anxiety_fighter',
        'mood_weather', 'gratitude_tree', 'kindness_ripple', 'habit_builder', 'memory_palace', 'emotion_detective', 'campus_compass'
    ]
    if game_name not in valid_games:
        return render_template('404.html'), 404
    return render_template(f'games/{game_name}.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        student = Student.query.filter_by(email=email).first()
        
        if student and check_password_hash(student.password_hash, password):
            session['student_id'] = student.id
            session['student_name'] = student.name
            session['is_admin'] = student.is_admin
            session['dark_mode'] = student.dark_mode  # Add this line
            
            # Update last active
            student.last_active = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {student.name}!', 'success')
            
            if student.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/toggle_dark_mode', methods=['POST'])
def toggle_dark_mode():
    if 'student_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = Student.query.get(session['student_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Toggle dark mode
    user.dark_mode = not user.dark_mode
    db.session.commit()
    
    # Update session
    session['dark_mode'] = user.dark_mode
    
    return jsonify({'dark_mode': user.dark_mode})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        year = request.form['year']
        branch = request.form['branch']
        age = int(request.form['age'])
        gender = request.form.get('gender', 'Not specified')
        location = request.form.get('location', 'Not specified')
        hostel_resident = 'hostel_resident' in request.form
        phone = request.form.get('phone', '')
        emergency_contact = request.form.get('emergency_contact', '')
        
        if Student.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        anonymous_id = f"Anonymous_{random.choice(['Panda', 'Tiger', 'Eagle', 'Phoenix', 'Lion', 'Butterfly', 'Lotus', 'Swan', 'Peacock', 'Elephant'])}_{random.randint(10, 99)}"
        
        student = Student(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            year=year,
            branch=branch,
            age=age,
            gender=gender,
            location=location,
            hostel_resident=hostel_resident,
            phone=phone,
            emergency_contact=emergency_contact,
            anonymous_id=anonymous_id
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    name = session.get('student_name', 'User')
    session.clear()
    flash(f'Goodbye, {name}!', 'info')
    return redirect(url_for('home'))

@app.route('/chat')
def chat():
    if 'student_id' not in session:
        flash('Please login to access chat', 'error')
        return redirect(url_for('login'))
    
    conversations = ChatConversation.query.filter_by(
        student_id=session['student_id']
    ).order_by(ChatConversation.timestamp.desc()).limit(50).all()
    
    return render_template('chat.html', conversations=conversations[::-1])

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'student_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
    
    start_time = datetime.utcnow()
    
    crisis_detected = detect_crisis(user_message)
    ai_response = get_gemini_response(user_message)
    
    response_time = (datetime.utcnow() - start_time).total_seconds()
    
    conversation = ChatConversation(
        student_id=session['student_id'],
        user_message=user_message,
        bot_response=ai_response,
        crisis_detected=crisis_detected,
        response_time=response_time
    )
    db.session.add(conversation)
    
    if crisis_detected:
        crisis = CrisisIncident(
            student_id=session['student_id'],
            message=user_message,
            severity='high',
            counselor_notified=True,
            counselor_assigned='Dr. Priya Sharma'
        )
        db.session.add(crisis)
        print(f"🚨 CRISIS DETECTED for student {session['student_id']}")
    
    db.session.commit()
    
    return jsonify({
        'response': ai_response,
        'crisis_detected': crisis_detected,
        'timestamp': conversation.timestamp.strftime('%H:%M'),
        'gemini_status': 'active' if GEMINI_AVAILABLE else 'fallback'
    })

@app.route('/screening')
def screening():
    if 'student_id' not in session:
        flash('Please login to take screening', 'error')
        return redirect(url_for('login'))
    
    # Check if user has taken screening in last 7 days
    recent_screening = ScreeningResult.query.filter_by(
        student_id=session['student_id']
    ).filter(
        ScreeningResult.created_at >= datetime.utcnow() - timedelta(days=7)
    ).first()
    
    return render_template('screening.html', recent_screening=recent_screening)

@app.route('/submit_screening', methods=['POST'])
def submit_screening():
    if 'student_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    # PHQ-9 and GAD-7 responses
    phq9_responses = [int(request.form.get(f'phq9_{i}', 0)) for i in range(1, 10)]
    gad7_responses = [int(request.form.get(f'gad7_{i}', 0)) for i in range(1, 8)]
    
    phq9_score = sum(phq9_responses)
    gad7_score = sum(gad7_responses)
    
    def get_phq9_category(score):
        if score <= 4: return "Minimal Depression"
        elif score <= 9: return "Mild Depression"
        elif score <= 14: return "Moderate Depression"
        elif score <= 19: return "Moderately Severe Depression"
        else: return "Severe Depression"
    
    def get_gad7_category(score):
        if score <= 4: return "Minimal Anxiety"
        elif score <= 9: return "Mild Anxiety"
        elif score <= 14: return "Moderate Anxiety"
        else: return "Severe Anxiety"
    
    def get_risk_level(phq9, gad7):
        if phq9 >= 20 or gad7 >= 15 or (phq9 >= 15 and gad7 >= 10):
            return 'high'
        elif phq9 >= 10 or gad7 >= 10:
            return 'moderate'
        else:
            return 'low'
    
    def get_recommendations(risk_level):
        if risk_level == 'high':
            return [
                "तुरंत counselor से मिलना जरूरी है - Immediate counselor consultation recommended",
                "Dr. Priya Sharma से संपर्क करें: 9152987821",
                "24/7 Crisis Helpline: 1800-599-0019",
                "Daily self-care activities शुरू करें",
                "Family/friends को inform करें (with consent)"
            ]
        elif risk_level == 'moderate':
            return [
                "नियमित counseling sessions की सलाह दी जाती है",
                "Stress management workshops में join करें",
                "रोजाना meditation का अभ्यास करें",
                "Social connections बनाए रखें",
                "Academic support लें यदि जरूरत हो"
            ]
        else:
            return [
                "Self-care practices जारी रखें",
                "Wellness activities में भाग लें",
                "नियमित रूप से mood को monitor करें",
                "यदि feelings worse हों तो तुरंत help लें",
                "Healthy lifestyle maintain करें"
            ]
    
    phq9_category = get_phq9_category(phq9_score)
    gad7_category = get_gad7_category(gad7_score)
    risk_level = get_risk_level(phq9_score, gad7_score)
    recommendations = get_recommendations(risk_level)
    
    screening = ScreeningResult(
        student_id=session['student_id'],
        phq9_score=phq9_score,
        gad7_score=gad7_score,
        phq9_responses=str(phq9_responses),
        gad7_responses=str(gad7_responses),
        phq9_category=phq9_category,
        gad7_category=gad7_category,
        risk_level=risk_level,
        recommendations='\n'.join(recommendations)
    )
    db.session.add(screening)
    
    # Create crisis incident for high risk
    if risk_level == 'high':
        crisis = CrisisIncident(
            student_id=session['student_id'],
            message=f"High risk screening result - PHQ-9: {phq9_score}, GAD-7: {gad7_score}",
            severity='high',
            counselor_notified=True
        )
        db.session.add(crisis)
    
    db.session.commit()
    
    return render_template('screening_result.html',
                         screening=screening,
                         recommendations=recommendations)

@app.route('/resources')
def resources():
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = Resource.query
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(Resource.title.contains(search) | Resource.description.contains(search))
    
    resources_list = query.order_by(Resource.is_featured.desc(), Resource.views.desc()).all()
    
    categories = [
        'Academic Stress', 'Anxiety', 'Depression', 'Social Anxiety', 
        'Sleep Issues', 'Family Issues', 'Career Guidance', 'Relationships',
        'Self-Care', 'Mindfulness', 'Crisis Support'
    ]
    
    return render_template('resources.html', 
                         resources=resources_list, 
                         categories=categories, 
                         selected_category=category,
                         search_query=search)

@app.route('/resource/<int:resource_id>')
def view_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    
    # Increment views
    resource.views += 1
    db.session.commit()
    
    return render_template('resource_detail.html', resource=resource)

@app.route('/forum')
def forum():
    category = request.args.get('category', '')
    sort_by = request.args.get('sort', 'recent')
    
    query = ForumPost.query
    
    if category:
        query = query.filter_by(category=category)
    
    if sort_by == 'popular':
        query = query.order_by(ForumPost.likes.desc(), ForumPost.views.desc())
    elif sort_by == 'resolved':
        query = query.filter_by(is_resolved=True).order_by(ForumPost.created_at.desc())
    else:  # recent
        query = query.order_by(ForumPost.is_pinned.desc(), ForumPost.created_at.desc())
    
    posts = query.all()
    
    categories = ['General', 'Academic', 'Social', 'Mental Health', 'Career', 'Relationships', 'Campus Life']
    
    return render_template('forum.html', posts=posts, categories=categories, 
                         selected_category=category, sort_by=sort_by)

@app.route('/forum/post/<int:post_id>')
def forum_post_detail(post_id):
    post = ForumPost.query.get_or_404(post_id)
    
    # Increment views
    post.views += 1
    db.session.commit()
    
    replies = ForumReply.query.filter_by(post_id=post_id).order_by(ForumReply.created_at.asc()).all()
    
    return render_template('forum_post_detail.html', post=post, replies=replies)

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'student_id' not in session:
        flash('Please login to create a post', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        
        student = Student.query.get(session['student_id'])
        
        post = ForumPost(
            title=title,
            content=content,
            category=category,
            student_id=session['student_id'],
            anonymous_id=student.anonymous_id
        )
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('forum_post_detail', post_id=post.id))
    
    categories = ['General', 'Academic', 'Social', 'Mental Health', 'Career', 'Relationships', 'Campus Life']
    return render_template('create_post.html', categories=categories)

@app.route('/mood_tracker')
def mood_tracker():
    if 'student_id' not in session:
        flash('Please login to access mood tracker', 'error')
        return redirect(url_for('login'))
    
    # Get recent mood entries
    mood_entries = MoodTracker.query.filter_by(
        student_id=session['student_id']
    ).order_by(MoodTracker.created_at.desc()).limit(30).all()
    
    for entry in mood_entries:
        entry.mood_score = entry.mood_score or 0
        entry.energy_level = entry.energy_level or 0
        entry.stress_level = entry.stress_level or 0

    return render_template('mood_tracker.html', mood_entries=mood_entries)

@app.route('/submit_mood', methods=['POST'])
def submit_mood():
    if 'student_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    mood_score = int(request.form['mood_score'])
    energy_level = int(request.form['energy_level'])
    stress_level = int(request.form['stress_level'])
    sleep_hours = float(request.form.get('sleep_hours', 0))
    notes = request.form.get('notes', '')
    
    mood_entry = MoodTracker(
        student_id=session['student_id'],
        mood_score=mood_score,
        energy_level=energy_level,
        stress_level=stress_level,
        sleep_hours=sleep_hours,
        notes=notes
    )
    db.session.add(mood_entry)
    db.session.commit()
    
    flash('Mood entry saved successfully!', 'success')
    return redirect(url_for('mood_tracker'))

@app.route('/counselors')
def counselors():
    counselors_list = Counselor.query.filter_by(is_available=True).order_by(Counselor.rating.desc()).all()
    return render_template('counselors.html', counselors=counselors_list)

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Access denied. Admin login required.', 'error')
        return redirect(url_for('login'))
    
    # Statistics
    total_students = Student.query.filter_by(is_admin=False).count()
    total_screenings = ScreeningResult.query.count()
    high_risk_students = ScreeningResult.query.filter_by(risk_level='high').count()
    crisis_incidents = CrisisIncident.query.filter_by(status='open').count()
    total_chats = ChatConversation.query.count()
    total_forum_posts = ForumPost.query.count()
    
    # Recent activities
    recent_crises = CrisisIncident.query.filter_by(status='open').order_by(CrisisIncident.created_at.desc()).limit(10).all()
    recent_screenings = ScreeningResult.query.order_by(ScreeningResult.created_at.desc()).limit(10).all()
    
    # Monthly trends (last 6 months)
    monthly_data = []
    for i in range(6):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        screenings = ScreeningResult.query.filter(
            ScreeningResult.created_at >= month_start,
            ScreeningResult.created_at < month_end
        ).count()
        
        high_risk = ScreeningResult.query.filter(
            ScreeningResult.created_at >= month_start,
            ScreeningResult.created_at < month_end,
            ScreeningResult.risk_level == 'high'
        ).count()
        
        crisis_count = CrisisIncident.query.filter(
            CrisisIncident.created_at >= month_start,
            CrisisIncident.created_at < month_end
        ).count()
        
        monthly_data.append({
            "month": month_start.strftime('%B %Y'),
            "screenings": screenings,
            "high_risk": high_risk,
            "crisis_incidents": crisis_count
        })
    
    return render_template('admin/dashboard.html',
                         total_students=total_students,
                         total_screenings=total_screenings,
                         high_risk_students=high_risk_students,
                         crisis_incidents=crisis_incidents,
                         total_chats=total_chats,
                         total_forum_posts=total_forum_posts,
                         recent_crises=recent_crises,
                         recent_screenings=recent_screenings,
                         monthly_trends=monthly_data[::-1])

import os
import json
import random
from datetime import datetime, timedelta

def load_conversations_from_json(file_path, students):
    """Load conversation data from JSON file"""
    try:
        # Get the absolute path to the JSON file
        if not os.path.isabs(file_path):
            # If relative path, make it relative to the Flask app directory
            file_path = os.path.join(os.path.dirname(__file__), file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            conversations_data = json.load(f)
        
        conversations = []
        for item in conversations_data:
            # Get student by index, cycling if necessary
            student_index = item.get('student_index', 0) % len(students)
            student = students[student_index]
            
            conversation = {
                'student_id': student.id,
                'user_message': item.get('user_message', ''),
                'bot_response': item.get('bot_response', ''),
                'crisis_detected': item.get('crisis_detected', False),
                'sentiment_score': item.get('sentiment_score', 0.0),
                'response_time': item.get('response_time', 1.0),
                'timestamp': datetime.utcnow() - timedelta(hours=random.randint(1, 72))
            }
            conversations.append(conversation)
        
        return conversations
        
    except FileNotFoundError:
        print(f"⚠️ Conversation file {file_path} not found. Using fallback conversations.")
        return create_fallback_conversations(students)
    except json.JSONDecodeError:
        print(f"⚠️ Error parsing JSON in {file_path}. Using fallback conversations.")
        return create_fallback_conversations(students)

def create_fallback_conversations(students):
    """Fallback conversations if JSON file is not available"""
    sample_conversations = [
        ("I'm feeling stressed about exams", "Exams can be tough. Remember to take breaks.", False),
        ("I feel lonely here", "You're not alone. Many students feel the same.", False),
        ("Need help with time management", "Let me share some time management strategies.", False)
    ]
    
    conversations = []
    for i, (user_msg, bot_msg, crisis) in enumerate(sample_conversations):
        if i < len(students):
            conversation = {
                'student_id': students[i].id,
                'user_message': user_msg,
                'bot_response': bot_msg,
                'crisis_detected': crisis,
                'sentiment_score': 0.5,
                'response_time': 1.0,
                'timestamp': datetime.utcnow() - timedelta(hours=random.randint(1, 72))
            }
            conversations.append(conversation)
    
    return conversations

def populate_sample_data():
    """Populate comprehensive sample data"""
    if Student.query.count() > 0:
        return
    
    print("Populating comprehensive sample data...")
    
    # STEP 1: Create admin user FIRST
    admin = Student(
        name="Admin User",
        email="admin@college.edu",
        password_hash=generate_password_hash("admin123"),
        year="Staff",
        branch="Administration",
        age=30,
        gender="Not specified",
        anonymous_id="Admin_001",
        is_admin=True
    )
    db.session.add(admin)
    
    # STEP 2: Create all students
    students_data = [
        {"name": "Arjun Sharma", "email": "arjun@student.edu", "year": "Second Year", "branch": "Computer Science", "age": 19, "gender": "Male", "location": "Delhi"},
        {"name": "Priya Patel", "email": "priya@student.edu", "year": "Final Year", "branch": "Mechanical Engineering", "age": 21, "gender": "Female", "location": "Gujarat"},
        {"name": "Rahul Kumar", "email": "rahul@student.edu", "year": "Third Year", "branch": "Electronics", "age": 20, "gender": "Male", "location": "Bihar"},
        {"name": "Sneha Singh", "email": "sneha@student.edu", "year": "First Year", "branch": "Civil Engineering", "age": 18, "gender": "Female", "location": "UP"},
        {"name": "Vikram Mehta", "email": "vikram@student.edu", "year": "Final Year", "branch": "Biotechnology", "age": 22, "gender": "Male", "location": "Rajasthan"},
        {"name": "Ananya Gupta", "email": "ananya@student.edu", "year": "Second Year", "branch": "Information Technology", "age": 19, "gender": "Female", "location": "Maharashtra"},
        {"name": "Rohan Verma", "email": "rohan@student.edu", "year": "Third Year", "branch": "Electrical Engineering", "age": 21, "gender": "Male", "location": "Punjab"},
        {"name": "Kavya Reddy", "email": "kavya@student.edu", "year": "First Year", "branch": "Chemical Engineering", "age": 18, "gender": "Female", "location": "Telangana"},
        {"name": "Aditya Jain", "email": "aditya@student.edu", "year": "Second Year", "branch": "Aerospace", "age": 20, "gender": "Male", "location": "Karnataka"},
        {"name": "Shreya Nair", "email": "shreya@student.edu", "year": "Third Year", "branch": "Biomedical", "age": 21, "gender": "Female", "location": "Kerala"},
    ]
    
    students = []
    for data in students_data:
        student = Student(
            name=data["name"],
            email=data["email"],
            password_hash=generate_password_hash("password123"),
            year=data["year"],
            branch=data["branch"],
            age=data["age"],
            gender=data["gender"],
            location=data["location"],
            hostel_resident=random.choice([True, False]),
            phone=f"9{random.randint(100000000, 999999999)}",
            emergency_contact=f"9{random.randint(100000000, 999999999)}",
            anonymous_id=f"Anonymous_{random.choice(['Panda', 'Tiger', 'Eagle', 'Phoenix', 'Lion', 'Butterfly', 'Lotus', 'Swan'])}_{random.randint(10, 99)}"
        )
        students.append(student)
        db.session.add(student)
    
    # STEP 3: COMMIT STUDENTS FIRST - This assigns IDs!
    db.session.commit()
    print(f"✅ Created {len(students) + 1} students with IDs")
    
    # STEP 4: Now create screening results (students have IDs now)
    for i, student in enumerate(students[:5]):  # Only first 5 students
        phq9_score = random.randint(0, 25)
        gad7_score = random.randint(0, 20)
        
        def get_phq9_category(score):
            if score <= 4: return "Minimal Depression"
            elif score <= 9: return "Mild Depression"
            elif score <= 14: return "Moderate Depression"
            elif score <= 19: return "Moderately Severe Depression"
            else: return "Severe Depression"
        
        def get_gad7_category(score):
            if score <= 4: return "Minimal Anxiety"
            elif score <= 9: return "Mild Anxiety"
            elif score <= 14: return "Moderate Anxiety"
            else: return "Severe Anxiety"
        
        risk_level = 'low'
        if phq9_score >= 20 or gad7_score >= 15:
            risk_level = 'high'
        elif phq9_score >= 10 or gad7_score >= 10:
            risk_level = 'moderate'
        
        screening = ScreeningResult(
            student_id=student.id,  # Now student.id exists!
            phq9_score=phq9_score,
            gad7_score=gad7_score,
            phq9_responses=str([random.randint(0, 3) for _ in range(9)]),
            gad7_responses=str([random.randint(0, 3) for _ in range(7)]),
            phq9_category=get_phq9_category(phq9_score),
            gad7_category=get_gad7_category(gad7_score),
            risk_level=risk_level,
            recommendations="Sample recommendations",
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        db.session.add(screening)
    
    # STEP 5: 🎯 LOAD CONVERSATIONS FROM JSON FILE
    print("📄 Loading conversations from JSON file...")
    conversations_data = load_conversations_from_json('data/conversations.json', students)
    
    for conversation_data in conversations_data:
        conversation = ChatConversation(**conversation_data)
        db.session.add(conversation)
    
    print(f"✅ Created {len(conversations_data)} conversations from JSON file")
    
    # STEP 6: Create resources
    resources_data = [
        {
            "title": "Stress Management Techniques (तनाव प्रबंधन तकनीकें)",
            "description": "परीक्षा और academic pressure को handle करने के व्यावहारिक तरीके।",
            "category": "Academic Stress",
            "resource_type": "video",
            "url": "https://youtube.com/watch?v=stress-management",
            "author": "Dr. Priya Sharma",
            "duration": "15 mins",
            "is_featured": True
        },
        {
            "title": "Meditation and Mindfulness Guide (ध्यान और सचेतना)",
            "description": "Daily meditation practices with Hindi guidance।",
            "category": "Anxiety",
            "resource_type": "audio",
            "url": "https://example.com/meditation.mp3",
            "author": "Mindfulness Coach",
            "duration": "10 mins"
        },
        {
            "title": "Sleep Hygiene for Students (छात्रों के लिए नींद की स्वच्छता)",
            "description": "Better mental health के लिए quality sleep की importance।",
            "category": "Self-Care",
            "resource_type": "article",
            "url": "https://example.com/sleep-guide",
            "author": "Health Expert"
        }
    ]
    
    for data in resources_data:
        resource = Resource(
            title=data["title"],
            description=data["description"],
            category=data["category"],
            resource_type=data["resource_type"],
            url=data["url"],
            author=data.get("author", ""),
            duration=data.get("duration", ""),
            language="Hindi/English",
            views=random.randint(50, 500),
            likes=random.randint(10, 100),
            is_featured=data.get("is_featured", False)
        )
        db.session.add(resource)
    
    # STEP 7: Create forum posts
    forum_posts_data = [
        {
            "title": "Exam stress is overwhelming me (परीक्षा का तनाव)",
            "content": "I have back-to-back exams और रात में नींद नहीं आती। Anyone else feeling the same?",
            "category": "Academic",
            "student_idx": 0
        },
        {
            "title": "Difficulty making friends in college",
            "content": "I'm in my third year और अभी भी struggle करता हूँ close friends बनाने में।",
            "category": "Social", 
            "student_idx": 2
        }
    ]
    
    for post_data in forum_posts_data:
        post = ForumPost(
            title=post_data["title"],
            content=post_data["content"],
            category=post_data["category"],
            student_id=students[post_data["student_idx"]].id,  # Use valid student ID
            anonymous_id=students[post_data["student_idx"]].anonymous_id,
            views=random.randint(10, 100),
            likes=random.randint(1, 20),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 15))
        )
        db.session.add(post)
    
    # STEP 8: Create counselors
    counselors_data = [
        {
            "name": "Dr. Priya Sharma",
            "designation": "Clinical Psychologist",
            "specialization": "Depression, Anxiety, Academic Stress",
            "languages": "Hindi, English, Punjabi",
            "phone": "9152987821",
            "email": "priya.sharma@college.edu",
            "office_location": "Student Welfare Building, Room 201",
            "availability": "Monday-Friday: 9AM-5PM",
            "current_caseload": 45,
            "max_capacity": 60,
            "rating": 4.8
        }
    ]
    
    for counselor_data in counselors_data:
        counselor = Counselor(**counselor_data)
        db.session.add(counselor)
    
    # STEP 9: Create crisis incidents for high-risk students
    if len(students) > 1:
        crisis = CrisisIncident(
            student_id=students[1].id,  # Use valid student ID
            message="I can't handle this placement pressure anymore",
            severity="high",
            counselor_assigned="Dr. Priya Sharma",
            counselor_notified=True,
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        db.session.add(crisis)
    
    # FINAL COMMIT
    db.session.commit()
    print("Comprehensive sample data created successfully!")
    print(f"✅ Created {len(students) + 1} students")
    print(f"✅ Created {len(conversations_data)} conversations from JSON")
    print(f"✅ Created {len(resources_data)} resources")
    print(f"✅ Created {len(forum_posts_data)} forum posts")
    print(f"✅ Created {len(counselors_data)} counselors")
    print(f"✅ Created screening results, chat conversations, and mood data")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        populate_sample_data()
        
        print("\n🚀 Enhanced Mental Health Platform Starting...")
        print("📊 Admin Login: admin@college.edu / admin123")
        print("👤 Student Login: arjun@student.edu / password123")
        print("🔗 Platform URL: http://localhost:5000")
        if GEMINI_AVAILABLE:
            print("✅ Gemini AI: Active")
        else:
            print("⚠️ Gemini AI: Using fallback responses")
        print("\n🎯 Features Available:")
        print("   • AI Chat Support with Crisis Detection")
        print("   • PHQ-9 & GAD-7 Mental Health Screening")
        print("   • Resource Library with 8+ categories")
        print("   • Anonymous Peer Support Forum")
        print("   • Mood Tracking System")
        print("   • Professional Counselor Directory")
        print("   • Comprehensive Admin Dashboard")
        print("   • Mobile-Responsive Design")
        
    app.run()
