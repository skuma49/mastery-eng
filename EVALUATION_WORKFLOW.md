# Mastered Words Evaluation Workflow

## 📋 Complete Workflow Steps

### 1. **Take the Advanced Test**
- Navigate to `/mastered/test`
- Write creative sentences using your mastered words
- Submit the test to generate JSON results
- Download the JSON file for external evaluation

### 2. **External Evaluation Process**
The downloaded JSON contains:
```json
{
  "test_metadata": {
    "test_date": "2025-09-30T18:30:00.123456",
    "test_type": "sentence_writing_mastery_test",
    "total_questions": 10,
    "user_id": "anonymous",
    "test_version": "1.0"
  },
  "questions_and_responses": [
    {
      "question_id": 123,
      "word_type": "vocabulary",
      "target_word": "sophisticated",
      "user_sentence": "The sophisticated algorithm solved the complex problem efficiently.",
      "word_details": {
        "definition_or_meaning": "having great knowledge or experience",
        "part_of_speech": "adjective",
        "difficulty_level": "hard",
        "original_example": "She has sophisticated tastes in art.",
        "pronunciation": "/səˈfɪstɪkeɪtɪd/"
      },
      "evaluation_criteria": {
        "word_used_correctly": null,
        "demonstrates_understanding": null,
        "grammar_correct": null,
        "creative_usage": null,
        "overall_score": null,
        "evaluator_comments": ""
      }
    }
  ]
}
```

### 3. **Evaluation Criteria**
For each sentence, evaluate:

- **word_used_correctly**: `true/false` - Is the target word used correctly in context?
- **demonstrates_understanding**: `true/false` - Does the sentence show understanding of the word meaning?
- **grammar_correct**: `true/false` - Is the sentence grammatically correct?
- **creative_usage**: `true/false` - Is the usage creative and original?
- **overall_score**: `0-100` - Overall quality of the sentence (0=poor, 100=excellent)
- **evaluator_comments**: Optional feedback for the learner

### 4. **Return Evaluation Results**
Format the results as:
```json
{
  "evaluated_results": [
    {
      "question_id": 123,
      "word_type": "vocabulary",
      "evaluation_criteria": {
        "word_used_correctly": true,
        "demonstrates_understanding": true,
        "grammar_correct": true,
        "creative_usage": true,
        "overall_score": 85,
        "evaluator_comments": "Excellent usage with creative context"
      }
    }
  ]
}
```

### 5. **Submit Results Back to System**
- Navigate to `/submit-evaluation`
- Paste the evaluation results JSON
- Click "Submit Evaluation Results"
- System will automatically update mastery levels

### 6. **Automatic Mastery Updates**
- **Words that PASS** (score ≥ 70 AND word_used_correctly=true AND demonstrates_understanding=true):
  - Remain at mastery level 5
  - Stay in mastered section
- **Words that FAIL**:
  - Reset to mastery level 0
  - Reset practice counter to 0
  - Move back to practice mode

## 🔄 **API Endpoints**

### Test Submission
```http
POST /api/submit-mastered-test
Content-Type: application/json

{
  "responses": [
    {
      "id": 123,
      "type": "vocabulary",
      "word": "sophisticated",
      "user_sentence": "The sophisticated algorithm...",
      "question": "Write a creative sentence using 'sophisticated'",
      "instructions": "Create an original sentence..."
    }
  ]
}
```

### Evaluation Results Submission
```http
POST /api/submit-evaluation-results
Content-Type: application/json

{
  "evaluated_results": [
    {
      "question_id": 123,
      "word_type": "vocabulary",
      "evaluation_criteria": {
        "word_used_correctly": true,
        "demonstrates_understanding": true,
        "grammar_correct": true,
        "creative_usage": true,
        "overall_score": 85,
        "evaluator_comments": "Excellent usage"
      }
    }
  ]
}
```

## 🎯 **Scoring Guidelines**

### Overall Score Bands:
- **90-100**: Exceptional - Perfect usage, highly creative, excellent grammar
- **80-89**: Excellent - Correct usage, creative, good grammar
- **70-79**: Good - Correct usage, shows understanding, minor issues
- **60-69**: Fair - Mostly correct but some issues
- **0-59**: Poor - Incorrect usage or major problems

### Pass/Fail Criteria:
A word remains mastered only if:
1. `overall_score >= 70` AND
2. `word_used_correctly = true` AND  
3. `demonstrates_understanding = true`

If any of these conditions fail, the word is reset to practice mode.

## 🛠 **Integration Options**

### Manual Process
1. Download JSON from test
2. Manually evaluate each sentence
3. Create evaluation results JSON
4. Submit via web interface

### Automated Process
1. Download JSON from test
2. Send to AI evaluation service (ChatGPT, Claude, etc.)
3. Receive evaluation results
4. Submit via API endpoint

### Semi-Automated Process
1. Download JSON from test
2. Use AI for initial evaluation
3. Manual review and adjustment
4. Submit final results

## 📊 **Tracking & Analytics**

The system tracks:
- Test completion dates
- Evaluation scores per word
- Mastery level changes
- Practice counters reset
- Overall progress metrics

All data is stored in the SQLite database and can be viewed through the Progress and Mastered Words sections.
