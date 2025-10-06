/**
 * Unified Test Framework for Mastery English Application
 * 
 * This framework provides a common base for all test types with configuration-driven behavior.
 * Supports inheritance pattern and configurable test modes.
 */

class BaseTestManager {
    constructor(config = {}) {
        // Default configuration
        this.config = {
            testType: 'regular', // 'regular' or 'mastery'
            hasTimer: false,
            timerDuration: 600, // seconds
            questionsPerTest: 10,
            showExamples: true,
            showDefinitions: true,
            autoSave: true,
            keyboardNavigation: true,
            downloadFormat: 'json',
            ...config
        };
        
        // Test state
        this.questions = [];
        this.currentQuestionIndex = 0;
        this.responses = [];
        this.timer = null;
        this.timeRemaining = this.config.timerDuration;
        this.startTime = null;
        this.isTransitioning = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadQuestions();
    }
    
    bindEvents() {
        // Common event bindings
        this.bindElement('start-test', 'click', () => this.startTest());
        this.bindElement('next-btn', 'click', () => this.nextQuestion());
        this.bindElement('prev-btn', 'click', () => this.prevQuestion());
        this.bindElement('finish-btn', 'click', () => this.finishTest());
        this.bindElement('download-btn', 'click', () => this.downloadResults());
        
        if (this.config.autoSave) {
            this.bindElement('sentence-input', 'input', () => this.saveCurrentResponse());
        }
        
        if (this.config.keyboardNavigation) {
            document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        }
    }
    
    bindElement(id, event, handler) {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener(event, handler);
        }
    }
    
    handleKeyboard(e) {
        if (e.ctrlKey || e.metaKey) return;
        
        if (e.key === 'ArrowRight' && !document.getElementById('next-btn')?.disabled) {
            this.nextQuestion();
        } else if (e.key === 'ArrowLeft' && !document.getElementById('prev-btn')?.disabled) {
            this.prevQuestion();
        }
    }
    
    async loadQuestions() {
        try {
            const endpoint = this.getQuestionsEndpoint();
            const method = this.getQuestionsMethod();
            const fetchOptions = {
                method: method,
                headers: { 'Content-Type': 'application/json' }
            };
            
            const response = await fetch(endpoint, fetchOptions);
            
            const data = await response.json();
            
            if (data.success) {
                this.questions = data.questions;
                this.responses = new Array(this.questions.length).fill('');
                
                if (this.questions.length === 0) {
                    this.showNoQuestionsMessage();
                } else {
                    this.showPreTest();
                }
            } else {
                this.showError(data.message || 'Failed to load test questions');
            }
        } catch (error) {
            this.showError('Network error while loading test');
        }
    }
    
    // Abstract methods to be implemented by subclasses
    getQuestionsEndpoint() {
        throw new Error('getQuestionsEndpoint must be implemented by subclass');
    }
    
    getQuestionsMethod() {
        return 'POST';
    }
    
    getSubmitEndpoint() {
        throw new Error('getSubmitEndpoint must be implemented by subclass');
    }
    
    showNoQuestionsMessage() {
        const element = document.getElementById('loading-state');
        if (element) {
            element.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-exclamation-triangle text-warning mb-3" style="font-size: 3rem;"></i>
                    <h3>No Questions Available</h3>
                    <p class="text-muted">${this.getNoQuestionsMessage()}</p>
                    <a href="/flashcards" class="btn btn-primary">
                        <i class="fas fa-cards-blank"></i> Practice Flashcards
                    </a>
                </div>
            `;
        }
    }
    
    getNoQuestionsMessage() {
        return this.config.testType === 'mastery' 
            ? 'No mastered words found for testing. Master some words first!'
            : 'You need items with mastery level 2 or higher to take the test.';
    }
    
    showPreTest() {
        this.hideElement('loading-state');
        this.showElement('pre-test');
    }
    
    startTest() {
        this.startTime = new Date();
        this.currentQuestionIndex = 0;
        this.responses = new Array(this.questions.length).fill('');
        
        this.hideElement('pre-test');
        this.showElement('test-interface');
        
        if (this.config.hasTimer) {
            this.startTimer();
        }
        
        this.displayQuestion();
    }
    
    startTimer() {
        this.timer = setInterval(() => {
            this.timeRemaining--;
            this.updateTimerDisplay();
            
            if (this.timeRemaining <= 0) {
                this.finishTest();
            }
        }, 1000);
    }
    
    updateTimerDisplay() {
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        const timerElements = ['timer', 'timer-small'];
        timerElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.innerHTML = `<i class="fas fa-${this.timeRemaining <= 60 ? 'exclamation-triangle' : 'clock'}"></i> ${timeString}`;
                if (this.timeRemaining <= 60) {
                    element.className = element.className.replace('bg-primary bg-warning', 'bg-danger');
                }
            }
        });
    }
    
    displayQuestion() {
        if (this.currentQuestionIndex >= this.questions.length) {
            return;
        }
        
        const question = this.questions[this.currentQuestionIndex];
        this.updateProgress();
        this.updateNavigationButtons();
        this.renderQuestion(question);
        this.loadSavedResponse();
    }
    
    updateProgress() {
        const progress = ((this.currentQuestionIndex + 1) / this.questions.length) * 100;
        
        const progressBar = document.getElementById('progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        const counter = document.getElementById('question-counter');
        if (counter) {
            counter.textContent = `${this.currentQuestionIndex + 1} / ${this.questions.length}`;
        }
        
        const currentQuestion = document.getElementById('current-question');
        if (currentQuestion) {
            currentQuestion.textContent = this.currentQuestionIndex + 1;
        }
    }
    
    updateNavigationButtons() {
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const finishBtn = document.getElementById('finish-btn');
        
        if (prevBtn) {
            prevBtn.disabled = this.currentQuestionIndex === 0;
        }
        
        const isLastQuestion = this.currentQuestionIndex === this.questions.length - 1;
        
        if (nextBtn && finishBtn) {
            if (isLastQuestion) {
                nextBtn.style.display = 'none';
                finishBtn.style.display = 'inline-block';
            } else {
                nextBtn.style.display = 'inline-block';
                finishBtn.style.display = 'none';
            }
        }
    }
    
    renderQuestion(question) {
        // Update question type badge
        const badge = document.getElementById('question-type-badge');
        if (badge) {
            const typeText = this.getQuestionTypeText(question.type);
            const typeClass = this.getQuestionTypeClass(question.type);
            badge.textContent = typeText;
            badge.className = `badge ${typeClass} me-2`;
        }
        
        // Update question text
        const questionText = document.getElementById('question-text');
        if (questionText) {
            questionText.textContent = question.text || question.word;
        }
        
        // Update word highlight
        const wordHighlight = document.getElementById('word-highlight');
        if (wordHighlight) {
            wordHighlight.textContent = question.text || question.word;
        }
        
        // Show/hide example if configured
        if (this.config.showExamples && question.example) {
            this.showExample(question.example);
        } else {
            this.hideElement('question-example');
        }
        
        // Show additional context based on test type
        this.renderQuestionContext(question);
    }
    
    getQuestionTypeText(type) {
        const typeMap = {
            'vocabulary': 'Vocabulary',
            'phrasal_verb': 'Phrasal Verb',
            'idiom': 'Idiom'
        };
        return typeMap[type] || type.charAt(0).toUpperCase() + type.slice(1);
    }
    
    getQuestionTypeClass(type) {
        const classMap = {
            'vocabulary': 'bg-primary',
            'phrasal_verb': 'bg-success',
            'idiom': 'bg-info'
        };
        return classMap[type] || 'bg-secondary';
    }
    
    showExample(example) {
        const exampleElement = document.getElementById('example-text');
        const exampleContainer = document.getElementById('question-example');
        
        if (exampleElement && exampleContainer) {
            exampleElement.textContent = example;
            exampleContainer.style.display = 'block';
        }
    }
    
    renderQuestionContext(question) {
        // Override in subclasses for specific context rendering
    }
    
    loadSavedResponse() {
        const input = document.getElementById('sentence-input');
        if (input) {
            input.value = this.responses[this.currentQuestionIndex] || '';
        }
    }
    
    saveCurrentResponse() {
        if (this.isTransitioning) return;
        
        const input = document.getElementById('sentence-input');
        if (input) {
            this.responses[this.currentQuestionIndex] = input.value;
        }
    }
    
    nextQuestion() {
        if (this.currentQuestionIndex < this.questions.length - 1) {
            this.saveCurrentResponse();
            this.isTransitioning = true;
            this.currentQuestionIndex++;
            this.displayQuestion();
            this.isTransitioning = false;
        }
    }
    
    prevQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.saveCurrentResponse();
            this.isTransitioning = true;
            this.currentQuestionIndex--;
            this.displayQuestion();
            this.isTransitioning = false;
        }
    }
    
    async finishTest() {
        this.saveCurrentResponse();
        
        if (this.timer) {
            clearInterval(this.timer);
        }
        
        try {
            const testData = this.prepareSubmissionData();
            const response = await fetch(this.getSubmitEndpoint(), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(testData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showCompletion(data);
            } else {
                this.showError('Failed to submit test');
            }
        } catch (error) {
            this.showError('Network error while submitting test');
        }
    }
    
    prepareSubmissionData() {
        return {
            test_type: this.config.testType,
            responses: this.questions.map((question, index) => ({
                id: question.id,
                type: question.type,
                text: question.text || question.word,
                user_sentence: this.responses[index] || '',
                example_sentence: question.example || ''
            }))
        };
    }
    
    showCompletion(data) {
        this.hideElement('test-interface');
        this.showElement('test-complete');
        this.renderCompletion(data);
    }
    
    renderCompletion(data) {
        // Update completion statistics
        const totalAnswered = document.getElementById('total-answered');
        const timeTaken = document.getElementById('time-taken');
        
        if (totalAnswered) {
            const answered = this.responses.filter(r => r && r.trim()).length;
            totalAnswered.textContent = answered;
        }
        
        if (timeTaken && this.startTime) {
            const duration = Math.floor((new Date() - this.startTime) / 1000);
            const minutes = Math.floor(duration / 60);
            const seconds = duration % 60;
            timeTaken.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
        
        // Store result data for download
        this.resultData = data.result || data.test_result;
        this.downloadFilename = data.download_filename;
    }
    
    downloadResults() {
        if (this.resultData) {
            this.downloadJSON(this.resultData, this.downloadFilename);
        } else {
            alert('No results available for download');
        }
    }
    
    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || `test-results-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    // Utility methods
    showElement(id) {
        const element = document.getElementById(id);
        if (element) {
            element.style.display = 'block';
            element.classList.remove('d-none');
        }
    }
    
    hideElement(id) {
        const element = document.getElementById(id);
        if (element) {
            element.style.display = 'none';
            element.classList.add('d-none');
        }
    }
    
    showError(message) {
        const element = document.getElementById('loading-state');
        if (element) {
            element.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-exclamation-triangle text-danger mb-3" style="font-size: 3rem;"></i>
                    <h3>Error</h3>
                    <p class="text-muted">${message}</p>
                    <button onclick="location.reload()" class="btn btn-primary">
                        <i class="fas fa-redo"></i> Try Again
                    </button>
                </div>
            `;
        }
    }
}

/**
 * Regular Test Manager (10-minute timed test)
 * Extends BaseTestManager with timer functionality
 */
class RegularTestManager extends BaseTestManager {
    constructor(config = {}) {
        const regularConfig = {
            testType: 'regular',
            hasTimer: true,
            timerDuration: 600,
            questionsPerTest: 10,
            showExamples: true,
            showDefinitions: true,
            ...config
        };
        
        super(regularConfig);
    }
    
    getQuestionsEndpoint() {
        return `/api/test?type=${this.config.testType}`;
    }
    
    getQuestionsMethod() {
        return 'GET';
    }
    
    getSubmitEndpoint() {
        return '/api/test';
    }
}

/**
 * Mastery Test Manager (Advanced test for mastered words)
 * Extends BaseTestManager without timer, focuses on creativity
 */
class MasteryTestManager extends BaseTestManager {
    constructor(config = {}) {
        const masteryConfig = {
            testType: 'mastery',
            hasTimer: false,
            questionsPerTest: 10,
            showExamples: false,
            showDefinitions: false,
            ...config
        };
        
        super(masteryConfig);
    }
    
    getQuestionsEndpoint() {
        return `/api/test?type=${this.config.testType}`;
    }
    
    getQuestionsMethod() {
        return 'GET';
    }
    
    getSubmitEndpoint() {
        return '/api/test';
    }
    
    renderQuestionContext(question) {
        // For mastery tests, show additional context without giving away answers
        const contextElement = document.getElementById('question-context');
        if (contextElement && this.config.showDefinitions) {
            contextElement.innerHTML = `
                <div class="alert alert-info">
                    <small><strong>Type:</strong> ${this.getQuestionTypeText(question.type)}</small>
                </div>
            `;
        }
    }
    
    getNoQuestionsMessage() {
        return 'No mastered words found for testing. Master some words first by practicing with flashcards!';
    }
}

// Export for use in different contexts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BaseTestManager, RegularTestManager, MasteryTestManager };
}