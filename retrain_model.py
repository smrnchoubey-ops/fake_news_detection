import os
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import pickle

# Ensure stopwords
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

stop_words = set(stopwords.words("english"))

def clean_text(text):
    """
    Identical preprocessing function used in Flask prediction.
    """
    if not isinstance(text, str):
        text = str(text)
    text = text.lower()
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Replace all non-alphabetic characters with space to prevent concatenating words
    text = re.sub(r'[^a-zA-Z]', ' ', text)
    words = text.split()
    # Remove stopwords
    words = [word for word in words if word not in stop_words]
    return " ".join(words)

def remove_publisher_bias(text):
    """
    Removes the publisher prefixes found mostly in the True.csv dataset.
    Example: 'WASHINGTON (Reuters) - The White house...'
    Pattern: ^.*?\(Reuters\) - 
    """
    if not isinstance(text, str):
        return text
    # The dataset often has City (Publisher) - Text
    # Let's remove anything before and including " - " if it contains "(Reuters)" or similar
    text = re.sub(r'^.*?\(.*?\) - ', '', text)
    return text

def main():
    print("Loading data...")
    fake_df = pd.read_csv('Fake.csv')
    true_df = pd.read_csv('True.csv')
    
    # Assign labels based on original setup: 0 = Fake, 1 = Real
    fake_df['label'] = 0
    true_df['label'] = 1
    
    print("Removing dataset biases (publisher tags)...")
    # Clean the text specifically of the massive Reuters bias
    true_df['text'] = true_df['text'].apply(remove_publisher_bias)
    fake_df['text'] = fake_df['text'].apply(remove_publisher_bias)
    
    # Combine datasets
    df = pd.concat([fake_df, true_df], ignore_index=True)
    
    # Create the final feature by combining title and text
    print("Combining title and text...")
    df['full_text'] = df['title'] + " " + df['text']
    
    print("Applying main text preprocessing (this will take a few minutes)...")
    df['clean_full_text'] = df['full_text'].apply(clean_text)
    
    X = df['clean_full_text']
    y = df['label']
    
    print("Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Fitting TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer(max_features=5000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    print("Training Logistic Regression Model...")
    model = LogisticRegression()
    model.fit(X_train_vec, y_train)
    
    # Evaluate
    print("Evaluating Model...")
    y_train_pred = model.predict(X_train_vec)
    y_test_pred = model.predict(X_test_vec)
    
    print(f"Training Accuracy: {accuracy_score(y_train, y_train_pred):.4f}")
    print(f"Testing Accuracy: {accuracy_score(y_test, y_test_pred):.4f}")
    print("\nClassification Report (Testing):")
    print(classification_report(y_test, y_test_pred))
    
    print("Checking 'reuters' weight to ensure bias is eliminated...")
    if 'reuters' in vectorizer.vocabulary_:
        idx = vectorizer.vocabulary_['reuters']
        weight = model.coef_[0][idx]
        print(f"Weight for 'reuters': {weight:.4f}")
    else:
        print("'reuters' not found in vocabulary! Bias successfully eliminated.")
    
    # Save the new models
    print("Saving models to .pkl files...")
    with open('fake_news_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('tfidf_vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
        
    print("Done! Retraining successful.")

if __name__ == '__main__':
    main()
