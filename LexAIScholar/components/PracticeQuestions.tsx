'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api, Document } from '@/lib/api';
import { 
  BookOpen, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Loader2,
  Award,
  TrendingUp,
  FileText,
  Plus,
  Play,
  RotateCcw,
  ChevronRight,
  ChevronLeft
} from 'lucide-react';

interface Question {
  id: number;
  type: 'multiple_choice' | 'short_answer' | 'true_false';
  question: string;
  options?: { [key: string]: string };
  correct_answer: any;
  explanation: string;
  difficulty: string;
  topic?: string;
  document_id?: string;
  document_name?: string;
}

interface QuizSession {
  questions: Question[];
  currentQuestionIndex: number;
  answers: { [key: number]: any };
  evaluations: { [key: number]: any };
  startTime: Date;
  isComplete: boolean;
}

export default function PracticeQuestions() {
  const { session } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Quiz generation settings
  const [questionCount, setQuestionCount] = useState(5);
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [questionTypes, setQuestionTypes] = useState<string[]>([
    'multiple_choice',
    'short_answer',
    'true_false'
  ]);
  
  // Quiz session state
  const [quizSession, setQuizSession] = useState<QuizSession | null>(null);
  const [currentAnswer, setCurrentAnswer] = useState<any>('');
  const [evaluating, setEvaluating] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    if (!session?.access_token) return;
    
    try {
      const docs = await api.getDocuments(session.access_token);
      setDocuments(docs);
    } catch (err: any) {
      console.error('Error loading documents:', err);
    }
  };

  const toggleDocumentSelection = (docId: string) => {
    setSelectedDocuments(prev => 
      prev.includes(docId)
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };

  const toggleQuestionType = (type: string) => {
    setQuestionTypes(prev => 
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const generateQuiz = async () => {
    if (!session?.access_token) return;
    if (selectedDocuments.length === 0) {
      setError('Please select at least one document');
      return;
    }
    if (questionTypes.length === 0) {
      setError('Please select at least one question type');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = selectedDocuments.length === 1
        ? await api.generatePracticeQuestions(
            selectedDocuments[0],
            session.access_token,
            {
              questionCount,
              questionTypes,
              difficulty
            }
          )
        : await api.generateQuiz(
            selectedDocuments,
            'Practice Quiz',
            session.access_token,
            {
              questionCount,
              questionTypes,
              difficulty
            }
          );

      if (result.success) {
        setQuizSession({
          questions: result.questions,
          currentQuestionIndex: 0,
          answers: {},
          evaluations: {},
          startTime: new Date(),
          isComplete: false
        });
      } else {
        setError(result.error || 'Failed to generate quiz');
      }
    } catch (err: any) {
      setError(err.message || 'Error generating quiz');
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!session?.access_token || !quizSession) return;
    
    const currentQuestion = quizSession.questions[quizSession.currentQuestionIndex];
    
    // Validate answer
    if (currentAnswer === '' || currentAnswer === null || currentAnswer === undefined) {
      setError('Please provide an answer');
      return;
    }

    setEvaluating(true);
    setError(null);

    try {
      const evaluation = await api.evaluateAnswer(
        currentQuestion,
        currentAnswer,
        session.access_token
      );

      // Store answer and evaluation
      setQuizSession(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          answers: {
            ...prev.answers,
            [currentQuestion.id]: currentAnswer
          },
          evaluations: {
            ...prev.evaluations,
            [currentQuestion.id]: evaluation
          }
        };
      });

      setShowExplanation(true);
    } catch (err: any) {
      setError(err.message || 'Error evaluating answer');
    } finally {
      setEvaluating(false);
    }
  };

  const nextQuestion = async () => {
    if (!quizSession) return;
    
    if (quizSession.currentQuestionIndex < quizSession.questions.length - 1) {
      const nextIndex = quizSession.currentQuestionIndex + 1;
      setQuizSession(prev => prev ? { ...prev, currentQuestionIndex: nextIndex } : null);
      setCurrentAnswer('');
      setShowExplanation(false);
      setError(null);
    } else {
      // Quiz complete - save results to backend
      setQuizSession(prev => prev ? { ...prev, isComplete: true } : null);
      await saveQuizResults();
    }
  };

  const saveQuizResults = async () => {
    if (!session?.access_token || !quizSession) return;
    
    try {
      // Calculate performance metrics
      const { score, total } = calculateScore();
      
      // Calculate performance by question type
      const performanceByType: { [key: string]: { correct: number; total: number } } = {};
      
      quizSession.questions.forEach((question) => {
        const evaluation = quizSession.evaluations[question.id];
        const qType = question.type;
        
        if (!performanceByType[qType]) {
          performanceByType[qType] = { correct: 0, total: 0 };
        }
        
        performanceByType[qType].total++;
        if (evaluation?.is_correct) {
          performanceByType[qType].correct++;
        }
      });
      
      // Extract unique document IDs from questions
      const documentIds = Array.from(
        new Set(
          quizSession.questions
            .map(q => q.document_id)
            .filter((id): id is string => id !== undefined)
        )
      );
      
      // Extract topics from questions
      const topics = Array.from(
        new Set(
          quizSession.questions
            .map(q => q.topic)
            .filter((topic): topic is string => topic !== undefined && topic !== '')
        )
      );
      
      // Save to backend
      await api.recordQuizSession({
        documentIds: documentIds,
        totalQuestions: total,
        correctAnswers: score,
        difficulty: difficulty,
        questionTypes: questionTypes,
        startTime: quizSession.startTime.toISOString(),
        endTime: new Date().toISOString(),
        performanceByType: performanceByType,
        topicsCovered: topics
      }, session.access_token);
      
      console.log('[QUIZ] Results saved successfully');
    } catch (err: any) {
      console.error('[QUIZ] Error saving results:', err);
      // Don't show error to user, just log it
    }
  };

  const previousQuestion = () => {
    if (!quizSession) return;
    
    if (quizSession.currentQuestionIndex > 0) {
      const prevIndex = quizSession.currentQuestionIndex - 1;
      setQuizSession(prev => prev ? { ...prev, currentQuestionIndex: prevIndex } : null);
      const prevQuestion = quizSession.questions[prevIndex];
      setCurrentAnswer(quizSession.answers[prevQuestion.id] || '');
      setShowExplanation(!!quizSession.evaluations[prevQuestion.id]);
      setError(null);
    }
  };

  const resetQuiz = () => {
    setQuizSession(null);
    setCurrentAnswer('');
    setShowExplanation(false);
    setError(null);
  };

  const calculateScore = (): { score: number; total: number; percentage: number } => {
    if (!quizSession) return { score: 0, total: 0, percentage: 0 };
    
    let score = 0;
    const total = quizSession.questions.length;
    
    Object.values(quizSession.evaluations).forEach((evaluation: any) => {
      if (evaluation.is_correct) {
        score++;
      }
    });
    
    const percentage = total > 0 ? (score / total) * 100 : 0;
    return { score, total, percentage };
  };

  // Render quiz setup view
  if (!quizSession) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 border border-purple-700/50 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-2">
            <BookOpen className="w-8 h-8 text-purple-400" />
            <h2 className="text-2xl font-bold text-white">Practice Questions Generator</h2>
          </div>
          <p className="text-gray-300">
            Generate custom practice questions from your documents to test your knowledge and reinforce learning.
          </p>
        </div>

        {/* Document Selection */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            Select Documents
          </h3>
          
          {documents.length === 0 ? (
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-yellow-400 mx-auto mb-3" />
              <p className="text-gray-400">No documents uploaded yet. Upload documents to generate practice questions.</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-3">
              {documents.map(doc => (
                <div
                  key={doc.id}
                  onClick={() => toggleDocumentSelection(doc.id)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedDocuments.includes(doc.id)
                      ? 'border-blue-500 bg-blue-900/30'
                      : 'border-slate-600 bg-slate-800/30 hover:border-slate-500'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="text-white font-medium mb-1">{doc.filename}</h4>
                      {doc.title && <p className="text-sm text-gray-400 mb-1">{doc.title}</p>}
                      <p className="text-xs text-gray-500">{doc.page_count} pages • {doc.chunk_count} chunks</p>
                    </div>
                    {selectedDocuments.includes(doc.id) && (
                      <CheckCircle className="w-5 h-5 text-blue-400 flex-shrink-0" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quiz Settings */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Quiz Settings</h3>
          
          <div className="space-y-4">
            {/* Question Count */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Number of Questions: {questionCount}
              </label>
              <input
                type="range"
                min="3"
                max="20"
                value={questionCount}
                onChange={(e) => setQuestionCount(parseInt(e.target.value))}
                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>3</span>
                <span>20</span>
              </div>
            </div>

            {/* Difficulty */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Difficulty Level</label>
              <div className="flex gap-2">
                {(['easy', 'medium', 'hard'] as const).map(level => (
                  <button
                    key={level}
                    onClick={() => setDifficulty(level)}
                    className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                      difficulty === level
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                    }`}
                  >
                    {level.charAt(0).toUpperCase() + level.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Question Types */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Question Types</label>
              <div className="space-y-2">
                {[
                  { value: 'multiple_choice', label: 'Multiple Choice' },
                  { value: 'short_answer', label: 'Short Answer' },
                  { value: 'true_false', label: 'True/False' }
                ].map(type => (
                  <label key={type.value} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={questionTypes.includes(type.value)}
                      onChange={() => toggleQuestionType(type.value)}
                      className="w-4 h-4 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500"
                    />
                    <span className="text-gray-300">{type.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 flex items-start gap-3">
            <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {/* Generate Button */}
        <button
          onClick={generateQuiz}
          disabled={loading || selectedDocuments.length === 0}
          className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold py-4 px-6 rounded-lg transition-all flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Generating Questions...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Generate Practice Quiz
            </>
          )}
        </button>
      </div>
    );
  }

  // Render quiz results
  if (quizSession.isComplete) {
    const { score, total, percentage } = calculateScore();
    
    return (
      <div className="space-y-6">
        {/* Results Header */}
        <div className="bg-gradient-to-r from-green-900/50 to-blue-900/50 border border-green-700/50 rounded-lg p-8 text-center">
          <Award className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-white mb-2">Quiz Complete!</h2>
          <p className="text-gray-300 text-lg mb-6">Here's how you did:</p>
          
          <div className="flex justify-center items-baseline gap-2 mb-4">
            <span className="text-6xl font-bold text-white">{percentage.toFixed(0)}%</span>
          </div>
          
          <p className="text-xl text-gray-300">
            {score} out of {total} correct
          </p>
          
          {/* Performance Message */}
          <div className="mt-6 p-4 bg-slate-800/50 rounded-lg">
            <p className="text-gray-300">
              {percentage >= 90 ? '🎉 Outstanding! You have excellent mastery of the material.' :
               percentage >= 80 ? '✨ Great job! You have a strong understanding.' :
               percentage >= 70 ? '👍 Good work! Keep practicing to improve further.' :
               percentage >= 60 ? '📚 Not bad! Review the material and try again.' :
               '💪 Keep studying! Practice makes perfect.'}
            </p>
          </div>
        </div>

        {/* Question Review */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Review Your Answers</h3>
          
          <div className="space-y-4">
            {quizSession.questions.map((question, idx) => {
              const evaluation = quizSession.evaluations[question.id];
              const isCorrect = evaluation?.is_correct;
              
              return (
                <div
                  key={question.id}
                  className={`p-4 rounded-lg border-2 ${
                    isCorrect
                      ? 'border-green-600 bg-green-900/20'
                      : 'border-red-600 bg-red-900/20'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {isCorrect ? (
                      <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className="text-white font-medium mb-2">
                        {idx + 1}. {question.question}
                      </p>
                      <p className="text-sm text-gray-400 mb-1">
                        Your answer: <span className="text-white">{String(quizSession.answers[question.id])}</span>
                      </p>
                      {!isCorrect && (
                        <p className="text-sm text-gray-400 mb-2">
                          Correct answer: <span className="text-green-400">{String(question.correct_answer)}</span>
                        </p>
                      )}
                      <p className="text-sm text-gray-300 mt-2">{evaluation?.feedback || question.explanation}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button
            onClick={resetQuiz}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2"
          >
            <RotateCcw className="w-5 h-5" />
            Take Another Quiz
          </button>
        </div>
      </div>
    );
  }

  // Render active quiz question
  const currentQuestion = quizSession.questions[quizSession.currentQuestionIndex];
  const currentEvaluation = quizSession.evaluations[currentQuestion.id];
  const progress = ((quizSession.currentQuestionIndex + 1) / quizSession.questions.length) * 100;

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-300">
            Question {quizSession.currentQuestionIndex + 1} of {quizSession.questions.length}
          </span>
          <span className="text-sm text-gray-400">{progress.toFixed(0)}% Complete</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Question Card */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
        {/* Question Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                currentQuestion.difficulty === 'easy' ? 'bg-green-900/50 text-green-300' :
                currentQuestion.difficulty === 'hard' ? 'bg-red-900/50 text-red-300' :
                'bg-yellow-900/50 text-yellow-300'
              }`}>
                {currentQuestion.difficulty}
              </span>
              <span className="px-2 py-1 rounded text-xs font-medium bg-blue-900/50 text-blue-300">
                {currentQuestion.type.replace('_', ' ')}
              </span>
            </div>
            <h3 className="text-xl font-bold text-white">{currentQuestion.question}</h3>
            {currentQuestion.document_name && (
              <p className="text-sm text-gray-400 mt-2">From: {currentQuestion.document_name}</p>
            )}
          </div>
        </div>

        {/* Answer Input */}
        {!showExplanation && (
          <div className="mt-6">
            {currentQuestion.type === 'multiple_choice' && currentQuestion.options && (
              <div className="space-y-3">
                {Object.entries(currentQuestion.options).map(([key, value]) => (
                  <label
                    key={key}
                    className={`block p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      currentAnswer === key
                        ? 'border-blue-500 bg-blue-900/30'
                        : 'border-slate-600 bg-slate-800/30 hover:border-slate-500'
                    }`}
                  >
                    <input
                      type="radio"
                      name="answer"
                      value={key}
                      checked={currentAnswer === key}
                      onChange={(e) => setCurrentAnswer(e.target.value)}
                      className="sr-only"
                    />
                    <div className="flex items-center gap-3">
                      <span className="flex-shrink-0 w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold text-white">
                        {key}
                      </span>
                      <span className="text-gray-300">{value}</span>
                    </div>
                  </label>
                ))}
              </div>
            )}

            {currentQuestion.type === 'true_false' && (
              <div className="flex gap-4">
                <button
                  onClick={() => setCurrentAnswer(true)}
                  className={`flex-1 py-4 px-6 rounded-lg border-2 font-bold transition-all ${
                    currentAnswer === true
                      ? 'border-green-500 bg-green-900/30 text-white'
                      : 'border-slate-600 bg-slate-800/30 text-gray-300 hover:border-slate-500'
                  }`}
                >
                  True
                </button>
                <button
                  onClick={() => setCurrentAnswer(false)}
                  className={`flex-1 py-4 px-6 rounded-lg border-2 font-bold transition-all ${
                    currentAnswer === false
                      ? 'border-red-500 bg-red-900/30 text-white'
                      : 'border-slate-600 bg-slate-800/30 text-gray-300 hover:border-slate-500'
                  }`}
                >
                  False
                </button>
              </div>
            )}

            {currentQuestion.type === 'short_answer' && (
              <textarea
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                placeholder="Type your answer here (2-3 sentences)..."
                rows={4}
                className="w-full bg-slate-900/50 border border-slate-600 rounded-lg p-4 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
            )}
          </div>
        )}

        {/* Evaluation Result */}
        {showExplanation && currentEvaluation && (
          <div className={`mt-6 p-4 rounded-lg border-2 ${
            currentEvaluation.is_correct
              ? 'border-green-600 bg-green-900/20'
              : 'border-red-600 bg-red-900/20'
          }`}>
            <div className="flex items-start gap-3 mb-3">
              {currentEvaluation.is_correct ? (
                <>
                  <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0" />
                  <div>
                    <h4 className="text-lg font-bold text-green-400 mb-1">Correct!</h4>
                    <p className="text-gray-300">{currentEvaluation.feedback}</p>
                  </div>
                </>
              ) : (
                <>
                  <XCircle className="w-6 h-6 text-red-400 flex-shrink-0" />
                  <div>
                    <h4 className="text-lg font-bold text-red-400 mb-1">Incorrect</h4>
                    <p className="text-gray-300 mb-2">{currentEvaluation.feedback}</p>
                    <p className="text-sm text-gray-400">
                      Correct answer: <span className="text-white font-medium">{String(currentQuestion.correct_answer)}</span>
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mt-4 bg-red-900/30 border border-red-700 rounded-lg p-3 flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 mt-6">
          <button
            onClick={previousQuestion}
            disabled={quizSession.currentQuestionIndex === 0}
            className="px-6 py-3 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:text-gray-600 text-white rounded-lg font-medium transition-all flex items-center gap-2"
          >
            <ChevronLeft className="w-5 h-5" />
            Previous
          </button>

          {!showExplanation ? (
            <button
              onClick={submitAnswer}
              disabled={evaluating || currentAnswer === '' || currentAnswer === null}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-bold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2"
            >
              {evaluating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Evaluating...
                </>
              ) : (
                <>
                  <CheckCircle className="w-5 h-5" />
                  Submit Answer
                </>
              )}
            </button>
          ) : (
            <button
              onClick={nextQuestion}
              className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2"
            >
              {quizSession.currentQuestionIndex === quizSession.questions.length - 1 ? (
                <>
                  <Award className="w-5 h-5" />
                  Finish Quiz
                </>
              ) : (
                <>
                  Next Question
                  <ChevronRight className="w-5 h-5" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

