from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vocabulary_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Simple Models
class VocabularyWord(db.Model):
    __tablename__ = 'vocabulary_words'
    
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    definition = db.Column(db.Text, nullable=False)
    example_sentence = db.Column(db.Text)
    pronunciation = db.Column(db.String(100))
    part_of_speech = db.Column(db.String(50))
    difficulty_level = db.Column(db.String(20), default='medium')
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    times_practiced = db.Column(db.Integer, default=0)
    last_practiced = db.Column(db.DateTime)
    mastery_level = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<VocabularyWord {self.word}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'word': self.word,
            'definition': self.definition,
            'example_sentence': self.example_sentence,
            'pronunciation': self.pronunciation,
            'part_of_speech': self.part_of_speech,
            'difficulty_level': self.difficulty_level,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'times_practiced': self.times_practiced,
            'last_practiced': self.last_practiced.isoformat() if self.last_practiced else None,
            'mastery_level': self.mastery_level
        }

class PhrasalVerb(db.Model):
    __tablename__ = 'phrasal_verbs'
    
    id = db.Column(db.Integer, primary_key=True)
    phrasal_verb = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.Text, nullable=False)
    example_sentence = db.Column(db.Text)
    separable = db.Column(db.Boolean, default=False)
    difficulty_level = db.Column(db.String(20), default='medium')
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    times_practiced = db.Column(db.Integer, default=0)
    last_practiced = db.Column(db.DateTime)
    mastery_level = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<PhrasalVerb {self.phrasal_verb}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'phrasal_verb': self.phrasal_verb,
            'meaning': self.meaning,
            'example_sentence': self.example_sentence,
            'separable': self.separable,
            'difficulty_level': self.difficulty_level,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'times_practiced': self.times_practiced,
            'last_practiced': self.last_practiced.isoformat() if self.last_practiced else None,
            'mastery_level': self.mastery_level
        }

class Idiom(db.Model):
    __tablename__ = 'idioms'
    
    id = db.Column(db.Integer, primary_key=True)
    idiom = db.Column(db.String(200), nullable=False)
    meaning = db.Column(db.Text, nullable=False)
    example_sentence = db.Column(db.Text)
    origin = db.Column(db.Text)
    difficulty_level = db.Column(db.String(20), default='medium')
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    times_practiced = db.Column(db.Integer, default=0)
    last_practiced = db.Column(db.DateTime)
    mastery_level = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Idiom {self.idiom}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'idiom': self.idiom,
            'meaning': self.meaning,
            'example_sentence': self.example_sentence,
            'origin': self.origin,
            'difficulty_level': self.difficulty_level,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'times_practiced': self.times_practiced,
            'last_practiced': self.last_practiced.isoformat() if self.last_practiced else None,
            'mastery_level': self.mastery_level
        }

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # Get counts for dashboard
    vocab_count = VocabularyWord.query.count()
    phrasal_count = PhrasalVerb.query.count()
    idiom_count = Idiom.query.count()
    
    # Get recently added items
    recent_vocab = VocabularyWord.query.order_by(VocabularyWord.date_added.desc()).limit(5).all()
    recent_phrasal = PhrasalVerb.query.order_by(PhrasalVerb.date_added.desc()).limit(5).all()
    recent_idioms = Idiom.query.order_by(Idiom.date_added.desc()).limit(5).all()
    
    return render_template('index.html', 
                         vocab_count=vocab_count,
                         phrasal_count=phrasal_count,
                         idiom_count=idiom_count,
                         recent_vocab=recent_vocab,
                         recent_phrasal=recent_phrasal,
                         recent_idioms=recent_idioms)

# Vocabulary Routes
@app.route('/vocabulary')
def vocabulary_list():
    page = request.args.get('page', 1, type=int)
    words = VocabularyWord.query.order_by(VocabularyWord.date_added.desc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('vocabulary_list.html', words=words)

@app.route('/vocabulary/add', methods=['GET', 'POST'])
def add_vocabulary():
    if request.method == 'POST':
        word = VocabularyWord(
            word=request.form['word'],
            definition=request.form['definition'],
            example_sentence=request.form.get('example_sentence', ''),
            pronunciation=request.form.get('pronunciation', ''),
            part_of_speech=request.form.get('part_of_speech', ''),
            difficulty_level=request.form.get('difficulty_level', 'medium')
        )
        db.session.add(word)
        db.session.commit()
        flash(f'Vocabulary word "{word.word}" added successfully!', 'success')
        return redirect(url_for('vocabulary_list'))
    return render_template('add_vocabulary.html')

@app.route('/vocabulary/<int:id>/edit', methods=['GET', 'POST'])
def edit_vocabulary(id):
    word = VocabularyWord.query.get_or_404(id)
    if request.method == 'POST':
        word.word = request.form['word']
        word.definition = request.form['definition']
        word.example_sentence = request.form.get('example_sentence', '')
        word.pronunciation = request.form.get('pronunciation', '')
        word.part_of_speech = request.form.get('part_of_speech', '')
        word.difficulty_level = request.form.get('difficulty_level', 'medium')
        db.session.commit()
        flash(f'Vocabulary word "{word.word}" updated successfully!', 'success')
        return redirect(url_for('vocabulary_list'))
    return render_template('edit_vocabulary.html', word=word)

@app.route('/vocabulary/<int:id>/delete', methods=['POST'])
def delete_vocabulary(id):
    word = VocabularyWord.query.get_or_404(id)
    word_name = word.word
    db.session.delete(word)
    db.session.commit()
    flash(f'Vocabulary word "{word_name}" deleted successfully!', 'success')
    return redirect(url_for('vocabulary_list'))

# Phrasal Verb Routes
@app.route('/phrasal-verbs')
def phrasal_verbs_list():
    page = request.args.get('page', 1, type=int)
    phrasal_verbs = PhrasalVerb.query.order_by(PhrasalVerb.date_added.desc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('phrasal_verbs_list.html', phrasal_verbs=phrasal_verbs)

@app.route('/phrasal-verbs/add', methods=['GET', 'POST'])
def add_phrasal_verb():
    if request.method == 'POST':
        phrasal_verb = PhrasalVerb(
            phrasal_verb=request.form['phrasal_verb'],
            meaning=request.form['meaning'],
            example_sentence=request.form.get('example_sentence', ''),
            separable=bool(request.form.get('separable')),
            difficulty_level=request.form.get('difficulty_level', 'medium')
        )
        db.session.add(phrasal_verb)
        db.session.commit()
        flash(f'Phrasal verb "{phrasal_verb.phrasal_verb}" added successfully!', 'success')
        return redirect(url_for('phrasal_verbs_list'))
    return render_template('add_phrasal_verb.html')

@app.route('/phrasal-verbs/<int:id>/edit', methods=['GET', 'POST'])
def edit_phrasal_verb(id):
    phrasal_verb = PhrasalVerb.query.get_or_404(id)
    if request.method == 'POST':
        phrasal_verb.phrasal_verb = request.form['phrasal_verb']
        phrasal_verb.meaning = request.form['meaning']
        phrasal_verb.example_sentence = request.form.get('example_sentence', '')
        phrasal_verb.separable = bool(request.form.get('separable'))
        phrasal_verb.difficulty_level = request.form.get('difficulty_level', 'medium')
        db.session.commit()
        flash(f'Phrasal verb "{phrasal_verb.phrasal_verb}" updated successfully!', 'success')
        return redirect(url_for('phrasal_verbs_list'))
    return render_template('edit_phrasal_verb.html', phrasal_verb=phrasal_verb)

@app.route('/phrasal-verbs/<int:id>/delete', methods=['POST'])
def delete_phrasal_verb(id):
    phrasal_verb = PhrasalVerb.query.get_or_404(id)
    phrasal_verb_name = phrasal_verb.phrasal_verb
    db.session.delete(phrasal_verb)
    db.session.commit()
    flash(f'Phrasal verb "{phrasal_verb_name}" deleted successfully!', 'success')
    return redirect(url_for('phrasal_verbs_list'))

# Idiom Routes
@app.route('/idioms')
def idioms_list():
    page = request.args.get('page', 1, type=int)
    idioms = Idiom.query.order_by(Idiom.date_added.desc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('idioms_list.html', idioms=idioms)

@app.route('/idioms/add', methods=['GET', 'POST'])
def add_idiom():
    if request.method == 'POST':
        idiom = Idiom(
            idiom=request.form['idiom'],
            meaning=request.form['meaning'],
            example_sentence=request.form.get('example_sentence', ''),
            origin=request.form.get('origin', ''),
            difficulty_level=request.form.get('difficulty_level', 'medium')
        )
        db.session.add(idiom)
        db.session.commit()
        flash(f'Idiom "{idiom.idiom}" added successfully!', 'success')
        return redirect(url_for('idioms_list'))
    return render_template('add_idiom.html')

@app.route('/idioms/<int:id>/edit', methods=['GET', 'POST'])
def edit_idiom(id):
    idiom = Idiom.query.get_or_404(id)
    if request.method == 'POST':
        idiom.idiom = request.form['idiom']
        idiom.meaning = request.form['meaning']
        idiom.example_sentence = request.form.get('example_sentence', '')
        idiom.origin = request.form.get('origin', '')
        idiom.difficulty_level = request.form.get('difficulty_level', 'medium')
        db.session.commit()
        flash(f'Idiom "{idiom.idiom}" updated successfully!', 'success')
        return redirect(url_for('idioms_list'))
    return render_template('edit_idiom.html', idiom=idiom)

@app.route('/idioms/<int:id>/delete', methods=['POST'])
def delete_idiom(id):
    idiom = Idiom.query.get_or_404(id)
    idiom_name = idiom.idiom
    db.session.delete(idiom)
    db.session.commit()
    flash(f'Idiom "{idiom_name}" deleted successfully!', 'success')
    return redirect(url_for('idioms_list'))

# Flashcard Routes
@app.route('/flashcards')
def flashcards_menu():
    return render_template('flashcards_menu.html')

@app.route('/flashcards/<category>')
def flashcards(category):
    if category == 'vocabulary':
        items = VocabularyWord.query.all()
        template = 'flashcards_vocabulary.html'
    elif category == 'phrasal-verbs':
        items = PhrasalVerb.query.all()
        template = 'flashcards_phrasal.html'
    elif category == 'idioms':
        items = Idiom.query.all()
        template = 'flashcards_idioms.html'
    else:
        flash('Invalid flashcard category!', 'error')
        return redirect(url_for('index'))
    
    return render_template(template, items=items, category=category)

@app.route('/api/flashcards/<category>')
def api_flashcards(category):
    if category == 'vocabulary':
        items = VocabularyWord.query.all()
    elif category == 'phrasal-verbs':
        items = PhrasalVerb.query.all()
    elif category == 'idioms':
        items = Idiom.query.all()
    else:
        return jsonify({'error': 'Invalid category'}), 400
    
    random.shuffle(items)
    return jsonify([item.to_dict() for item in items])

# Search Route
@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return render_template('search_results.html', query='', results={})
    
    # Search vocabulary
    vocab_results = VocabularyWord.query.filter(
        VocabularyWord.word.contains(query) | 
        VocabularyWord.definition.contains(query)
    ).all()
    
    # Search phrasal verbs
    phrasal_results = PhrasalVerb.query.filter(
        PhrasalVerb.phrasal_verb.contains(query) | 
        PhrasalVerb.meaning.contains(query)
    ).all()
    
    # Search idioms
    idiom_results = Idiom.query.filter(
        Idiom.idiom.contains(query) | 
        Idiom.meaning.contains(query)
    ).all()
    
    results = {
        'vocabulary': vocab_results,
        'phrasal_verbs': phrasal_results,
        'idioms': idiom_results
    }
    
    return render_template('search_results.html', query=query, results=results)

if __name__ == '__main__':
    # Try different ports if default is busy, but only on first run
    import os
    import socket
    
    # Check if this is the reloader process
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        def find_free_port():
            ports = [5001, 5002, 5003, 5004, 5005]
            for port in ports:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.bind(('127.0.0.1', port))
                        return port
                    except OSError:
                        continue
            return 5000  # fallback
        
        port = find_free_port()
        print(f"🚀 Starting Mastery English on http://127.0.0.1:{port}")
        os.environ['FLASK_PORT'] = str(port)
    else:
        port = int(os.environ.get('FLASK_PORT', 5001))
    
    app.run(debug=True, port=port)
