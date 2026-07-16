import os
import io
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pickle
import re
import nltk
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import requests
from bs4 import BeautifulSoup
import numpy as np
import traceback
# pyrefly: ignore [missing-import]
import PyPDF2
# pyrefly: ignore [missing-import]
import docx

# Ensure stopwords and vader_lexicon are downloaded locally
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
    
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

stop_words = set(stopwords.words("english"))
sia = SentimentIntensityAnalyzer()

app = Flask(__name__)

# Database Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'history.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class ScanHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_snippet = db.Column(db.Text, nullable=False)
    source_type = db.Column(db.String(50), nullable=False) # 'text', 'url', 'file'
    prediction = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    sentiment = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# Load Models
MODEL_PATH = os.path.join(BASE_DIR, 'fake_news_model.pkl')
VECTORIZER_PATH = os.path.join(BASE_DIR, 'tfidf_vectorizer.pkl')

try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(VECTORIZER_PATH, 'rb') as f:
        vectorizer = pickle.load(f)
    model_loaded = True
    print(f"[DEBUG] Loaded model and vectorizer.")
except Exception as e:
    print(f"[ERROR] Could not load the model files. Error: {e}")
    model_loaded = False

def clean_text(text):
    if not isinstance(text, str):
        text = str(text)
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'[^a-zA-Z]', ' ', text)
    words = text.split()
    words = [word for word in words if word not in stop_words]
    return " ".join(words)

def extract_text_from_pdf(file_stream):
    try:
        reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"[ERROR] PDF extraction failed: {e}")
        return ""

def extract_text_from_docx(file_stream):
    try:
        doc = docx.Document(file_stream)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"[ERROR] DOCX extraction failed: {e}")
        return ""

def scrape_article(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text() for p in paragraphs])
        if not text.strip():
            text = soup.get_text(separator=' ')
        return text
    except Exception as e:
        print(f"[ERROR] Scraping URL failed: {e}")
        return ""

def get_sentiment_label(text):
    scores = sia.polarity_scores(text)
    compound = scores['compound']
    if compound >= 0.05:
        return "Positive", scores
    elif compound <= -0.05:
        return "Negative", scores
    else:
        return "Neutral", scores

def fake_news_prediction(news_text):
    if not model_loaded:
        return ("Error: Model missing", 0.0, [], "Unknown", {})
    
    try:
        cleaned_text = clean_text(news_text)
        vectorized_input_data = vectorizer.transform([cleaned_text])
        prediction = model.predict(vectorized_input_data)
        predicted_class_id = prediction[0]
        probabilities = model.predict_proba(vectorized_input_data)
        confidence = np.max(probabilities[0]) * 100
        
        positive_class_label = model.classes_[1] if len(model.classes_) > 1 else 1
        negative_class_label = model.classes_[0]
        
        if predicted_class_id == negative_class_label:
            predicted_class = "Fake News"
        elif predicted_class_id == positive_class_label:
            predicted_class = "Real News"
        else:
            predicted_class = "Unknown"
            
        # Explainable AI (XAI) Logic
        top_words = []
        try:
            feature_names = vectorizer.get_feature_names_out()
            coefs = model.coef_[0]
            non_zero_indices = vectorized_input_data.nonzero()[1]
            word_contributions = []
            for idx in non_zero_indices:
                word = feature_names[idx]
                weight = coefs[idx]
                word_contributions.append((word, weight))
            word_contributions.sort(key=lambda x: abs(x[1]), reverse=True)
            top_words_raw = word_contributions[:15]
            for word, weight in top_words_raw:
                impact_type = "real" if weight > 0 else "fake"
                top_words.append({
                    "word": word, 
                    "impact": impact_type, 
                    "weight": float(abs(weight))
                })
        except Exception as e:
            print(f"[ERROR] Extracting word contributions failed: {e}")
            
        sentiment_label, sentiment_scores = get_sentiment_label(news_text)
            
        return predicted_class, confidence, top_words, sentiment_label, sentiment_scores
        
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        traceback.print_exc()
        return ("Error in prediction", 0.0, [], "Unknown", {})

@app.route('/', methods=['GET', 'POST'])
def home():
    prediction_result = None
    confidence_score = None
    news_text = ""
    url_input = ""
    top_words = []
    sentiment_label = None
    sentiment_scores = None
    active_tab = "text"
    
    if request.method == 'POST':
        active_tab = request.form.get('active_tab', 'text')
        content_to_analyze = ""
        source_type = active_tab
        
        if active_tab == 'url':
            url_input = request.form.get('url', '')
            if url_input.strip():
                content_to_analyze = scrape_article(url_input)
                news_text = content_to_analyze 
        elif active_tab == 'file':
            if 'file' in request.files:
                uploaded_file = request.files['file']
                if uploaded_file.filename != '':
                    if uploaded_file.filename.endswith('.pdf'):
                        content_to_analyze = extract_text_from_pdf(uploaded_file)
                    elif uploaded_file.filename.endswith('.docx'):
                        content_to_analyze = extract_text_from_docx(uploaded_file)
                    else:
                        content_to_analyze = uploaded_file.read().decode('utf-8', errors='ignore')
                    news_text = content_to_analyze
        else:
            news_text = request.form.get('news', '')
            content_to_analyze = news_text
            
        if content_to_analyze.strip():
            prediction_result, confidence, top_words_formatted, sent_label, sent_scores = fake_news_prediction(content_to_analyze)
            if prediction_result and not prediction_result.startswith("Error"):
                confidence_score = f"{confidence:.2f}"
                top_words = top_words_formatted
                sentiment_label = sent_label
                sentiment_scores = sent_scores
                
                # Save to database
                snippet = content_to_analyze[:200] + "..." if len(content_to_analyze) > 200 else content_to_analyze
                new_scan = ScanHistory(
                    content_snippet=snippet,
                    source_type=source_type,
                    prediction=prediction_result,
                    confidence=confidence,
                    sentiment=sentiment_label
                )
                db.session.add(new_scan)
                db.session.commit()
            
    return render_template('index.html', 
                           prediction=prediction_result, 
                           confidence=confidence_score, 
                           news_text=news_text,
                           url_input=url_input,
                           top_words=top_words,
                           sentiment_label=sentiment_label,
                           sentiment_scores=sentiment_scores,
                           active_tab=active_tab)

@app.route('/history')
def history():
    scans = ScanHistory.query.order_by(ScanHistory.timestamp.desc()).limit(50).all()
    return render_template('history.html', scans=scans)

@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
        
    text = data.get('text', '')
    url = data.get('url', '')
    
    if url:
        text = scrape_article(url)
        
    if not text.strip():
        return jsonify({"error": "No text or valid URL provided"}), 400
        
    prediction, confidence, top_words, sent_label, sent_scores = fake_news_prediction(text)
    
    if prediction.startswith("Error"):
        return jsonify({"error": prediction}), 500
        
    # Log to DB
    snippet = text[:200] + "..." if len(text) > 200 else text
    new_scan = ScanHistory(
        content_snippet=snippet,
        source_type='api',
        prediction=prediction,
        confidence=confidence,
        sentiment=sent_label
    )
    db.session.add(new_scan)
    db.session.commit()
        
    return jsonify({
        "prediction": prediction,
        "confidence": float(confidence),
        "sentiment": sent_label,
        "sentiment_scores": sent_scores,
        "top_words": top_words
    })

if __name__ == '__main__':
    app.run(debug=True)
