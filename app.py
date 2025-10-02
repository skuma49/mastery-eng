from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vocabulary_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mastery level configuration
MASTERY_SCORE_THRESHOLD = 8  # Configurable threshold for increasing mastery level

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
    
    # Get mastered counts
    mastered_vocab = VocabularyWord.query.filter(VocabularyWord.mastery_level == 5).count()
    mastered_phrasal = PhrasalVerb.query.filter(PhrasalVerb.mastery_level == 5).count()
    mastered_idioms = Idiom.query.filter(Idiom.mastery_level == 5).count()
    total_mastered = mastered_vocab + mastered_phrasal + mastered_idioms
    
    # Get recently added items
    recent_vocab = VocabularyWord.query.order_by(VocabularyWord.date_added.desc()).limit(5).all()
    recent_phrasal = PhrasalVerb.query.order_by(PhrasalVerb.date_added.desc()).limit(5).all()
    recent_idioms = Idiom.query.order_by(Idiom.date_added.desc()).limit(5).all()
    
    return render_template('index.html', 
                         vocab_count=vocab_count,
                         phrasal_count=phrasal_count,
                         idiom_count=idiom_count,
                         mastered_vocab=mastered_vocab,
                         mastered_phrasal=mastered_phrasal,
                         mastered_idioms=mastered_idioms,
                         total_mastered=total_mastered,
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
    # Get limit parameter for mini practice
    limit = request.args.get('limit', type=int)
    
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
    
    # Apply limit for mini practice if specified
    if limit and limit > 0:
        items_data = items_data[:limit]
        practice_type = f"Mini Practice ({len(items_data)} cards)"
    else:
        practice_type = f"Full Practice ({len(items_data)} cards)"
    
    return render_template(template, items=items_data, category=category, 
                         practice_type=practice_type, is_mini=bool(limit))

@app.route('/api/flashcards/<category>')
def api_flashcards(category):
    # Get limit parameter for mini practice
    limit = request.args.get('limit', type=int)
    
    if category == 'vocabulary':
        items = VocabularyWord.query.all()
    elif category == 'phrasal-verbs':
        items = PhrasalVerb.query.all()
    elif category == 'idioms':
        items = Idiom.query.all()
    else:
        return jsonify({'error': 'Invalid category'}), 400
    
    random.shuffle(items)
    items_data = [item.to_dict() for item in items]
    
    # Apply limit for mini practice if specified
    if limit and limit > 0:
        items_data = items_data[:limit]
    
    return jsonify(items_data)

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

@app.route('/test')
def test():
    """10-minute test with sentence creation"""
    return render_template('test.html')

@app.route('/evaluation-results')
def evaluation_results():
    """Display evaluation results with JSON upload functionality"""
    return render_template('evaluation_results.html')

@app.route('/api/process-mastery-levels', methods=['POST'])
def process_mastery_levels():
    """Process evaluation results and update mastery levels for high-scoring items"""
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug print
        
        if not data or 'detailed_evaluation' not in data:
            return jsonify({'success': False, 'message': 'Invalid data format'}), 400
        
        detailed_evaluation = data['detailed_evaluation']
        threshold = data.get('threshold', MASTERY_SCORE_THRESHOLD)
        
        updated_items = []
        not_found_items = []
        
        for item in detailed_evaluation:
            score = item.get('Score', 0)
            item_type = item.get('Type', '').lower()
            word_phrase = item.get('Word/Phrase', '').strip()
            
            if score >= threshold and word_phrase:
                # Find and update the appropriate item based on type
                updated = False
                
                if item_type == 'vocabulary':
                    vocab_item = VocabularyWord.query.filter(
                        VocabularyWord.word.ilike(f'%{word_phrase}%')
                    ).first()
                    
                    if vocab_item:
                        old_level = vocab_item.mastery_level
                        vocab_item.mastery_level += 1
                        vocab_item.last_practiced = datetime.utcnow()
                        vocab_item.times_practiced += 1
                        try:
                            db.session.commit()
                        except Exception as db_error:
                            db.session.rollback()
                            print(f"Database error for vocabulary item {word_phrase}: {db_error}")
                            continue
                        updated_items.append({
                            'type': 'vocabulary',
                            'word': word_phrase,
                            'old_level': old_level,
                            'new_level': vocab_item.mastery_level,
                            'score': score
                        })
                        updated = True
                
                elif item_type == 'idiom':
                    idiom_item = Idiom.query.filter(
                        Idiom.idiom.ilike(f'%{word_phrase}%')
                    ).first()
                    
                    if idiom_item:
                        old_level = idiom_item.mastery_level
                        idiom_item.mastery_level += 1
                        idiom_item.last_practiced = datetime.utcnow()
                        idiom_item.times_practiced += 1
                        try:
                            db.session.commit()
                        except Exception as db_error:
                            db.session.rollback()
                            print(f"Database error for idiom item {word_phrase}: {db_error}")
                            continue
                        updated_items.append({
                            'type': 'idiom',
                            'word': word_phrase,
                            'old_level': old_level,
                            'new_level': idiom_item.mastery_level,
                            'score': score
                        })
                        updated = True
                
                elif item_type == 'phrasal_verb':
                    phrasal_item = PhrasalVerb.query.filter(
                        PhrasalVerb.phrasal_verb.ilike(f'%{word_phrase}%')
                    ).first()
                    
                    if phrasal_item:
                        old_level = phrasal_item.mastery_level
                        phrasal_item.mastery_level += 1
                        phrasal_item.last_practiced = datetime.utcnow()
                        phrasal_item.times_practiced += 1
                        try:
                            db.session.commit()
                        except Exception as db_error:
                            db.session.rollback()
                            print(f"Database error for phrasal verb item {word_phrase}: {db_error}")
                            continue
                        updated_items.append({
                            'type': 'phrasal_verb',
                            'word': word_phrase,
                            'old_level': old_level,
                            'new_level': phrasal_item.mastery_level,
                            'score': score
                        })
                        updated = True
                
                if not updated:
                    not_found_items.append({
                        'type': item_type,
                        'word': word_phrase,
                        'score': score
                    })
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated {len(updated_items)} items',
            'updated_items': updated_items,
            'not_found_items': not_found_items,
            'threshold_used': threshold,
            'total_processed': len(detailed_evaluation)
        })
        
    except Exception as e:
        print(f"Error in process_mastery_levels: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error processing mastery levels: {str(e)}'}), 500

@app.route('/api/generate-test', methods=['POST'])
def generate_test():
    """Generate test questions based on mastery level >= 2"""
    # Get items with mastery level >= 2
    vocab_items = VocabularyWord.query.filter(VocabularyWord.mastery_level >= 2).all()
    phrasal_items = PhrasalVerb.query.filter(PhrasalVerb.mastery_level >= 2).all()
    idiom_items = Idiom.query.filter(Idiom.mastery_level >= 2).all()
    
    # Calculate question counts based on available items (target: 10 questions for 10-minute test)
    target_questions = 10
    total_available = len(vocab_items) + len(phrasal_items) + len(idiom_items)
    
    if total_available == 0:
        return jsonify({
            'success': False,
            'message': 'No items with mastery level 2 or higher found'
        })
    
    # Use all available items if less than target, otherwise use proportional distribution
    actual_total = min(target_questions, total_available)
    
    # Calculate proportional counts based on available items
    idiom_count = min(len(idiom_items), max(1, int(actual_total * 0.4)) if len(idiom_items) > 0 else 0)
    vocab_count = min(len(vocab_items), max(1, int(actual_total * 0.3)) if len(vocab_items) > 0 else 0)
    
    # Remaining questions go to phrasal verbs, but don't exceed available
    remaining = actual_total - idiom_count - vocab_count
    phrasal_count = min(len(phrasal_items), max(0, remaining))
    
    # Adjust if we still have too few questions
    total_selected = idiom_count + vocab_count + phrasal_count
    if total_selected < actual_total:
        # Distribute remaining questions to categories that have more items available
        remaining_to_distribute = actual_total - total_selected
        if len(idiom_items) > idiom_count:
            additional_idioms = min(remaining_to_distribute, len(idiom_items) - idiom_count)
            idiom_count += additional_idioms
            remaining_to_distribute -= additional_idioms
        if remaining_to_distribute > 0 and len(vocab_items) > vocab_count:
            additional_vocab = min(remaining_to_distribute, len(vocab_items) - vocab_count)
            vocab_count += additional_vocab
            remaining_to_distribute -= additional_vocab
        if remaining_to_distribute > 0 and len(phrasal_items) > phrasal_count:
            phrasal_count += min(remaining_to_distribute, len(phrasal_items) - phrasal_count)
    
    # Select random items
    selected_questions = []
    
    # Select idioms
    if idiom_count > 0:
        selected_idioms = random.sample(idiom_items, idiom_count)
        for item in selected_idioms:
            selected_questions.append({
                'type': 'idiom',
                'id': item.id,
                'text': item.idiom,
                'meaning': item.meaning,
                'example': item.example_sentence
            })
    
    # Select vocabulary
    if vocab_count > 0:
        selected_vocab = random.sample(vocab_items, vocab_count)
        for item in selected_vocab:
            selected_questions.append({
                'type': 'vocabulary',
                'id': item.id,
                'text': item.word,
                'meaning': item.definition,
                'example': item.example_sentence
            })
    
    # Select phrasal verbs
    if phrasal_count > 0:
        selected_phrasal = random.sample(phrasal_items, phrasal_count)
        for item in selected_phrasal:
            selected_questions.append({
                'type': 'phrasal_verb',
                'id': item.id,
                'text': item.phrasal_verb,
                'meaning': item.meaning,
                'example': item.example_sentence,
                'separable': item.separable
            })
    
    # Shuffle questions
    random.shuffle(selected_questions)
    
    return jsonify({
        'success': True,
        'questions': selected_questions,
        'total_questions': len(selected_questions),
        'duration_minutes': 10
    })

@app.route('/api/submit-test', methods=['POST'])
def submit_test():
    """Handle test submission and generate downloadable JSON"""
    data = request.json
    responses = data.get('responses', [])
    
    # Create result JSON with timestamp
    test_result = {
        'test_date': datetime.utcnow().isoformat(),
        'duration_minutes': 10,
        'total_questions': len(responses),
        'responses': responses
    }
    
    return jsonify({
        'success': True,
        'message': 'Test completed successfully!',
        'result': test_result
    })

# Mastered Words Section
@app.route('/mastered')
def mastered_words():
    """Show all mastered words (mastery_level = 5)"""
    # Get mastered vocabulary words
    mastered_vocab = VocabularyWord.query.filter(VocabularyWord.mastery_level == 5).all()
    
    # Get mastered phrasal verbs
    mastered_phrasal = PhrasalVerb.query.filter(PhrasalVerb.mastery_level == 5).all()
    
    # Get mastered idioms
    mastered_idioms = Idiom.query.filter(Idiom.mastery_level == 5).all()
    
    # Calculate statistics
    total_mastered = len(mastered_vocab) + len(mastered_phrasal) + len(mastered_idioms)
    
    stats = {
        'vocabulary': len(mastered_vocab),
        'phrasal_verbs': len(mastered_phrasal),
        'idioms': len(mastered_idioms),
        'total': total_mastered
    }
    
    return render_template('mastered_words.html', 
                         mastered_vocab=mastered_vocab,
                         mastered_phrasal=mastered_phrasal,
                         mastered_idioms=mastered_idioms,
                         stats=stats)

@app.route('/mastered/test')
def mastered_test():
    """Advanced test for mastered words"""
    return render_template('mastered_test.html')

@app.route('/submit-evaluation')
def submit_evaluation():
    """Page for submitting evaluation results from external system"""
    return render_template('submit_evaluation.html')

@app.route('/api/mastered-test-questions')
def get_mastered_test_questions():
    """Get sentence writing test questions for mastered words only"""
    # Get all mastered items (no need for example sentences as users will create their own)
    mastered_vocab = VocabularyWord.query.filter(VocabularyWord.mastery_level == 5).all()
    mastered_phrasal = PhrasalVerb.query.filter(PhrasalVerb.mastery_level == 5).all()
    mastered_idioms = Idiom.query.filter(Idiom.mastery_level == 5).all()
    
    all_sentence_questions = []
    
    # Add vocabulary sentence writing questions
    for word in mastered_vocab:
        all_sentence_questions.append({
            'type': 'vocabulary',
            'format': 'sentence_writing',
            'id': word.id,
            'word': word.word,
            'definition': word.definition,
            'part_of_speech': word.part_of_speech,
            'pronunciation': word.pronunciation,
            'example_sentence': word.example_sentence,
            'difficulty_level': word.difficulty_level,
            'category': 'vocabulary',
            'question': f"Write a creative sentence using the word '{word.word}'",
            'instructions': f"Create an original sentence that demonstrates your understanding of '{word.word}' (meaning: {word.definition})"
        })
    
    # Add phrasal verb sentence writing questions
    for phrasal in mastered_phrasal:
        all_sentence_questions.append({
            'type': 'phrasal_verb',
            'format': 'sentence_writing',
            'id': phrasal.id,
            'word': phrasal.phrasal_verb,
            'meaning': phrasal.meaning,
            'separable': phrasal.separable,
            'example_sentence': phrasal.example_sentence,
            'difficulty_level': phrasal.difficulty_level,
            'category': 'phrasal_verb',
            'question': f"Write a creative sentence using the phrasal verb '{phrasal.phrasal_verb}'",
            'instructions': f"Create an original sentence that demonstrates your understanding of '{phrasal.phrasal_verb}' (meaning: {phrasal.meaning}){' - Note: This is a separable phrasal verb' if phrasal.separable else ' - Note: This is an inseparable phrasal verb'}"
        })
    
    # Add idiom sentence writing questions
    for idiom in mastered_idioms:
        all_sentence_questions.append({
            'type': 'idiom',
            'format': 'sentence_writing',
            'id': idiom.id,
            'word': idiom.idiom,
            'meaning': idiom.meaning,
            'origin': idiom.origin,
            'example_sentence': idiom.example_sentence,
            'difficulty_level': idiom.difficulty_level,
            'category': 'idiom',
            'question': f"Write a creative sentence using the idiom '{idiom.idiom}'",
            'instructions': f"Create an original sentence that demonstrates your understanding of '{idiom.idiom}' (meaning: {idiom.meaning})"
        })
    
    if not all_sentence_questions:
        return jsonify({
            'success': False,
            'message': 'No mastered words found for testing. Master some words first!',
            'questions': []
        })
    
    # Shuffle and select questions dynamically based on available mastered words
    random.shuffle(all_sentence_questions)
    
    # Select up to 10 questions for sentence writing (fewer than fill-in-blank as they take more time)
    max_questions = min(10, len(all_sentence_questions))
    selected_questions = all_sentence_questions[:max_questions]
    
    return jsonify({
        'success': True,
        'questions': selected_questions,
        'total_questions': len(selected_questions),
        'available_mastered': {
            'vocabulary': len(mastered_vocab),
            'phrasal_verbs': len(mastered_phrasal),
            'idioms': len(mastered_idioms),
            'total': len(mastered_vocab) + len(mastered_phrasal) + len(mastered_idioms)
        },
        'test_format': 'sentence_writing',
        'instructions': 'Write creative and original sentences using your mastered words to demonstrate true understanding.'
    })

@app.route('/api/submit-mastered-test', methods=['POST'])
def submit_mastered_test():
    """Handle mastered test submission and return JSON for external evaluation"""
    data = request.get_json()
    responses = data.get('responses', [])
    
    # Create a comprehensive test result JSON
    test_result = {
        'test_metadata': {
            'test_date': datetime.utcnow().isoformat(),
            'test_type': 'sentence_writing_mastery_test',
            'total_questions': len(responses),
            'user_id': 'anonymous',  # You can add user identification later
            'test_version': '1.0'
        },
        'questions_and_responses': []
    }
    
    # Process each response and add to result
    for response in responses:
        item_id = response.get('id')
        item_type = response.get('type')
        user_sentence = response.get('user_sentence', '')
        
        # Get the item details from database
        # Get the item from database
        item = None
        if item_type == 'vocabulary':
            item = db.session.get(VocabularyWord, item_id)
        elif item_type == 'phrasal_verb':
            item = db.session.get(PhrasalVerb, item_id)
        elif item_type == 'idiom':
            item = db.session.get(Idiom, item_id)
        
        if item:
            # Get the target word based on item type
            if item_type == 'vocabulary':
                target_word = item.word
                definition_or_meaning = item.definition
            elif item_type == 'phrasal_verb':
                target_word = item.phrasal_verb
                definition_or_meaning = item.meaning
            else:  # idiom
                target_word = item.idiom
                definition_or_meaning = item.meaning
            
            question_response = {
                'question_id': item_id,
                'word_type': item_type,
                'target_word': target_word,
                'user_sentence': user_sentence,
                'word_details': {
                    'definition_or_meaning': definition_or_meaning,
                    'part_of_speech': getattr(item, 'part_of_speech', None),
                    'difficulty_level': item.difficulty_level,
                    'original_example': getattr(item, 'example_sentence', ''),
                    'pronunciation': getattr(item, 'pronunciation', None),
                    'separable': getattr(item, 'separable', None),  # For phrasal verbs
                    'origin': getattr(item, 'origin', None)  # For idioms
                },
                'evaluation_criteria': {
                    'word_used_correctly': None,  # To be filled by external evaluator
                    'demonstrates_understanding': None,  # To be filled by external evaluator
                    'grammar_correct': None,  # To be filled by external evaluator
                    'creative_usage': None,  # To be filled by external evaluator
                    'overall_score': None,  # To be filled by external evaluator (0-100)
                    'evaluator_comments': ''  # To be filled by external evaluator
                }
            }
            
            test_result['questions_and_responses'].append(question_response)
    
    # Return the JSON structure for external evaluation
    return jsonify({
        'success': True,
        'message': 'Test responses collected successfully. Use the test_result JSON for external evaluation.',
        'test_result': test_result,
        'download_filename': f'mastery_test_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json',
        'evaluation_instructions': {
            'overview': 'Evaluate each sentence based on correct word usage, understanding demonstration, grammar, and creativity.',
            'scoring_guide': {
                'word_used_correctly': 'true/false - Is the target word used correctly in context?',
                'demonstrates_understanding': 'true/false - Does the sentence show understanding of the word meaning?',
                'grammar_correct': 'true/false - Is the sentence grammatically correct?',
                'creative_usage': 'true/false - Is the usage creative and original?',
                'overall_score': '0-100 - Overall quality of the sentence (0=poor, 100=excellent)',
                'evaluator_comments': 'Optional feedback for the learner'
            }
        }
    })

@app.route('/api/submit-evaluation-results', methods=['POST'])
def submit_evaluation_results():
    """Submit evaluation results and update mastery levels based on external evaluation"""
    data = request.get_json()
    evaluated_results = data.get('evaluated_results', [])
    
    passed_items = []
    failed_items = []
    
    # Process each evaluated response
    for result in evaluated_results:
        item_id = result.get('question_id')
        item_type = result.get('word_type')
        evaluation = result.get('evaluation_criteria', {})
        
        # Determine if the word should remain mastered based on evaluation
        overall_score = evaluation.get('overall_score', 0)
        word_used_correctly = evaluation.get('word_used_correctly', False)
        demonstrates_understanding = evaluation.get('demonstrates_understanding', False)
        
        # Consider it passed if overall score >= 70 AND word is used correctly AND demonstrates understanding
        passed = (overall_score >= 70 and word_used_correctly and demonstrates_understanding)
        
        # Get the item from database
        item = None
        if item_type == 'vocabulary':
            item = db.session.get(VocabularyWord, item_id)
        elif item_type == 'phrasal_verb':
            item = db.session.get(PhrasalVerb, item_id)
        elif item_type == 'idiom':
            item = db.session.get(Idiom, item_id)
        
        if item:
            # Get the text based on item type
            if item_type == 'vocabulary':
                item_text = item.word
            elif item_type == 'phrasal_verb':
                item_text = item.phrasal_verb
            else:  # idiom
                item_text = item.idiom
            
            if passed:
                passed_items.append({
                    'id': item.id,
                    'type': item_type,
                    'text': item_text,
                    'score': overall_score
                })
            else:
                # Reset mastery level to 0 and reset practice counter
                item.mastery_level = 0
                item.times_practiced = 0
                item.last_practiced = datetime.utcnow()
                
                failed_items.append({
                    'id': item.id,
                    'type': item_type,
                    'text': item_text,
                    'score': overall_score
                })
    
    # Commit changes to database
    db.session.commit()
    
    # Calculate overall statistics
    total_questions = len(evaluated_results)
    passed_count = len(passed_items)
    score_percentage = round((passed_count / total_questions * 100) if total_questions > 0 else 0)
    
    return jsonify({
        'success': True,
        'evaluation_complete': True,
        'score_percentage': score_percentage,
        'passed_count': passed_count,
        'failed_count': len(failed_items),
        'total_questions': total_questions,
        'passed_items': passed_items,
        'failed_items': failed_items,
        'message': f'Evaluation completed! {passed_count}/{total_questions} words remain mastered. {len(failed_items)} words moved back to practice.'
    })

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
