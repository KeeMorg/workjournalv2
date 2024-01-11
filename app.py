from flask import Flask, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import datetime
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Entry {self.id}>'

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        timestamp = datetime.datetime.now().strftime("%b. %d, %Y, %I:%M %p")
        new_entry = Entry(title=title, content=content, timestamp=timestamp)
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('home'))
    
    entries = Entry.query.order_by(Entry.id.desc()).all()
    return render_template('index.html', entries=entries)

@app.route('/entry/<int:entry_id>')
def show_entry(entry_id):
    entry = Entry.query.get_or_404(entry_id)
    return render_template('entry.html', entry=entry)

@app.route('/export', methods=['POST'])
def export_entries():
    entries = Entry.query.all()  # Fetch all entries from the database

    # Create a PDF
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    for entry in entries:
        title = entry.title
        content = entry.content
        timestamp = entry.timestamp

        # Create a Paragraph for the entry and add it to elements
        entry_text = f"<b>Title:</b> {title}<br/><b>Date:</b> {timestamp}<br/><b>Content:</b> {content}"
        p = Paragraph(entry_text, styles['Normal'])
        elements.append(p)

        # Add space between entries
        elements.append(Spacer(1, 12))

    # Build the PDF document
    pdf.build(elements)

    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    # Send the PDF as a response
    response = Response(pdf_bytes, content_type='application/pdf')
    
    # Set headers to indicate download
    response.headers['Content-Disposition'] = 'attachment; filename=journal_entries.pdf'

    return response

if __name__ == "__main__":
    app.run(debug=True)
