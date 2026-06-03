from flask import Flask, render_template, request, send_file
from textblob import TextBlob
import sqlite3
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

# Ensure database folder exists
os.makedirs("database", exist_ok=True)

# Create database table
def init_db():
    conn = sqlite3.connect('database/mental_health.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mood TEXT,
            journal TEXT,
            sentiment REAL,
            sentiment_label TEXT,
            suggestion TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    mood = request.form['mood']
    journal = request.form['journal']

    # Sentiment Analysis
    analysis = TextBlob(journal)
    sentiment_score = analysis.sentiment.polarity

    # Emotion Detection + Suggestion
    if sentiment_score > 0:
        sentiment_label = "Positive 😊"
        suggestion = "Keep up the positive mindset and continue your good habits."
    elif sentiment_score < 0:
        sentiment_label = "Negative 😔"
        suggestion = "Take a short break, talk to a friend, and get some rest."
    else:
        sentiment_label = "Neutral 😐"
        suggestion = "Try some physical activity or journaling to boost your mood."

    # Save to database
    conn = sqlite3.connect('database/mental_health.db')
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO entries
        (mood, journal, sentiment, sentiment_label, suggestion)
        VALUES (?, ?, ?, ?, ?)
        """,
        (mood, journal, sentiment_score, sentiment_label, suggestion)
    )

    conn.commit()
    conn.close()

    return f"""
    <html>
    <head><title>Result</title></head>
    <body>
        <h2>Entry Saved Successfully!</h2>
        <p><b>Mood:</b> {mood}</p>
        <p><b>Sentiment Score:</b> {sentiment_score:.2f}</p>
        <p><b>Detected Emotion:</b> {sentiment_label}</p>
        <p><b>Wellness Suggestion:</b> {suggestion}</p>
        <br>
        <a href="/">Go Back</a>
        <br><br>
        <a href="/dashboard">View Dashboard</a>
    </body>
    </html>
    """


@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('database/mental_health.db')
    cursor = conn.cursor()

    cursor.execute("SELECT mood, journal, sentiment_label, suggestion FROM entries ORDER BY id DESC")
    entries = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM entries")
    total_entries = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entries WHERE sentiment_label LIKE 'Positive%'")
    positive_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entries WHERE sentiment_label LIKE 'Negative%'")
    negative_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entries WHERE sentiment_label LIKE 'Neutral%'")
    neutral_count = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'dashboard.html',
        entries=entries,
        total_entries=total_entries,
        positive_count=positive_count,
        negative_count=negative_count,
        neutral_count=neutral_count
    )


@app.route('/download-report')
def download_report():
    conn = sqlite3.connect('database/mental_health.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM entries")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entries WHERE sentiment_label LIKE 'Positive%'")
    positive = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entries WHERE sentiment_label LIKE 'Negative%'")
    negative = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entries WHERE sentiment_label LIKE 'Neutral%'")
    neutral = cursor.fetchone()[0]

    conn.close()

    pdf_file = "mental_health_report.pdf"
    doc = SimpleDocTemplate(pdf_file)
    styles = getSampleStyleSheet()

    content = [
        Paragraph("Student Mental Health Report", styles['Title']),
        Paragraph(f"Total Entries: {total}", styles['Normal']),
        Paragraph(f"Positive Entries: {positive}", styles['Normal']),
        Paragraph(f"Negative Entries: {negative}", styles['Normal']),
        Paragraph(f"Neutral Entries: {neutral}", styles['Normal']),
    ]

    doc.build(content)

    return send_file(pdf_file, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
