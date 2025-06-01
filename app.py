from flask import Flask, request, jsonify, render_template
from datetime import datetime
from openai import OpenAI
import os, json
import spacy
from spacy.matcher import PhraseMatcher
import sqlite3

# Load English NLP model
nlp = spacy.load("en_core_web_sm")
symptom_concepts = [
    # General
    "pain", "ache", "discomfort",

    # Head and face
    "headache", "migraine", "my head hurts", "pain in my head",
    "toothache", "my tooth hurts", "pain in tooth",
    "earache", "ear pain", "my ear hurts",
    "blurred vision", "vision is blurry", "can’t see clearly",
    "loss of smell", "can’t smell anything",
    "loss of taste", "can’t taste food",

    # Neck, back, and torso
    "neck pain", "pain in neck", "sore neck",
    "back pain", "lower back pain", "hurting back",
    "stomach ache", "abdominal pain", "belly pain",
    "chest pain", "tightness in chest", "pressure in chest",

    # Limbs
    "leg pain", "pain in legs", "hurting legs", "sore legs",
    "arm pain", "pain in arms", "sore arm", "pain in shoulder",
    "knee pain", "ankle pain", "foot pain", "heel pain",
    "hand pain", "wrist pain", "elbow pain", "finger pain",

    # Respiratory and GI
    "cough", "can’t stop coughing", "i’m coughing a lot",
    "sore throat", "throat hurts", "pain while swallowing",
    "runny nose", "stuffy nose", "dripping nose",
    "shortness of breath", "can’t breathe", "trouble breathing",
    "fever", "temperature is high", "i feel hot",
    "nausea", "i feel like throwing up", "queasy",
    "vomiting", "throwing up", "puked",
    "diarrhea", "loose stools", "frequent bathroom trips",
    "constipation", "can’t poop", "irregular bowel movement",
    "heartburn", "acid reflux",

    # Skin
    "rash", "skin redness", "spots on skin",
    "itchy skin", "itching", "i’m itchy",
    "swelling", "something is swollen", "puffy area",
    "bruising", "easily bruised", "purple mark",

    # Neurological and others
    "fatigue", "feeling tired", "exhausted",
    "dizziness", "feeling lightheaded", "i’m dizzy",
    "numbness", "numb sensation", "no feeling",
    "tingling", "pins and needles", "tingly",
    "palpitations", "heart is racing", "irregular heartbeat",
    "insomnia", "can’t sleep", "trouble sleeping",
    "muscle pain", "my muscles hurt", "sore muscles",
    "joint pain", "pain in joints", "aching joints",
    "burning sensation", "feels like burning", "hot feeling",
    "dry mouth", "mouth feels dry"
]

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp(concept) for concept in symptom_concepts]
matcher.add("SYMPTOMS", patterns)

app = Flask(__name__)

openai_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_key)

system_prompt = """
You are SympAI, an AI health assistant created by EvolvAI Nexus.
Your tone should be warm, supportive, and conversational, like a helpful friend with health knowledge.

Your role is to help users describe their symptoms and guide them with general information or suggestions. 
You should NOT give a diagnosis, prescribe treatments, or answer emergency questions.

If a user asks about anything unrelated to health symptoms, kindly let them know you are here to assist only with symptom-related concerns.

Encourage users to consult a licensed healthcare provider for any serious or ongoing issues.
"""

conversation_history = []
MAX_CONTEXT_MESSAGES = 8

def is_health_related(text):
    doc = nlp(text)
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

    recent_msgs = [m['content'] for m in conversation_history[-MAX_CONTEXT_MESSAGES:] if m['role'] == 'user']
    context_string = " ".join(recent_msgs + [user_input])
    is_symptom = is_health_related(context_string)

    conversation_history.append({"role": "user", "content": user_input})

    if not is_symptom:
        reply = "I'm here to help with health symptoms only. Please describe any symptoms you're experiencing."
        conversation_history.append({"role": "assistant", "content": reply})
        return jsonify({'response': reply})

    try:
        messages = [{"role": "system", "content": system_prompt}] + conversation_history[-MAX_CONTEXT_MESSAGES:]

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )

        response_text = completion.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": response_text})

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
    os.environ["FLASK_ENV"] = "production"
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
