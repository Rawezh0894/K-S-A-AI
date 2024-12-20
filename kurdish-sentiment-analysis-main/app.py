from flask import Flask, jsonify, render_template, request, send_file
import tempfile
import os
import pandas as pd
import joblib
import re

app = Flask(__name__)

# Load the Naive Bayes model
with open('static/model/nb_classifier.pkl', 'rb') as model_file:
    model = joblib.load(model_file)

# Load the vectorizer
with open('static/model/tfidf_vectorizer.pkl', 'rb') as vectorizer_file:
    vectorizer = joblib.load(vectorizer_file)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

# Function to remove specific suffixes from each word in the text
def remove_suffixes(text):
    suffixes = ['ی', 'یان', 'م', 'مان', 'ت', 'تا']
    words = text.split()
    cleaned_words = []
    for word in words:
        for suffix in suffixes:
            if word.endswith(suffix):
                word = word[: -len(suffix)]
                break
        cleaned_words.append(word)
    return ' '.join(cleaned_words)

@app.route('/')
def my_form():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    text = request.form['text']
    
    if not text:
        return jsonify({'variable': 'تکایە ڕستەیەک بنووسە'})
    
    # Preprocess text to remove suffixes
    cleaned_text = remove_suffixes(text)
    
    # Transform the input using the vectorizer
    transformed_text = vectorizer.transform([cleaned_text])
    
    predicted_label = model.predict(transformed_text)[0]

    # Determine the label based on the prediction
    if predicted_label == 'positive':
        label = 'ئەم ڕستە ئەرێنییە✔️'
    elif predicted_label == 'neutral':
        label = 'ئەم ڕستە بێلایەنە🤷'
    elif predicted_label == 'negative':
        label = 'ئەم ڕستەیە نەرێنییە❌'

    return jsonify({'variable': label})

@app.route('/downloads/<filename>')
def download_file(filename):
    file_path = os.path.join(tempfile.gettempdir(), filename)
    
    # Check if the file exists
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found"

@app.route('/predict_file', methods=['POST'])
def predict_file():
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'result': 'تکایە فایلێکی ئیگزڵ هەڵبژێرە (xlsx, xls)'})

    _, temp_path = tempfile.mkstemp()
    file.save(temp_path)

    df = pd.read_excel(temp_path)
    text_column = request.form['column']

    if text_column not in df.columns:
        return jsonify({'result': 'ناوی کۆڵۆمەکە هەڵەیە'})

    analyzed_sentences = []
    for index, row in df.iterrows():
        sentence = row[text_column]
        
        # Preprocess sentence to remove suffixes
        cleaned_sentence = remove_suffixes(sentence)
        
        # Transform the input using the vectorizer
        transformed_sentence = vectorizer.transform([cleaned_sentence])
        
        predicted_label = model.predict(transformed_sentence)[0]

        # Determine the label based on the prediction
        if predicted_label == 'positive':
            label = 'Positive'
        elif predicted_label == 'neutral':
            label = 'Neutral'
        elif predicted_label == 'negative':
            label = 'Negative'

        analyzed_sentences.append([sentence, label])

    df['Sentiment'] = [label for _, label in analyzed_sentences]

    result_file_path = os.path.join(tempfile.gettempdir(), 'analyzed_file.xlsx')
    df.to_excel(result_file_path, index=False)

    return jsonify({
        'table': df.to_html(classes='table table-bordered', index=False),
        'download_link': '/downloads/analyzed_file.xlsx'
    })

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
