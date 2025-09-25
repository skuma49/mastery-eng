# Mastery English

A comprehensive Flask web application for learning and practicing English vocabulary, phrasal verbs, and idioms with interactive flashcards.

## Features

### 📚 Three Categories of Learning
- **Vocabulary Words**: Store words with definitions, pronunciations, parts of speech, and example sentences
- **Phrasal Verbs**: Manage phrasal verbs with meanings, examples, and separability information
- **Idioms**: Collect idioms with meanings, examples, and historical origins

### 🎯 Interactive Flashcards
- Practice with randomized flashcard sessions
- Track your progress and mastery levels
- Self-assessment with "Got it" or "Need more practice" options
- Visual progress indicators

### 📊 Progress Tracking
- Monitor how many times each item has been practiced
- Mastery level system (0-5 scale)
- Practice statistics and date tracking
- Dashboard with recent additions and statistics

### 🔍 Search Functionality
- Search across all categories
- Find items by word, meaning, or example sentences
- Comprehensive search results with easy editing access

### 💻 Modern Interface
- Responsive design that works on desktop and mobile
- Bootstrap 5 styling with custom CSS
- Interactive modals for confirmations
- Clean, professional appearance

## Installation

1. **Clone or download the project**
2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open your browser** and go to `http://localhost:5000`

## Project Structure

```
mastery-eng/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── app.js        # JavaScript functionality
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Dashboard
    ├── add_vocabulary.html
    ├── vocabulary_list.html
    ├── edit_vocabulary.html
    ├── add_phrasal_verb.html
    ├── phrasal_verbs_list.html
    ├── edit_phrasal_verb.html
    ├── add_idiom.html
    ├── idioms_list.html
    ├── edit_idiom.html
    ├── flashcards_menu.html
    ├── flashcards_vocabulary.html
    ├── flashcards_phrasal.html
    ├── flashcards_idioms.html
    └── search_results.html
```

## Usage

### Adding Content
1. Use the navigation menu to access each category
2. Click "Add New" buttons to create vocabulary items
3. Fill in the required fields (marked with *)
4. Optional fields provide additional context and learning aids

### Practicing with Flashcards
1. Go to the Flashcards section from the main menu
2. Choose a category (Vocabulary, Phrasal Verbs, or Idioms)
3. Click on cards to reveal answers
4. Rate your knowledge after each card
5. Complete sessions to improve mastery levels

### Tracking Progress
- View your dashboard for overall statistics
- Check individual item mastery levels in list views
- Monitor recent additions and practice frequency

### Search and Organization
- Use the search bar in the navigation
- Browse paginated lists of all items
- Edit or delete items as needed
- Filter by difficulty levels

## Database

The application uses SQLite database with three main tables:
- `vocabulary_words`: Stores vocabulary with definitions and metadata
- `phrasal_verbs`: Stores phrasal verbs with meanings and separability info
- `idioms`: Stores idioms with meanings and origins

The database is automatically created when you first run the application.

## Customization

### Adding New Features
- Modify `models.py` to add new fields
- Update forms in templates
- Add corresponding routes in `app.py`

### Styling Changes
- Edit `static/css/style.css` for visual customizations
- Bootstrap 5 classes are used throughout templates

### Extending Functionality
- Add new categories by creating new models and routes
- Implement user authentication for multi-user support
- Add import/export functionality for vocabulary lists

## Technologies Used

- **Backend**: Python Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Database**: SQLite
- **Icons**: Font Awesome 6
- **Styling**: Custom CSS with Bootstrap components

## Future Enhancements

- Audio pronunciation support
- Spaced repetition algorithm
- Import/export functionality
- User accounts and progress sharing
- Mobile app version
- Advanced statistics and analytics

## License

This project is open source and available under the MIT License.

---

**Happy Learning! 📚✨**
