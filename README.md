# TruthLens: Advanced Fake News Detection System 🚀

TruthLens is a premium, interactive web application designed to classify news articles as Authentic or Fake using Machine Learning and Natural Language Processing (NLP).

## ✨ Features
- **Machine Learning Engine**: Trained on the ISOT dataset using Logistic Regression and TF-IDF Vectorization.
- **Explainable AI (XAI)**: Highlights the specific words in an article that influenced the model's decision, showing both Real (Green) and Fake (Red) word weights.
- **Sentiment Analysis**: Uses NLTK VADER to detect the emotional tone of the article (Positive, Negative, Neutral).
- **Multi-Source Input**: Analyze text directly, scrape text from a live URL, or upload PDF/DOCX files.
- **Premium UI/UX**: Features a highly interactive, glassmorphic design with a custom "Deep Scan" animation and dynamic circular score gauges.
- **Scan History**: Built-in SQLite database to track and log all previous scans.

## 🛠️ Tech Stack
- **Backend**: Python, Flask, SQLAlchemy
- **Machine Learning**: Scikit-Learn (Logistic Regression, TF-IDF), NLTK, NumPy
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism), JavaScript, Bootstrap 5, tsParticles (Galaxy Animation)
- **Utilities**: PyPDF2, python-docx, BeautifulSoup4

## 🚀 Quick Start (Local Setup)

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/fake-news-detection.git
cd fake-news-detection
```

2. **Create a virtual environment (Optional but Recommended)**
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Mac/Linux
source .venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the Application**
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`

## 🧠 Note on the ML Model
The included `fake_news_model.pkl` is trained primarily on US Political News datasets. For best results, test the model using political text. General science or sports news may be misclassified as "Fake" due to domain mismatch (a common ML concept!).

---
*Built with ❤️ for a safer, more truthful internet.*
