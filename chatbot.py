from flask import Flask, render_template, request, session, redirect
import sqlite3
import json
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-in-production'
# Database setup
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT
)
""")

conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


# Load FAQ data from JSON file
def load_faq_data():
    try:
        with open('faq.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('COLLEGE_FAQ_DATA', [])
    except FileNotFoundError:
        print("faq.json file not found!")
        return []

# Load the FAQ data at startup
FAQ_DATA = load_faq_data()

def find_best_match(user_input):
    """Find the best matching FAQ entry based on tags with improved matching"""
    user_input_lower = user_input.lower().strip()
    
    # Common keywords mapping to categories
    keyword_mapping = {
        'course': ['courses', 'programs', 'btech', 'mtech', 'branch', 'department', 'cse', 'ece', 'eee', 'me', 'civil', 'it'],
        'fee': ['fees', 'fee structure', 'tuition', 'cost', 'amount', 'payment', 'btech fee', 'mtech fee', 'hostel fee'],
        'admission': ['admission', 'apply', 'procedure', 'keam', 'eligibility', 'lateral entry', 'join'],
        'placement': ['placement', 'job', 'career', 'recruitment', 'company', 'package', 'salary', 'internship'],
        'hostel': ['hostel', 'accommodation', 'boarding', 'room', 'mess', 'shahanas'],
        'library': ['library', 'book', 'reading', 'journal', 'study'],
        'contact': ['contact', 'phone', 'email', 'address', 'number', 'call'],
        'timing': ['timing', 'time', 'schedule', 'hour', 'open', 'close'],
        'sports': ['sports', 'game', 'gym', 'football', 'cricket', 'volleyball', 'badminton'],
        'bus': ['bus', 'transport', 'commute', 'pickup', 'route', 'travel'],
        'faculty': ['faculty', 'teacher', 'professor', 'staff', 'hod', 'dean'],
        'campus': ['campus', 'building', 'facility', 'infrastructure', 'lab', 'canteen'],
        'club': ['club', 'association', 'activity', 'iedc', 'technical club'],
        'scholarship': ['scholarship', 'financial aid', 'grant', 'fee waiver']
    }
    
    best_match = None
    best_score = 0
    matched_keywords = []
    
    # First, check which category the query belongs to
    for category, keywords in keyword_mapping.items():
        for keyword in keywords:
            if keyword in user_input_lower:
                matched_keywords.append(category)
                break
    
    # Search through FAQ data
    for item in FAQ_DATA:
        tags = item.get('tags', [])
        score = 0
        
        # Check each tag
        for tag in tags:
            tag_lower = tag.lower()
            
            # Exact match (highest priority)
            if tag_lower == user_input_lower:
                score += 10
            # Tag is in user input
            elif tag_lower in user_input_lower:
                score += 5
            # User input is in tag
            elif user_input_lower in tag_lower:
                score += 3
            # Partial word match
            elif any(word in tag_lower for word in user_input_lower.split()):
                score += 1
        
        # Bonus for matched categories
        for category in matched_keywords:
            if any(category in tag.lower() for tag in tags):
                score += 2
        
        if score > best_score:
            best_score = score
            best_match = item
    
    # If no match found with decent score, try partial matching
    if best_score < 2:
        for item in FAQ_DATA:
            tags = item.get('tags', [])
            for tag in tags:
                # Check if any significant word matches
                tag_words = tag.lower().split()
                user_words = user_input_lower.split()
                if any(word in tag_words or tag_word in user_words for word in user_words for tag_word in tag_words):
                    best_match = item
                    best_score = 1
                    break
            if best_match:
                break
    
    return best_match

def format_response(answer_facts):
    """Format the answer facts into a readable response"""
    if not answer_facts:
        return None
    
    response_parts = []
    
    # Format all facts nicely
    for key, value in answer_facts.items():
        # Skip if value is empty
        if not value:
            continue
        response_parts.append(f"• **{key}:** {value}")
    
    if response_parts:
        return "\n".join(response_parts)
    return None

def get_response(user_input):
    """Get response based on user input"""
    if not user_input or user_input.strip() == "":
        return "Please type something 🙂"
    
    user_input_lower = user_input.lower().strip()
    
    # Check for greetings
    if any(word in user_input_lower for word in ['hi', 'hello', 'hey', 'namaste']):
        return ("👋 Hello! I'm LBS College AI Assistant.\n\n"
                "I can help you with:\n"
                "• 📚 Courses & Programs\n"
                "• 💰 Fee Structure\n"
                "• 🎓 Admissions\n"
                "• 💼 Placements\n"
                "• 🏠 Hostel Facilities\n"
                "• 📖 Library Timings\n"
                "• 🚌 Bus Services\n"
                "• 📞 Contact Information\n\n"
                "What would you like to know?")
    
    # Check for thank you
    if any(word in user_input_lower for word in ['thanks', 'thank', 'thnks']):
        return "You're welcome! 😊 Is there anything else I can help you with?"
    
    # Find best matching FAQ entry
    matched_item = find_best_match(user_input)
    
    if matched_item:
        answer_facts = matched_item.get('answer_facts', {})
        formatted_response = format_response(answer_facts)
        
        if formatted_response:
            return formatted_response
    
    # If still no match, provide helpful suggestions
    return ("Sorry, I didn't understand that 😅\n\n"
            "Try asking about these topics:\n"
            "• 📚 **Courses** - What B.Tech courses are available?\n"
            "• 💰 **Fees** - What is the fee structure?\n"
            "• 🎓 **Admission** - How to get admission?\n"
            "• 💼 **Placement** - What is the placement record?\n"
            "• 🏠 **Hostel** - Does college have hostel facilities?\n"
            "• 📖 **Library** - What are library timings?\n"
            "• 🚌 **Bus** - Is there college bus service?\n"
            "• 📞 **Contact** - How to contact the college?\n\n"
            "Or type a specific question!")

@app.route("/")
def home():
    """Home page route"""
    return render_template("login.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    if request.method == "POST":
        user_message = request.form.get("message")

        if user_message:
            reply = get_response(user_message)

            cursor.execute(
                "INSERT INTO chats (user_id, message, response) VALUES (?, ?, ?)",
                (user_id, user_message, reply)
            )
            conn.commit()

    cursor.execute(
        "SELECT message, response FROM chats WHERE user_id=?",
        (user_id,)
    )
    chat_data = cursor.fetchall()

    chat_history = []
    for msg, res in chat_data:
        chat_history.append({'sender': 'You', 'message': msg})
        chat_history.append({'sender': 'Bot', 'message': res})

    return render_template("chat.html", chat_history=chat_history)

@app.route('/start')
def start():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template("home.html")



@app.route("/clear_history", methods=["POST"])
def clear_history():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor.execute(
        "DELETE FROM chats WHERE user_id=?",
        (user_id,)
    )
    conn.commit()

    return redirect('/chat')

    
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )

        conn.commit()

        return redirect('/')

    return render_template('signup.html')




@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        if user:

            session['user_id'] = user[0]   # store user id
            session['user'] = user[1]      # optional (username)

            return redirect('/start')

        else:
            return "Invalid Email or Password"

    return render_template('login.html')

# logout here
@app.route('/logout')
def logout():
    session.pop('user',None)

    return redirect('/login')

if __name__ == "__main__":
    app.run(debug=True)