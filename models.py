from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class VocabularyWord(db.Model):
    __tablename__ = 'vocabulary_words'
    
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    definition = db.Column(db.Text, nullable=False)
    example_sentence = db.Column(db.Text)
    pronunciation = db.Column(db.String(100))
    part_of_speech = db.Column(db.String(50))
    difficulty_level = db.Column(db.String(20), default='medium')  # easy, medium, hard
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    times_practiced = db.Column(db.Integer, default=0)
    last_practiced = db.Column(db.DateTime)
    mastery_level = db.Column(db.Integer, default=0)  # 0-5 scale
    
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
            'date_added': self.date_added.strftime('%Y-%m-%d %H:%M:%S') if self.date_added else None,
            'times_practiced': self.times_practiced,
            'last_practiced': self.last_practiced.strftime('%Y-%m-%d %H:%M:%S') if self.last_practiced else None,
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
            'date_added': self.date_added.strftime('%Y-%m-%d %H:%M:%S') if self.date_added else None,
            'times_practiced': self.times_practiced,
            'last_practiced': self.last_practiced.strftime('%Y-%m-%d %H:%M:%S') if self.last_practiced else None,
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
            'date_added': self.date_added.strftime('%Y-%m-%d %H:%M:%S') if self.date_added else None,
            'times_practiced': self.times_practiced,
            'last_practiced': self.last_practiced.strftime('%Y-%m-%d %H:%M:%S') if self.last_practiced else None,
            'mastery_level': self.mastery_level
        }
