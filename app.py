from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Unified Test Configuration Classes
class TestConfiguration:
    """Configuration class for different test types"""
    
    REGULAR_TEST = {
        'name': 'regular',
        'mastery_levels': [2, 3, 4],  # Exclude mastered (5) and unlearned (0-1)
        'question_distribution': {'idioms': 0.4, 'vocabulary': 0.3, 'phrasal_verbs': 0.3},
        'max_questions': 10,
        'has_timer': True,
        'timer_duration': 600,  # 10 minutes
        'show_definitions': True,
        'show_examples': True,
        'test_format': 'mixed_practice'
    }
    
    MASTERY_TEST = {
        'name': 'mastery',
        'mastery_levels': [5],  # Only mastered items
        'question_distribution': {'idioms': 0.33, 'vocabulary': 0.33, 'phrasal_verbs': 0.34},
        'max_questions': 10,
        'has_timer': False,
        'timer_duration': None,
        'show_definitions': False,
        'show_examples': False,
        'test_format': 'sentence_writing'
    }
    
    @classmethod
    def get_config(cls, test_type):
        """Get configuration for specified test type"""
        configs = {
            'regular': cls.REGULAR_TEST,
            'mastery': cls.MASTERY_TEST
        }
        return configs.get(test_type, cls.REGULAR_TEST)

class UnifiedTestManager:
    """Unified test management class"""
    
    def __init__(self, test_type='regular'):
        self.config = TestConfiguration.get_config(test_type)
        self.test_type = test_type
    
    def get_available_items(self):
        """Get items based on test type mastery level requirements"""
        mastery_levels = self.config['mastery_levels']
        
        # Query items by mastery level
        vocab_items = VocabularyWord.query.filter(
            VocabularyWord.mastery_level.in_(mastery_levels)
        ).all()
        
        phrasal_items = PhrasalVerb.query.filter(
            PhrasalVerb.mastery_level.in_(mastery_levels)
        ).all()
        
        idiom_items = Idiom.query.filter(
            Idiom.mastery_level.in_(mastery_levels)
        ).all()
        
        return {
            'vocabulary': vocab_items,
            'phrasal_verbs': phrasal_items,
            'idioms': idiom_items
        }
    
    def calculate_question_distribution(self, available_items):
        """Calculate how many questions of each type to include"""
        total_available = sum(len(items) for items in available_items.values())
        
        if total_available == 0:
            return {'vocabulary': 0, 'phrasal_verbs': 0, 'idioms': 0}
        
        max_questions = min(self.config['max_questions'], total_available)
        distribution = self.config['question_distribution']
        
        # Calculate initial counts
        counts = {}
        for category, ratio in distribution.items():
            available_count = len(available_items.get(category, []))
            ideal_count = int(max_questions * ratio)
            counts[category] = min(available_count, max(1 if available_count > 0 else 0, ideal_count))
        
        # Adjust if we have fewer total questions than max
        total_selected = sum(counts.values())
        remaining = max_questions - total_selected
        
        # Distribute remaining questions to categories with availability
        for category in counts:
            if remaining <= 0:
                break
            available_count = len(available_items.get(category, []))
            current_count = counts[category]
            additional = min(remaining, available_count - current_count)
            if additional > 0:
                counts[category] += additional
                remaining -= additional
        
        return counts
    
    def generate_questions(self):
        """Generate questions based on test configuration"""
        available_items = self.get_available_items()
        question_counts = self.calculate_question_distribution(available_items)
        
        total_available = sum(len(items) for items in available_items.values())
        if total_available == 0:
            return {
                'success': False,
                'message': self.get_no_items_message(),
                'questions': []
            }
        
        selected_questions = []
        
        # Generate questions for each category
        for category, count in question_counts.items():
            if count > 0 and available_items[category]:
                items = random.sample(available_items[category], count)
                for item in items:
                    question = self.create_question_from_item(item, category)
                    selected_questions.append(question)
        
        # Shuffle questions
        random.shuffle(selected_questions)
        
        return {
            'success': True,
            'questions': selected_questions,
            'total_questions': len(selected_questions),
            'test_config': self.config,
            'available_stats': {
                'vocabulary': len(available_items['vocabulary']),
                'phrasal_verbs': len(available_items['phrasal_verbs']),
                'idioms': len(available_items['idioms'])
            }
        }
    
    def create_question_from_item(self, item, category):
        """Create a question object from a database item"""
        base_question = {
            'id': item.id,
            'type': category.rstrip('s'),  # Remove 's' from category name
            'category': category,
            'difficulty_level': getattr(item, 'difficulty_level', 'medium'),
            'mastery_level': getattr(item, 'mastery_level', 0)
        }
        
        if category == 'vocabulary':
            base_question.update({
                'text': item.word,
                'word': item.word,
                'meaning': item.definition if self.config['show_definitions'] else None,
                'definition': item.definition if self.config['show_definitions'] else None,
                'part_of_speech': getattr(item, 'part_of_speech', None),
                'pronunciation': getattr(item, 'pronunciation', None),
                'example': item.example_sentence if self.config['show_examples'] else None
            })
        elif category == 'phrasal_verbs':
            base_question.update({
                'text': item.phrasal_verb,
                'word': item.phrasal_verb,
                'meaning': item.meaning if self.config['show_definitions'] else None,
                'separable': getattr(item, 'separable', False),
                'example': item.example_sentence if self.config['show_examples'] else None
            })
        elif category == 'idioms':
            base_question.update({
                'text': item.idiom,
                'word': item.idiom,
                'meaning': item.meaning if self.config['show_definitions'] else None,
                'origin': getattr(item, 'origin', None),
                'example': item.example_sentence if self.config['show_examples'] else None
            })
        
        # Add test-specific question format
        if self.test_type == 'mastery':
            base_question.update({
                'format': 'sentence_writing',
                'question': f"Write a creative sentence using '{base_question['text']}'",
                'instructions': self.get_mastery_instructions(base_question)
            })
        
        return base_question
    
    def get_mastery_instructions(self, question):
        """Get instructions for mastery test questions"""
        word_type = question['type']
        word = question['text']
        
        instructions = f"Create an original sentence that demonstrates your understanding of '{word}'"
        
        if word_type == 'phrasal_verb' and question.get('separable') is not None:
            sep_text = "separable" if question['separable'] else "inseparable"
            instructions += f" (Note: This is a {sep_text} phrasal verb)"
        
        return instructions
    
    def get_no_items_message(self):
        """Get appropriate message when no items are available"""
        if self.test_type == 'mastery':
            return 'No mastered words found for testing. Master some words first!'
        else:
            return 'No items with appropriate mastery levels found. Practice more to unlock tests!'
    
    def process_submission(self, submission_data):
        """Process test submission and create result data"""
        responses = submission_data.get('responses', [])
        
        # Create metadata
        metadata = {
            'test_date': datetime.utcnow().isoformat(),
            'test_type': self.config['test_format'],
            'total_questions': len(responses),
            'test_config': self.test_type,
            'user_id': 'anonymous',  # Can be enhanced with user system
            'test_version': '2.0'
        }
        
        if self.test_type == 'regular':
            return self.process_regular_submission(responses, metadata)
        else:
            return self.process_mastery_submission(responses, metadata)
    
    def process_regular_submission(self, responses, metadata):
        """Process regular test submission"""
        test_result = {
            'test_date': metadata['test_date'],
            'duration_minutes': 10,
            'total_questions': metadata['total_questions'],
            'responses': responses
        }
        
        return {
            'success': True,
            'message': 'Test completed successfully!',
            'result': test_result,
            'download_filename': f'mastery-english-test-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
        }
    
    def process_mastery_submission(self, responses, metadata):
        """Process mastery test submission with detailed evaluation format"""
        # Create comprehensive evaluation format
        questions_and_responses = []
        
        for response in responses:
            item_id = response.get('id')
            item_type = response.get('type')
            user_sentence = response.get('user_sentence', '')
            
            # Get item details from database
            item = self.get_item_by_id_and_type(item_id, item_type)
            
            if item:
                target_word, definition_or_meaning = self.extract_item_details(item, item_type)
                
                question_data = {
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
                        'separable': getattr(item, 'separable', None),
                        'origin': getattr(item, 'origin', None)
                    },
                    'evaluation_criteria': {
                        'word_used_correctly': None,
                        'demonstrates_understanding': None,
                        'grammar_correct': None,
                        'creative_usage': None,
                        'overall_score': None,
                        'evaluator_comments': None
                    }
                }
                questions_and_responses.append(question_data)
        
        test_result = {
            'test_metadata': metadata,
            'questions_and_responses': questions_and_responses
        }
        
        return {
            'success': True,
            'message': 'Advanced test completed! Download JSON for external evaluation.',
            'test_result': test_result,
            'download_filename': f'mastery-test-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
        }
    
    def get_item_by_id_and_type(self, item_id, item_type):
        """Get database item by ID and type"""
        if item_type == 'vocabulary':
            return db.session.get(VocabularyWord, item_id)
        elif item_type == 'phrasal_verb':
            return db.session.get(PhrasalVerb, item_id)
        elif item_type == 'idiom':
            return db.session.get(Idiom, item_id)
        return None
    
    def extract_item_details(self, item, item_type):
        """Extract target word and definition from item"""
        if item_type == 'vocabulary':
            return item.word, item.definition
        elif item_type == 'phrasal_verb':
            return item.phrasal_verb, item.meaning
        elif item_type == 'idiom':
            return item.idiom, item.meaning
        return '', ''

class UnifiedEvaluationManager:
    """Unified evaluation management for all test types"""
    
    def __init__(self):
        self.supported_formats = ['regular_test', 'mastery_test', 'mixed']
    
    def detect_evaluation_format(self, data):
        """Detect the format of evaluation data"""
        print(f"Debug: Detecting format for data type: {type(data)}")
        if isinstance(data, dict):
            print(f"Debug: Data keys: {list(data.keys())}")
            print(f"Debug: Has summary: {'summary' in data}")
            print(f"Debug: Has details: {'details' in data}")
        
        if 'test_metadata' in data and 'questions_and_responses' in data:
            print("Debug: Detected mastery_test format")
            return 'mastery_test'
        elif 'responses' in data and isinstance(data['responses'], list):
            print("Debug: Detected regular_test format")
            return 'regular_test'
        elif 'evaluated_results' in data:
            print("Debug: Detected external_evaluation format")
            return 'external_evaluation'
        elif ('summary' in data or 'evaluation_summary' in data) and 'details' in data:
            print("Debug: Found summary/evaluation_summary and details - returning evaluation_report")
            return 'evaluation_report'
        elif isinstance(data, dict) and any(key in data for key in ['Test Date', 'Duration (minutes)', 'Total Questions', 'overall_score', 'total_questions']):
            print("Debug: Detected evaluation_report by summary keys")
            return 'evaluation_report'
        elif 'test_type' in data and 'questions' in data and 'metadata' in data:
            print("Debug: Detected raw_test_results format")
            return 'raw_test_results'
        else:
            print(f"Debug: Unknown format for data: {data}")
            return 'unknown'
    
    def process_evaluation_upload(self, data):
        """Process uploaded evaluation data and return standardized format"""
        eval_format = self.detect_evaluation_format(data)
        
        if eval_format == 'mastery_test':
            return self.process_mastery_evaluation(data)
        elif eval_format == 'regular_test':
            return self.process_regular_evaluation(data)
        elif eval_format == 'external_evaluation':
            return self.process_external_evaluation(data)
        elif eval_format == 'evaluation_report':
            return self.process_evaluation_report(data)
        elif eval_format == 'raw_test_results':
            return self.process_raw_test_results(data)
        else:
            print(f"Debug: Unsupported format '{eval_format}' for data: {data}")
            raise ValueError(f"Unsupported evaluation format: {eval_format}")
    
    def process_mastery_evaluation(self, data):
        """Process mastery test evaluation data"""
        metadata = data.get('test_metadata', {})
        questions = data.get('questions_and_responses', [])
        
        processed_results = []
        for question in questions:
            result = {
                'question_id': question.get('question_id'),
                'test_type': 'mastery',
                'word_type': question.get('word_type'),
                'target_word': question.get('target_word'),
                'user_response': question.get('user_sentence', ''),
                'word_details': question.get('word_details', {}),
                'evaluation': question.get('evaluation_criteria', {}),
                'has_evaluation': any(v is not None for v in question.get('evaluation_criteria', {}).values())
            }
            processed_results.append(result)
        
        return {
            'success': True,
            'format': 'mastery_test',
            'metadata': {
                'test_date': metadata.get('test_date'),
                'test_type': metadata.get('test_type', 'mastery'),
                'total_questions': len(processed_results),
                'test_version': metadata.get('test_version', '1.0')
            },
            'results': processed_results,
            'can_update_mastery': True,
            'evaluation_complete': any(r['has_evaluation'] for r in processed_results)
        }
    
    def process_regular_evaluation(self, data):
        """Process regular test evaluation data"""
        responses = data.get('responses', [])
        
        processed_results = []
        for i, response in enumerate(responses):
            result = {
                'question_id': response.get('id', i),
                'test_type': 'regular',
                'word_type': response.get('type'),
                'target_word': response.get('text'),
                'user_response': response.get('user_sentence', ''),
                'word_details': {
                    'definition_or_meaning': response.get('meaning', ''),
                    'example_sentence': response.get('example_sentence', '')
                },
                'evaluation': {},
                'has_evaluation': False
            }
            processed_results.append(result)
        
        return {
            'success': True,
            'format': 'regular_test',
            'metadata': {
                'test_date': data.get('test_date'),
                'test_type': 'regular',
                'total_questions': len(processed_results),
                'duration_minutes': data.get('duration_minutes', 10)
            },
            'results': processed_results,
            'can_update_mastery': False,
            'evaluation_complete': False
        }
    
    def process_external_evaluation(self, data):
        """Process external evaluation results"""
        evaluated_results = data.get('evaluated_results', [])
        
        processed_results = []
        for result in evaluated_results:
            evaluation = result.get('evaluation_criteria', {})
            processed_result = {
                'question_id': result.get('question_id'),
                'test_type': 'mastery',
                'word_type': result.get('word_type'),
                'target_word': result.get('target_word', ''),
                'user_response': result.get('user_sentence', ''),
                'word_details': result.get('word_details', {}),
                'evaluation': evaluation,
                'has_evaluation': True
            }
            processed_results.append(processed_result)
        
        return {
            'success': True,
            'format': 'external_evaluation',
            'metadata': {
                'test_type': 'mastery',
                'total_questions': len(processed_results),
                'evaluation_date': datetime.utcnow().isoformat()
            },
            'results': processed_results,
            'can_update_mastery': True,
            'evaluation_complete': True
        }
    
    def find_item_id_by_word(self, word_phrase, word_type):
        """Find the database ID of an item by its word/phrase and type"""
        try:
            if word_type == 'vocabulary':
                item = VocabularyWord.query.filter_by(word=word_phrase).first()
            elif word_type == 'phrasal_verb':
                item = PhrasalVerb.query.filter_by(phrasal_verb=word_phrase).first()
            elif word_type == 'idiom':
                item = Idiom.query.filter_by(idiom=word_phrase).first()
            else:
                return None
            
            return item.id if item else None
        except Exception as e:
            print(f"Error finding item by word '{word_phrase}' of type '{word_type}': {e}")
            return None

    def process_evaluation_report(self, data):
        """Process evaluation report format with summary and details"""
        processed_results = []
        
        # Extract results from details section
        details = data.get('details', {})
        
        # Handle case where details might be a list or dict
        if isinstance(details, list):
            # If details is a list, process each item directly
            for item in details:
                # Map the actual JSON field names to our expected format
                word_phrase = item.get('Word/Phrase', item.get('word', ''))
                user_answer = item.get('User Answer', item.get('user_answer', ''))
                score = item.get('Score', item.get('score', 0))
                feedback = item.get('Feedback', item.get('feedback', ''))
                word_type = item.get('Type', item.get('type', 'vocabulary')).lower()
                question_num = item.get('Question #', item.get('question_id', ''))
                
                # Find the actual database ID using word name and type
                actual_question_id = self.find_item_id_by_word(word_phrase, word_type)
                if actual_question_id is None:
                    print(f"Warning: Could not find database ID for '{word_phrase}' of type '{word_type}'")
                    actual_question_id = question_num  # Fallback to question number
                
                processed_result = {
                    'question_id': actual_question_id,
                    'test_type': 'evaluation_report',
                    'word_type': word_type,
                    'target_word': word_phrase,
                    'user_response': user_answer,
                    'word_details': {
                        'word': word_phrase,
                        'definition': '',  # Not provided in this format
                        'feedback': feedback
                    },
                    'evaluation': {
                        'correct': score >= 7,  # Consider score >= 7 as correct
                        'score': score,
                        'feedback': feedback
                    },
                    'has_evaluation': True,
                    'category': word_type
                }
                processed_results.append(processed_result)
        elif isinstance(details, dict):
            # Process each category in details if it's a dictionary
            for category, category_data in details.items():
                if isinstance(category_data, dict) and 'results' in category_data:
                    for item in category_data['results']:
                        processed_result = {
                            'question_id': item.get('question_id'),
                            'test_type': 'evaluation_report',
                            'word_type': category,
                            'target_word': item.get('word', ''),
                            'user_response': item.get('user_answer', ''),
                            'word_details': {
                                'word': item.get('word', ''),
                                'definition': item.get('correct_answer', '')
                            },
                            'evaluation': {
                                'correct': item.get('correct', False),
                                'score': 1 if item.get('correct', False) else 0
                            },
                            'has_evaluation': True,
                            'category': category
                        }
                        processed_results.append(processed_result)
                elif isinstance(category_data, list):
                    # Handle case where category contains a list of results
                    for item in category_data:
                        # Map the actual JSON field names to our expected format
                        word_phrase = item.get('Word/Phrase', item.get('word', ''))
                        user_answer = item.get('User Answer', item.get('user_answer', ''))
                        score = item.get('Score', item.get('score', 0))
                        feedback = item.get('Feedback', item.get('feedback', ''))
                        word_type = item.get('Type', item.get('type', category)).lower()
                        question_num = item.get('Question #', item.get('question_id', ''))
                        
                        processed_result = {
                            'question_id': question_num,
                            'test_type': 'evaluation_report',
                            'word_type': word_type,
                            'target_word': word_phrase,
                            'user_response': user_answer,
                            'word_details': {
                                'word': word_phrase,
                                'definition': '',  # Not provided in this format
                                'feedback': feedback
                            },
                            'evaluation': {
                                'correct': score >= 7,  # Consider score >= 7 as correct
                                'score': score,
                                'feedback': feedback
                            },
                            'has_evaluation': True,
                            'category': word_type
                        }
                        processed_results.append(processed_result)
        
        # Extract summary information if available
        summary = data.get('summary', {})
        if not summary and 'evaluation_summary' in data:
            summary = {'evaluation_summary': data.get('evaluation_summary')}
        
        # Add overall score and total questions if available
        if 'overall_score' in data:
            summary['overall_score'] = data['overall_score']
        if 'total_questions' in data:
            summary['total_questions'] = data['total_questions']
        
        return {
            'success': True,
            'format': 'evaluation_report',
            'metadata': {
                'test_type': 'evaluation_report',
                'total_questions': len(processed_results),
                'evaluation_date': datetime.utcnow().isoformat(),
                'summary': summary
            },
            'results': processed_results,
            'can_update_mastery': True,
            'evaluation_complete': True
        }
    
    def process_raw_test_results(self, data):
        """Process raw test results format (what gets downloaded from tests)"""
        processed_results = []
        
        # Extract questions from the raw format
        questions = data.get('questions', [])
        metadata = data.get('metadata', {})
        
        for question in questions:
            # Get current mastery level from database
            question_id = question.get('question_id', '')
            word_type = question.get('word_type', 'vocabulary')
            
            # Fetch current database item to get actual mastery level
            current_item = self.get_item_by_id_and_type(question_id, word_type)
            current_mastery_level = current_item.mastery_level if current_item else 0
            
            # Map the raw test format to our expected format
            processed_result = {
                'question_id': question_id,
                'test_type': data.get('test_type', 'regular'),
                'word_type': word_type,
                'target_word': question.get('word', ''),
                'user_response': question.get('user_answer', ''),
                'word_details': {
                    'word': question.get('word', ''),
                    'definition': question.get('definition', ''),
                    'example': question.get('example', '')
                },
                'evaluation': {
                    'correct': None,  # Not evaluated yet
                    'score': None,
                    'feedback': 'Awaiting evaluation'
                },
                'has_evaluation': False,
                'category': word_type,
                'current_mastery_level': current_mastery_level  # Add current level for reference
            }
            processed_results.append(processed_result)
        
        return {
            'success': True,
            'format': 'raw_test_results',
            'metadata': {
                'test_type': data.get('test_type', 'regular'),
                'total_questions': len(processed_results),
                'answered_questions': metadata.get('answered_questions', 0),
                'test_duration': metadata.get('test_duration', 0),
                'evaluation_date': datetime.utcnow().isoformat()
            },
            'results': processed_results,
            'can_update_mastery': False,  # Raw results need evaluation first
            'evaluation_complete': False,
            'message': 'Raw test results uploaded successfully. Evaluation is required before mastery levels can be updated.'
        }
    
    def update_mastery_levels(self, processed_data, threshold=None):
        """Update mastery levels based on evaluation results using configurable thresholds"""
        if not processed_data.get('can_update_mastery'):
            return {
                'success': False,
                'message': 'This test type does not support mastery level updates'
            }
        
        if not processed_data.get('evaluation_complete'):
            return {
                'success': False,
                'message': 'Evaluation not complete. Cannot update mastery levels.'
            }
        
        # Load configuration from environment variables
        excellent_threshold = int(os.getenv('MASTERY_EXCELLENT_THRESHOLD', 7))
        poor_threshold = int(os.getenv('MASTERY_POOR_THRESHOLD', 3))
        excellent_action = os.getenv('MASTERY_EXCELLENT_ACTION', 'increase')
        poor_action = os.getenv('MASTERY_POOR_ACTION', 'decrease')
        medium_action = os.getenv('MASTERY_MEDIUM_ACTION', 'maintain')
        
        updated_items = []
        failed_items = []
        
        for result in processed_data['results']:
            evaluation = result.get('evaluation', {})
            score = evaluation.get('score', evaluation.get('overall_score', 0))
            
            item_id = result.get('question_id')
            item_type = result.get('word_type')
            target_word = result.get('target_word')
            
            item = self.get_item_by_id_and_type(item_id, item_type)
            if not item:
                continue
                
            old_level = item.mastery_level
            new_level = old_level
            action = 'no_change'
            message = f'Level maintained at {old_level}'
            
            # Apply configurable mastery level logic based on score ranges
            if score > excellent_threshold and excellent_action == 'increase':
                # Increase mastery level by 1 (maximum 10)
                new_level = min(10, old_level + 1)
                action = 'increased_level'
                message = f'Level increased from {old_level} to {new_level} (score: {score})'
                
            elif score < poor_threshold and poor_action == 'decrease':
                # Reduce mastery level by 1 (minimum 0)
                new_level = max(0, old_level - 1)
                action = 'reduced_level'
                message = f'Level reduced from {old_level} to {new_level} (score: {score})'
                
            elif poor_threshold <= score <= excellent_threshold and medium_action == 'maintain':
                # Maintain current level (no change)
                action = 'maintained_level'
                message = f'Level maintained at {old_level} (score: {score})'
            
            # Update the item if level changed
            if new_level != old_level:
                item.mastery_level = new_level
                if new_level == 0:
                    item.times_practiced = 0
                    item.last_practiced = None
                
                try:
                    db.session.commit()
                    updated_items.append({
                        'id': item_id,
                        'word_type': item_type,
                        'word': target_word,
                        'action': action,
                        'old_level': old_level,
                        'new_level': new_level,
                        'score': score,
                        'message': message
                    })
                except Exception as e:
                    db.session.rollback()
                    failed_items.append({
                        'id': item_id,
                        'word_type': item_type,
                        'word': target_word,
                        'action': 'failed',
                        'old_level': old_level,
                        'new_level': old_level,
                        'score': score,
                        'error': str(e),
                        'message': f'Failed to update: {str(e)}'
                    })
                    print(f"Error updating item {item_id}: {e}")
            else:
                # Item level maintained
                updated_items.append({
                    'id': item_id,
                    'word_type': item_type,
                    'word': target_word,
                    'action': action,
                    'score': score,
                    'old_level': old_level,
                    'new_level': new_level,
                    'message': message
                })
        
        updated_count = len(updated_items)
        failed_count = len(failed_items)
        total_questions = len(processed_data['results'])
        
        # Count different types of changes
        increased = len([item for item in updated_items if item['action'] == 'increased_level'])
        decreased = len([item for item in updated_items if item['action'] == 'reduced_level'])
        maintained = len([item for item in updated_items if item['action'] in ['maintained_level', 'no_change']])
        
        return {
            'success': True,
            'message': f'Processed {total_questions} items: {increased} increased, {decreased} decreased, {maintained} maintained, {failed_count} failed',
            'changes': updated_items,  # Use 'changes' key for frontend compatibility
            'passed_items': updated_items,  # Keep for backward compatibility
            'failed_items': failed_items,
            'statistics': {
                'total_questions': total_questions,
                'updated_count': updated_count,
                'failed_count': failed_count,
                'increased_count': increased,
                'decreased_count': decreased,
                'maintained_count': maintained
            }
        }
    
    def get_item_by_id_and_type(self, item_id, item_type):
        """Get database item by ID and type"""
        if item_type == 'vocabulary':
            return db.session.get(VocabularyWord, item_id)
        elif item_type == 'phrasal_verb':
            return db.session.get(PhrasalVerb, item_id)
        elif item_type == 'idiom':
            return db.session.get(Idiom, item_id)
        return None

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
    """Unified test center - combines test taking and results evaluation in one interface"""
    return render_template('unified_test_center.html')

@app.route('/results')
def results():
    """Redirect to unified test center with evaluation mode"""
    test_type = request.args.get('type', 'regular')
    return redirect(url_for('test', evaluation=True, type=test_type))

@app.route('/test-center')
def test_center():
    """Alternative route name for the unified test center"""
    return render_template('unified_test_center.html')

@app.route('/api/evaluation', methods=['POST'])
def unified_evaluation_api():
    """
    Unified evaluation API that handles all evaluation types
    
    POST /api/evaluation - Process evaluation data
    
    Body:
    {
        "action": "process|update_mastery", 
        "data": {...evaluation data...},
        "threshold": 70 (optional, for mastery updates)
    }
    """
    try:
        request_data = request.get_json()
        action = request_data.get('action', 'process')
        evaluation_data = request_data.get('data', {})
        
        manager = UnifiedEvaluationManager()
        
        if action == 'process':
            # Process and standardize the evaluation data
            result = manager.process_evaluation_upload(evaluation_data)
            return jsonify(result)
            
        elif action == 'update_mastery':
            # Check if data is already processed or needs processing
            if evaluation_data.get('success') and evaluation_data.get('results'):
                # Data is already processed
                processed_data = evaluation_data
            else:
                # Data needs processing
                processed_data = manager.process_evaluation_upload(evaluation_data)
                
            if processed_data.get('success'):
                threshold = request_data.get('threshold', 7)
                update_result = manager.update_mastery_levels(processed_data, threshold)
                return jsonify(update_result)
            else:
                return jsonify(processed_data), 400
                
        else:
            return jsonify({
                'success': False,
                'message': f'Unsupported action: {action}'
            }), 400
            
    except Exception as e:
        print(f"Error in unified evaluation API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error processing evaluation: {str(e)}'
        }), 500

# Unified test functionality now handled directly by /test route

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

@app.route('/api/test', methods=['GET', 'POST'])
def unified_test_api():
    """
    Unified test API that handles all test types based on parameters
    
    GET /api/test?type=regular    - Generate regular test questions
    GET /api/test?type=mastery    - Generate mastery test questions  
    POST /api/test                - Submit test responses (test_type in body)
    
    Body for POST:
    {
        "test_type": "regular|mastery",
        "responses": [{"id": 1, "type": "vocabulary", "user_sentence": "..."}, ...]
    }
    """
    if request.method == 'GET':
        # Get test questions
        test_type = request.args.get('type', 'regular')  # regular or mastery
        
        try:
            manager = UnifiedTestManager(test_type)
            result = manager.generate_questions()
            return jsonify(result)
        except Exception as e:
            print(f"Error in unified test API: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': f'Error generating test: {str(e)}'}), 500
    
    elif request.method == 'POST':
        # Submit test responses
        data = request.get_json()
        test_type = data.get('test_type', 'regular')
        
        try:
            manager = UnifiedTestManager(test_type)
            result = manager.process_submission(data)
            return jsonify(result)
        except Exception as e:
            print(f"Error in unified test submission: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': f'Error submitting test: {str(e)}'}), 500

# Legacy endpoints removed - use unified /api/test endpoint instead

# Legacy endpoint removed - use /api/test with POST method instead

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
    """Legacy route - redirect to unified test system"""
    return redirect(url_for('test', type='mastery'))

@app.route('/submit-evaluation')
def submit_evaluation():
    """Legacy route - redirect to unified results system"""
    return redirect(url_for('results', type='mastery'))

# Legacy endpoint removed - use /api/test?type=mastery instead

# Legacy endpoint removed - use /api/test with POST method instead

# Legacy endpoint removed - use /api/evaluation instead

# All legacy routes consolidated into unified test and evaluation system


    
    # Calculate question counts based on available items (target: 10 questions for 10-minute test)
    target_questions = 10
    total_available = len(vocab_items) + len(phrasal_items) + len(idiom_items)
    
    if total_available == 0:
        return jsonify({
            'success': False,
            'message': 'No items with mastery level 2-4 found (excluding mastered items)'
        })
    
    # Use all available items if less than target, otherwise use proportional distribution
    actual_total = min(target_questions, total_available)
    
    # Calculate proportional counts based on available items
    idiom_count = min(len(idiom_items), max(1, int(actual_total * 0.4)) if len(idiom_items) > 0 else 0)
    vocab_count = min(len(vocab_items), max(1, int(actual_total * 0.3)) if len(vocab_items) > 0 else 0)
    
    # Remaining questions go to phrasal verbs, but don't exceed available
    remaining = actual_total - idiom_count - vocab_count
    phrasal_count = min(len(phrasal_items), max(0, remaining))
    
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

def submit_test_legacy():
    """Legacy implementation of submit_test"""
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

def get_mastered_test_questions_legacy():
    """Legacy implementation of get_mastered_test_questions"""
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

def submit_mastered_test_legacy():
    """Legacy implementation of submit_mastered_test"""
    data = request.get_json()
    responses = data.get('responses', [])
    
    # Create a comprehensive test result JSON
    test_result = {
        'test_metadata': {
            'test_date': datetime.utcnow().isoformat(),
            'test_type': 'sentence_writing_mastery_test',
            'total_questions': len(responses),
            'user_id': 'anonymous',
            'test_version': '1.0'
        },
        'questions_and_responses': []
    }
    
    # Process each response and add to result
    for response in responses:
        item_id = response.get('id')
        item_type = response.get('type')
        user_sentence = response.get('user_sentence', '')
        
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
                    'separable': getattr(item, 'separable', None),
                    'origin': getattr(item, 'origin', None)
                },
                'evaluation_criteria': {
                    'word_used_correctly': None,
                    'demonstrates_understanding': None,
                    'grammar_correct': None,
                    'creative_usage': None,
                    'overall_score': None,
                    'evaluator_comments': ''
                }
            }
            
            test_result['questions_and_responses'].append(question_response)
    
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
