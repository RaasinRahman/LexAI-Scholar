'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import {
  TrendingUp,
  TrendingDown,
  Award,
  Target,
  Clock,
  Calendar,
  BarChart3,
  AlertCircle,
  CheckCircle,
  Flame,
  Brain,
  Loader2
} from 'lucide-react';

interface ProgressMetrics {
  overview: {
    total_quizzes: number;
    total_questions_answered: number;
    total_correct_answers: number;
    overall_accuracy: number;
    average_score: number;
    median_score: number;
    days_active: number;
  };
  performance: {
    recent_average: number;
    improvement_trend: number;
    best_score: number;
    worst_score: number;
    consistency: number;
  };
  by_difficulty: {
    [key: string]: {
      quizzes_taken: number;
      accuracy: number;
    };
  };
  by_question_type: {
    [key: string]: {
      accuracy: number;
      questions_answered: number;
    };
  };
  time_stats: {
    total_time_spent_minutes: number;
    average_time_per_quiz_minutes: number;
  };
  learning_streak: {
    current: number;
    longest: number;
    last_activity?: string;
  };
  score_history: Array<{
    date: string;
    score: number;
    difficulty: string;
  }>;
  gaps?: {
    weak_topics: Array<{
      topic: string;
      accuracy: number;
      questions_answered: number;
    }>;
    weak_question_types: Array<{
      type: string;
      accuracy: number;
      questions_answered: number;
    }>;
    recommendations: Array<{
      area: string;
      accuracy?: number;
      suggestion: string;
      priority?: string;
    }>;
  };
}

export default function Analytics() {
  const { session } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<ProgressMetrics | null>(null);
  const [timePeriod, setTimePeriod] = useState<'7' | '30' | 'all'>('all');

  useEffect(() => {
    loadAnalytics();
  }, [timePeriod]);

  const loadAnalytics = async () => {
    if (!session?.access_token) return;

    setLoading(true);
    setError(null);

    try {
      const days = timePeriod === 'all' ? undefined : parseInt(timePeriod);
      const data = await api.getProgressAnalytics(session.access_token, days);
      
      if (data.success) {
        setMetrics(data);
      } else {
        setError(data.message || 'No analytics data available yet');
      }
    } catch (err: any) {
      setError(err.message || 'Error loading analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
        <span className="ml-3 text-gray-300">Loading analytics...</span>
      </div>
    );
  }

  if (error || !metrics || !metrics.overview || metrics.overview.total_quizzes === 0) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-12 text-center">
        <BarChart3 className="w-16 h-16 text-gray-500 mx-auto mb-4" />
        <h3 className="text-xl font-bold text-white mb-2">No Analytics Data Yet</h3>
        <p className="text-gray-400 mb-6">
          Complete some practice quizzes to see your progress and insights here.
        </p>
        <p className="text-sm text-gray-500">
          Your learning journey starts with your first quiz!
        </p>
      </div>
    );
  }

  const getPerformanceColor = (score: number) => {
    if (score >= 90) return 'text-green-400';
    if (score >= 80) return 'text-blue-400';
    if (score >= 70) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getPerformanceGrade = (score: number) => {
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  };

  // Safe accessors with defaults
  const overview = metrics?.overview || {};
  const performance = metrics?.performance || {};
  const learningStreak = metrics?.learning_streak || { current: 0, longest: 0 };
  const timeStats = metrics?.time_stats || { total_time_spent_minutes: 0, average_time_per_quiz_minutes: 0 };
  const byDifficulty = metrics?.by_difficulty || {};
  const byQuestionType = metrics?.by_question_type || {};
  const gaps = metrics?.gaps || { weak_topics: [], weak_question_types: [], recommendations: [] };
  const scoreHistory = metrics?.score_history || [];

  return (
    <div className="space-y-6">
      {/* Header with Time Period Filter */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-blue-400" />
            Learning Analytics
          </h2>
          <p className="text-gray-400 mt-1">Track your progress and identify areas for improvement</p>
        </div>
        
        <div className="flex gap-2">
          {(['7', '30', 'all'] as const).map(period => (
            <button
              key={period}
              onClick={() => setTimePeriod(period)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                timePeriod === period
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
              }`}
            >
              {period === 'all' ? 'All Time' : `${period} Days`}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Average Score */}
        <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border border-blue-700/50 rounded-lg p-6">
          <div className="flex items-start justify-between mb-2">
            <Target className="w-8 h-8 text-blue-400" />
            <span className={`text-3xl font-bold ${getPerformanceColor(overview.average_score || 0)}`}>
              {getPerformanceGrade(overview.average_score || 0)}
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Average Score</h3>
          <p className="text-2xl font-bold text-white">{(overview.average_score || 0).toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-2">
            {overview.total_quizzes || 0} quizzes completed
          </p>
        </div>

        {/* Learning Streak */}
        <div className="bg-gradient-to-br from-orange-900/50 to-red-800/30 border border-orange-700/50 rounded-lg p-6">
          <div className="flex items-start justify-between mb-2">
            <Flame className="w-8 h-8 text-orange-400" />
            <span className="text-2xl font-bold text-orange-400">🔥</span>
          </div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Current Streak</h3>
          <p className="text-2xl font-bold text-white">{learningStreak.current || 0} days</p>
          <p className="text-xs text-gray-500 mt-2">
            Longest: {learningStreak.longest || 0} days
          </p>
        </div>

        {/* Total Questions */}
        <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700/50 rounded-lg p-6">
          <div className="flex items-start justify-between mb-2">
            <Brain className="w-8 h-8 text-purple-400" />
            <CheckCircle className="w-6 h-6 text-purple-400" />
          </div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Questions Answered</h3>
          <p className="text-2xl font-bold text-white">{overview.total_questions_answered || 0}</p>
          <p className="text-xs text-gray-500 mt-2">
            {overview.total_correct_answers || 0} correct ({(overview.overall_accuracy || 0).toFixed(1)}%)
          </p>
        </div>

        {/* Time Spent */}
        <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 border border-green-700/50 rounded-lg p-6">
          <div className="flex items-start justify-between mb-2">
            <Clock className="w-8 h-8 text-green-400" />
            <Calendar className="w-6 h-6 text-green-400" />
          </div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Study Time</h3>
          <p className="text-2xl font-bold text-white">
            {(timeStats.total_time_spent_minutes || 0).toFixed(0)} min
          </p>
          <p className="text-xs text-gray-500 mt-2">
            Avg: {(timeStats.average_time_per_quiz_minutes || 0).toFixed(1)} min/quiz
          </p>
        </div>
      </div>

      {/* Performance Trends */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          {(performance.improvement_trend || 0) > 0 ? (
            <TrendingUp className="w-5 h-5 text-green-400" />
          ) : (
            <TrendingDown className="w-5 h-5 text-red-400" />
          )}
          Performance Trends
        </h3>

        <div className="grid md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-400 mb-1">Recent Average</p>
            <p className={`text-2xl font-bold ${getPerformanceColor(performance.recent_average || 0)}`}>
              {(performance.recent_average || 0).toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">Last 5 quizzes</p>
          </div>

          <div>
            <p className="text-sm text-gray-400 mb-1">Improvement</p>
            <p className={`text-2xl font-bold ${
              (performance.improvement_trend || 0) > 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {(performance.improvement_trend || 0) > 0 ? '+' : ''}
              {(performance.improvement_trend || 0).toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">First half vs second half</p>
          </div>

          <div>
            <p className="text-sm text-gray-400 mb-1">Best Score</p>
            <p className={`text-2xl font-bold ${getPerformanceColor(performance.best_score || 0)}`}>
              {(performance.best_score || 0).toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Lowest: {(performance.worst_score || 0).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Performance by Difficulty and Question Type */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* By Difficulty */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Performance by Difficulty</h3>
          
          <div className="space-y-4">
            {Object.entries(byDifficulty).map(([difficulty, stats]) => (
              <div key={difficulty}>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-300 capitalize">{difficulty}</span>
                  <span className={`text-sm font-bold ${getPerformanceColor(stats.accuracy)}`}>
                    {stats.accuracy.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      stats.accuracy >= 80 ? 'bg-green-500' :
                      stats.accuracy >= 70 ? 'bg-blue-500' :
                      stats.accuracy >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${stats.accuracy}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {stats.quizzes_taken} quizzes
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* By Question Type */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Performance by Question Type</h3>
          
          <div className="space-y-4">
            {Object.entries(byQuestionType).map(([type, stats]) => (
              <div key={type}>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-300 capitalize">
                    {type.replace('_', ' ')}
                  </span>
                  <span className={`text-sm font-bold ${getPerformanceColor(stats.accuracy)}`}>
                    {stats.accuracy.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      stats.accuracy >= 80 ? 'bg-green-500' :
                      stats.accuracy >= 70 ? 'bg-blue-500' :
                      stats.accuracy >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${stats.accuracy}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {stats.questions_answered} questions
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Knowledge Gaps & Recommendations */}
      {(gaps.weak_topics.length > 0 || gaps.weak_question_types.length > 0) && (
        <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-6">
          <h3 className="text-lg font-bold text-yellow-400 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Areas for Improvement
          </h3>

          {gaps.weak_topics.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-300 mb-2">Weak Topics:</h4>
              <div className="flex flex-wrap gap-2">
                {gaps.weak_topics.map((topic, idx) => (
                  <div key={idx} className="bg-yellow-900/30 px-3 py-1 rounded-full">
                    <span className="text-sm text-yellow-300">{topic.topic}</span>
                    <span className="text-xs text-gray-400 ml-2">({topic.accuracy.toFixed(0)}%)</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {gaps.weak_question_types.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-300 mb-2">Question Types to Practice:</h4>
              <div className="flex flex-wrap gap-2">
                {gaps.weak_question_types.map((type, idx) => (
                  <div key={idx} className="bg-orange-900/30 px-3 py-1 rounded-full">
                    <span className="text-sm text-orange-300 capitalize">{type.type.replace('_', ' ')}</span>
                    <span className="text-xs text-gray-400 ml-2">({type.accuracy.toFixed(0)}%)</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {gaps.recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-2">Recommendations:</h4>
              <ul className="space-y-2">
                {gaps.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                    <span>{rec.suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Score History */}
      {scoreHistory.length > 0 && (
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Recent Quiz Scores</h3>
          
          <div className="space-y-2">
            {scoreHistory.slice(-10).reverse().map((score, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold ${
                    score.score >= 90 ? 'bg-green-900/50 text-green-400' :
                    score.score >= 80 ? 'bg-blue-900/50 text-blue-400' :
                    score.score >= 70 ? 'bg-yellow-900/50 text-yellow-400' :
                    'bg-red-900/50 text-red-400'
                  }`}>
                    {score.score.toFixed(0)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">
                      {new Date(score.date).toLocaleDateString()}
                    </p>
                    <p className="text-xs text-gray-400 capitalize">{score.difficulty} difficulty</p>
                  </div>
                </div>
                <Award className={`w-5 h-5 ${
                  score.score >= 90 ? 'text-yellow-400' : 'text-gray-600'
                }`} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

