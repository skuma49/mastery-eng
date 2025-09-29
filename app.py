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
    
    # Convert items to dict for JSON serialization
    items_data = [item.to_dict() for item in items]
    random.shuffle(items_data)
    
    return render_template(template, items=items_data, category=category)

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

@app.route('/api/update-practice', methods=['POST'])
def update_practice():
    data = request.get_json()
    category = data.get('category')
    item_id = data.get('id')
    correct = data.get('correct')
    
    try:
        if category == 'vocabulary':
            item = VocabularyWord.query.get(item_id)
        elif category == 'phrasal-verbs':
            item = PhrasalVerb.query.get(item_id)
        elif category == 'idioms':
            item = Idiom.query.get(item_id)
        else:
            return jsonify({'error': 'Invalid category'}), 400
        
        if item:
            item.times_practiced = (item.times_practiced or 0) + 1
            item.last_practiced = datetime.utcnow()
            
            # Update mastery level based on correctness
            if correct:
                item.mastery_level = min((item.mastery_level or 0) + 1, 5)
            else:
                item.mastery_level = max((item.mastery_level or 0) - 1, 0)
            
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Item not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/check-vocabulary')
def check_vocabulary():
    """API endpoint to check if vocabulary word exists"""
    query = request.args.get('q', '').lower().strip()
    if not query:
        return jsonify([])
    
    results = []
    
    # Search for existing vocabulary words that match the query
    existing_words = VocabularyWord.query.filter(
        VocabularyWord.word.ilike(f'%{query}%')
    ).limit(8).all()
    
    for word in existing_words:
        results.append({
            'type': 'vocabulary',
            'text': word.word,
            'meaning': word.definition,
            'exact_match': word.word.lower() == query,
            'category': 'Vocabulary Word'
        })
    
    # Also check phrasal verbs and idioms for cross-category duplicates
    existing_phrasal = PhrasalVerb.query.filter(
        PhrasalVerb.phrasal_verb.ilike(f'%{query}%')
    ).limit(3).all()
    
    for verb in existing_phrasal:
        results.append({
            'type': 'phrasal_verb',
            'text': verb.phrasal_verb,
            'meaning': verb.meaning,
            'exact_match': verb.phrasal_verb.lower() == query,
            'category': 'Phrasal Verb',
            'separable': verb.separable
        })
    
    existing_idioms = Idiom.query.filter(
        Idiom.idiom.ilike(f'%{query}%')
    ).limit(3).all()
    
    for idiom in existing_idioms:
        results.append({
            'type': 'idiom',
            'text': idiom.idiom,
            'meaning': idiom.meaning,
            'exact_match': idiom.idiom.lower() == query,
            'category': 'Idiom'
        })
    
    # Sort by exact matches first, then by category priority (vocabulary first for vocab search)
    results.sort(key=lambda x: (not x['exact_match'], x['type'] != 'vocabulary', x['text'].lower()))
    
    return jsonify(results[:10])

@app.route('/api/check-phrasal-verb')
def check_phrasal_verb():
    """API endpoint to check if phrasal verb exists (includes cross-category check)"""
    query = request.args.get('q', '').lower().strip()
    if not query:
        return jsonify([])
    
    results = []
    
    # Search for existing phrasal verbs that match the query
    existing_verbs = PhrasalVerb.query.filter(
        PhrasalVerb.phrasal_verb.ilike(f'%{query}%')
    ).limit(8).all()
    
    for verb in existing_verbs:
        results.append({
            'type': 'phrasal_verb',
            'text': verb.phrasal_verb,
            'meaning': verb.meaning,
            'separable': verb.separable,
            'exact_match': verb.phrasal_verb.lower() == query,
            'category': 'Phrasal Verb'
        })
    
    # Also check vocabulary and idioms for cross-category duplicates
    existing_words = VocabularyWord.query.filter(
        VocabularyWord.word.ilike(f'%{query}%')
    ).limit(3).all()
    
    for word in existing_words:
        results.append({
            'type': 'vocabulary',
            'text': word.word,
            'meaning': word.definition,
            'exact_match': word.word.lower() == query,
            'category': 'Vocabulary Word'
        })
    
    existing_idioms = Idiom.query.filter(
        Idiom.idiom.ilike(f'%{query}%')
    ).limit(3).all()
    
    for idiom in existing_idioms:
        results.append({
            'type': 'idiom',
            'text': idiom.idiom,
            'meaning': idiom.meaning,
            'exact_match': idiom.idiom.lower() == query,
            'category': 'Idiom'
        })
    
    # Sort by exact matches first, then by category priority (phrasal verbs first for phrasal verb search)
    results.sort(key=lambda x: (not x['exact_match'], x['type'] != 'phrasal_verb', x['text'].lower()))
    
    return jsonify(results[:10])

@app.route('/api/check-idiom')
def check_idiom():
    """API endpoint to check if idiom exists (includes cross-category check)"""
    query = request.args.get('q', '').lower().strip()
    if not query:
        return jsonify([])
    
    results = []
    
    # Search for existing idioms that match the query
    existing_idioms = Idiom.query.filter(
        Idiom.idiom.ilike(f'%{query}%')
    ).limit(8).all()
    
    for idiom in existing_idioms:
        results.append({
            'type': 'idiom',
            'text': idiom.idiom,
            'meaning': idiom.meaning,
            'exact_match': idiom.idiom.lower() == query,
            'category': 'Idiom'
        })
    
    # Also check vocabulary and phrasal verbs for cross-category duplicates
    existing_words = VocabularyWord.query.filter(
        VocabularyWord.word.ilike(f'%{query}%')
    ).limit(3).all()
    
    for word in existing_words:
        results.append({
            'type': 'vocabulary',
            'text': word.word,
            'meaning': word.definition,
            'exact_match': word.word.lower() == query,
            'category': 'Vocabulary Word'
        })
    
    existing_verbs = PhrasalVerb.query.filter(
        PhrasalVerb.phrasal_verb.ilike(f'%{query}%')
    ).limit(3).all()
    
    for verb in existing_verbs:
        results.append({
            'type': 'phrasal_verb',
            'text': verb.phrasal_verb,
            'meaning': verb.meaning,
            'exact_match': verb.phrasal_verb.lower() == query,
            'category': 'Phrasal Verb',
            'separable': verb.separable
        })
    
    # Sort by exact matches first, then by category priority (idioms first for idiom search)
    results.sort(key=lambda x: (not x['exact_match'], x['type'] != 'idiom', x['text'].lower()))
    
    return jsonify(results[:10])



@app.route('/progress')
def progress():
    """Show mastery progress for all items"""
    # Get all items with their mastery levels
    vocabulary_items = VocabularyWord.query.all()
    phrasal_verbs = PhrasalVerb.query.all()
    idioms = Idiom.query.all()
    
    # Process vocabulary
    vocab_data = []
    for item in vocabulary_items:
        vocab_data.append({
            'word': item.word,
            'meaning': item.definition,
            'mastery_level': item.mastery_level or 0,
            'times_practiced': item.times_practiced or 0,
            'last_practiced': item.last_practiced,
            'id': item.id
        })
    
    # Process phrasal verbs
    phrasal_data = []
    for item in phrasal_verbs:
        phrasal_data.append({
            'word': item.phrasal_verb,
            'meaning': item.meaning,
            'separable': item.separable,
            'mastery_level': item.mastery_level or 0,
            'times_practiced': item.times_practiced or 0,
            'last_practiced': item.last_practiced,
            'id': item.id
        })
    
    # Process idioms
    idiom_data = []
    for item in idioms:
        idiom_data.append({
            'word': item.idiom,
            'meaning': item.meaning,
            'mastery_level': item.mastery_level or 0,
            'times_practiced': item.times_practiced or 0,
            'last_practiced': item.last_practiced,
            'id': item.id
        })
    
    # Sort each category by mastery level (lowest first)
    vocab_data.sort(key=lambda x: (x['mastery_level'], -(x['times_practiced'] or 0)))
    phrasal_data.sort(key=lambda x: (x['mastery_level'], -(x['times_practiced'] or 0)))
    idiom_data.sort(key=lambda x: (x['mastery_level'], -(x['times_practiced'] or 0)))
    
    # Calculate category statistics
    def calc_category_stats(items):
        total = len(items)
        practiced = sum(1 for item in items if item['times_practiced'] > 0)
        needs_practice = sum(1 for item in items if item['mastery_level'] <= 2)
        good_progress = sum(1 for item in items if 3 <= item['mastery_level'] <= 4)
        mastered = sum(1 for item in items if item['mastery_level'] == 5)
        
        return {
            'total': total,
            'practiced': practiced,
            'needs_practice': needs_practice,
            'good_progress': good_progress,
            'mastered': mastered,
            'practice_percentage': round((practiced / total * 100) if total > 0 else 0)
        }
    
    vocab_stats = calc_category_stats(vocab_data)
    phrasal_stats = calc_category_stats(phrasal_data)
    idiom_stats = calc_category_stats(idiom_data)
    
    # Calculate overall statistics
    total_items = len(vocabulary_items) + len(phrasal_verbs) + len(idioms)
    total_practiced = vocab_stats['practiced'] + phrasal_stats['practiced'] + idiom_stats['practiced']
    total_needs_practice = vocab_stats['needs_practice'] + phrasal_stats['needs_practice'] + idiom_stats['needs_practice']
    total_good_progress = vocab_stats['good_progress'] + phrasal_stats['good_progress'] + idiom_stats['good_progress']
    total_mastered = vocab_stats['mastered'] + phrasal_stats['mastered'] + idiom_stats['mastered']
    
    overall_stats = {
        'total_items': total_items,
        'total_practiced': total_practiced,
        'needs_practice_count': total_needs_practice,
        'good_progress_count': total_good_progress,
        'mastered_count': total_mastered,
        'practice_percentage': round((total_practiced / total_items * 100) if total_items > 0 else 0)
    }
    
    return render_template('progress.html', 
                         vocab_data=vocab_data,
                         phrasal_data=phrasal_data,
                         idiom_data=idiom_data,
                         vocab_stats=vocab_stats,
                         phrasal_stats=phrasal_stats,
                         idiom_stats=idiom_stats,
                         overall_stats=overall_stats)

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
