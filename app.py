from flask import Flask, request, jsonify, render_template
from datetime import datetime
from openai import OpenAI
import os, json
import spacy
from spacy.matcher import PhraseMatcher
import sqlite3
from datetime import datetime

# Load English NLP model
nlp = spacy.load("en_core_web_sm")
symptom_concepts = [
    "headache", "my head hurts", "pain in my head",
    "fever", "i feel hot", "my temperature is high",
    "cough", "can’t stop coughing", "i’m coughing a lot",
    "fatigue", "feeling tired", "i’m exhausted", "low energy",
    "nausea", "i feel like throwing up", "queasy",
    "vomiting", "throwing up", "i just puked",
    "diarrhea", "loose stools", "frequent bathroom trips",
    "constipation", "can’t poop", "irregular bowel movement",
    "stomach ache", "my stomach hurts", "abdominal pain",
    "chest pain", "tightness in chest", "pressure in chest",
    "sore throat", "throat hurts", "pain while swallowing",
    "runny nose", "nose is running", "dripping nose",
    "shortness of breath", "can’t breathe", "breathing trouble",
    "dizziness", "feeling lightheaded", "i’m dizzy",
    "rash", "skin redness", "spots on skin", "itchy skin",
    "itching", "i’m itchy", "itchy all over",
    "swelling", "something is swollen", "puffy area",
    "blurred vision", "vision is blurry", "can’t see clearly",
    "numbness", "no feeling", "numb sensation",
    "tingling", "pins and needles", "tingly",
    "palpitations", "heart is racing", "irregular heartbeat",
    "insomnia", "can’t sleep", "trouble sleeping",
    "bruising", "easily bruised", "purple mark",
    "muscle pain", "my muscles hurt", "sore muscles",
    "joint pain", "pain in my joints", "aching joints",
    "loss of smell", "can’t smell anything", "no sense of smell",
    "loss of taste", "can’t taste food", "taste is gone",
    "back pain", "lower back pain", "hurting back",
    "toothache", "my tooth hurts", "pain in tooth",
    "earache", "pain in ear", "my ear hurts",
    "dry mouth", "mouth feels dry", "not enough saliva",
    "burning sensation", "feels like burning", "hot feeling"
]

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp(concept) for concept in symptom_concepts]
matcher.add("SYMPTOMS", patterns)

app = Flask(__name__)

# Set your OpenAI API key (you can also export it as an env variable)
import os
openai_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_key)

# Initialize OpenAI client
client = OpenAI()

# System prompt for GPT model
system_prompt = """
You are SympAI, an AI health assistant created by EvolvAI Nexus. You only help users with health symptom-related questions.
You do NOT answer non-health questions. You do NOT provide diagnoses, medical treatment, or emergency advice.
If a user asks anything unrelated to health symptoms, politely decline and redirect them.
Always remind users to consult a licensed healthcare provider for any serious concerns.
"""

# Keywords to detect symptom-related messages
symptom_concepts = [
    "headache", "fever", "cough", "fatigue", "nausea", "pain", "dizziness",
    "rash", "infection", "sore throat", "chest pain", "cold", "flu", "allergy",
    "diarrhea", "constipation", "runny nose", "shortness of breath", "itching",
    "burning", "swelling", "cramps", "palpitations", "back pain", "joint pain",
    "urinary problems", "stomach ache", "heartburn", "tingling", "numbness",
    "blurred vision", "loss of smell", "weight loss", "insomnia", "bruising"
]


def is_health_related(user_input):
    doc = nlp(user_input)
    matches = matcher(doc)
    return len(matches) > 0


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message', '').strip()

    if not user_input:
        return jsonify({'response': "Please enter a valid message."})

    if not is_health_related(user_input):
        return jsonify({
            'response': "I'm here to help with health symptoms only. Please describe any symptoms you're experiencing."
        })

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )

        response_text = completion.choices[0].message.content

        # Save chat to DB
        conn = sqlite3.connect("sympai.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_history (timestamp, user_message, sympai_response)
            VALUES (?, ?, ?)
        """, (datetime.now().isoformat(), user_input, response_text))
        chat_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({'response': response_text, 'chat_id': chat_id})

    except Exception as e:
        return jsonify({'response': f"An error occurred: {str(e)}"})

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    feedback_value = data.get("feedback")
    chat_id = data.get("chat_id")

    conn = sqlite3.connect("sympai.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (chat_id, feedback, timestamp)
        VALUES (?, ?, ?)
    """, (chat_id, feedback_value, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

if __name__ == "__main__":
    import os
    os.environ["FLASK_ENV"] = "production"  # force production mode
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)