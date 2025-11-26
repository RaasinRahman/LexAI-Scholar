'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import {
  Calendar,
  Clock,
  BookOpen,
  CheckCircle,
  Target,
  Lightbulb,
  Zap,
  Award,
  TrendingUp,
  Loader2,
  AlertCircle,
  Play,
  Moon,
  Sun,
  Flame
} from 'lucide-react';

interface DailyTask {
  day: number;
  title: string;
  focus: string;
  tasks: Array<{
    activity: string;
    duration_minutes: number;
    description: string;
    type: string;
    recommendation?: {
      document_id?: string;
      question_count?: number;
      difficulty?: string;
      question_types?: string[];
    };
  }>;
  goal: string;
  total_time_minutes: number;
  completed?: boolean;
}

interface StudyPlan {
  plan_overview: {
    duration_days: number;
    focus_areas: string[];
    expected_outcome: string;
  };
  daily_tasks: DailyTask[];
  weekly_goals: string[];
  tips: string[];
  progress_milestones?: Array<{
    day: number;
    milestone: string;
    action: string;
  }>;
  generated_at: string;
  time_commitment: string;
  user_level: string;
}

interface Recommendation {
  type: string;
  priority: string;
  title: string;
  message: string;
  action: string;
}

export default function StudyPlan() {
  const { session } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [studyPlan, setStudyPlan] = useState<StudyPlan | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [timeCommitment, setTimeCommitment] = useState<'light' | 'moderate' | 'intensive'>('moderate');
  const [currentDay, setCurrentDay] = useState(1);
  const [showGoalsForm, setShowGoalsForm] = useState(false);
  const [goals, setGoals] = useState({
    targetScore: '',
    examDate: '',
    focusAreas: ''
  });

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    if (!session?.access_token) return;

    try {
      const data = await api.getQuickRecommendations(session.access_token);
      if (data.success) {
        setRecommendations(data.recommendations || []);
      }
    } catch (err: any) {
      console.error('Error loading recommendations:', err);
    }
  };

  const generatePlan = async () => {
    if (!session?.access_token) return;

    setLoading(true);
    setError(null);

    try {
      const goalsData = {
        target_score: goals.targetScore ? parseInt(goals.targetScore) : undefined,
        exam_date: goals.examDate || undefined,
        focus_areas: goals.focusAreas ? goals.focusAreas.split(',').map(a => a.trim()) : undefined
      };

      const data = await api.generateStudyPlan(session.access_token, {
        timeCommitment,
        goals: Object.values(goalsData).some(v => v) ? goalsData : undefined
      });

      if (data.success) {
        setStudyPlan(data.study_plan);
        setCurrentDay(1);
      } else {
        setError(data.error || 'Failed to generate study plan');
      }
    } catch (err: any) {
      setError(err.message || 'Error generating study plan');
    } finally {
      setLoading(false);
    }
  };

  const markDayComplete = (day: number) => {
    if (!studyPlan) return;
    
    const updatedPlan = { ...studyPlan };
    const dayTask = updatedPlan.daily_tasks.find(t => t.day === day);
    if (dayTask) {
      dayTask.completed = !dayTask.completed;
      setStudyPlan(updatedPlan);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-red-500 bg-red-900/20';
      case 'medium': return 'border-yellow-500 bg-yellow-900/20';
      case 'low': return 'border-green-500 bg-green-900/20';
      default: return 'border-blue-500 bg-blue-900/20';
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-600 text-white';
      case 'medium': return 'bg-yellow-600 text-white';
      case 'low': return 'bg-green-600 text-white';
      default: return 'bg-blue-600 text-white';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'reading': return <BookOpen className="w-5 h-5" />;
      case 'practice': return <Target className="w-5 h-5" />;
      case 'review': return <TrendingUp className="w-5 h-5" />;
      default: return <Zap className="w-5 h-5" />;
    }
  };

  if (!studyPlan) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 border border-purple-700/50 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-2">
            <Calendar className="w-8 h-8 text-purple-400" />
            <h2 className="text-2xl font-bold text-white">Personalized Study Plan</h2>
          </div>
          <p className="text-gray-300">
            Get an AI-powered study plan tailored to your performance and goals.
          </p>
        </div>

        {/* Quick Recommendations */}
        {recommendations.length > 0 && (
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-yellow-400" />
              Quick Recommendations
            </h3>
            
            <div className="space-y-3">
              {recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  className={`border-l-4 ${getPriorityColor(rec.priority)} rounded-lg p-4`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium text-white">{rec.title}</h4>
                    <span className={`text-xs px-2 py-1 rounded-full ${getPriorityBadge(rec.priority)}`}>
                      {rec.priority}
                    </span>
                  </div>
                  <p className="text-sm text-gray-300 mb-2">{rec.message}</p>
                  <p className="text-sm text-blue-400 flex items-center gap-1">
                    <Zap className="w-4 h-4" />
                    {rec.action}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Study Plan Configuration */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Generate Your Study Plan</h3>
          
          {/* Time Commitment */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Time Commitment
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { value: 'light' as const, label: 'Light', time: '15-20 min/day', Icon: Moon },
                { value: 'moderate' as const, label: 'Moderate', time: '30-45 min/day', Icon: Sun },
                { value: 'intensive' as const, label: 'Intensive', time: '1-2 hours/day', Icon: Flame }
              ].map(option => (
                <button
                  key={option.value}
                  onClick={() => setTimeCommitment(option.value)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    timeCommitment === option.value
                      ? 'border-blue-500 bg-blue-900/30'
                      : 'border-slate-600 bg-slate-800/30 hover:border-slate-500'
                  }`}
                >
                  <div className="flex justify-center mb-2">
                    <option.Icon className="w-8 h-8 text-blue-400" />
                  </div>
                  <div className="font-medium text-white mb-1">{option.label}</div>
                  <div className="text-xs text-gray-400">{option.time}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Goals (Optional) */}
          <div className="mb-6">
            <button
              onClick={() => setShowGoalsForm(!showGoalsForm)}
              className="text-sm font-medium text-blue-400 hover:text-blue-300 mb-3"
            >
              {showGoalsForm ? '- Hide' : '+ Add'} Goals (Optional)
            </button>
            
            {showGoalsForm && (
              <div className="space-y-3 p-4 bg-slate-900/50 rounded-lg">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Target Score (%)</label>
                  <input
                    type="number"
                    value={goals.targetScore}
                    onChange={(e) => setGoals({ ...goals, targetScore: e.target.value })}
                    placeholder="e.g., 85"
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg p-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Exam/Deadline Date</label>
                  <input
                    type="date"
                    value={goals.examDate}
                    onChange={(e) => setGoals({ ...goals, examDate: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg p-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Focus Areas (comma-separated)</label>
                  <input
                    type="text"
                    value={goals.focusAreas}
                    onChange={(e) => setGoals({ ...goals, focusAreas: e.target.value })}
                    placeholder="e.g., Contract Law, Torts, Criminal Law"
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg p-2 text-white"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 bg-red-900/30 border border-red-700 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          )}

          {/* Generate Button */}
          <button
            onClick={generatePlan}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold py-4 px-6 rounded-lg transition-all flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating Your Study Plan...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Generate Study Plan
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  const completedDays = studyPlan.daily_tasks.filter(t => t.completed).length;
  const progressPercentage = (completedDays / studyPlan.daily_tasks.length) * 100;
  const currentTask = studyPlan.daily_tasks.find(t => t.day === currentDay);

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 border border-purple-700/50 rounded-lg p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Your 7-Day Study Plan</h2>
            <p className="text-gray-300">{studyPlan.plan_overview.expected_outcome}</p>
            <div className="flex items-center gap-4 mt-3">
              <span className="text-sm text-gray-400">
                Level: <span className="text-blue-400 capitalize">{studyPlan.user_level}</span>
              </span>
              <span className="text-sm text-gray-400">
                Commitment: <span className="text-purple-400 capitalize">{studyPlan.time_commitment}</span>
              </span>
            </div>
          </div>
          <button
            onClick={() => setStudyPlan(null)}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm"
          >
            New Plan
          </button>
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-300">
              Progress: {completedDays}/{studyPlan.daily_tasks.length} days
            </span>
            <span className="text-sm text-gray-400">{progressPercentage.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      </div>

      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
        <h3 className="text-sm font-medium text-gray-400 mb-3">Focus Areas</h3>
        <div className="flex flex-wrap gap-2">
          {studyPlan.plan_overview.focus_areas.map((area, idx) => (
            <span
              key={idx}
              className="px-3 py-1 bg-blue-900/50 text-blue-300 rounded-full text-sm"
            >
              {area}
            </span>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-7 gap-3">
        {studyPlan.daily_tasks.map((task) => (
          <button
            key={task.day}
            onClick={() => setCurrentDay(task.day)}
            className={`p-4 rounded-lg border-2 transition-all ${
              currentDay === task.day
                ? 'border-blue-500 bg-blue-900/30'
                : task.completed
                ? 'border-green-500 bg-green-900/20'
                : 'border-slate-600 bg-slate-800/30 hover:border-slate-500'
            }`}
          >
            <div className="text-center">
              <div className="text-xs text-gray-400 mb-1">Day</div>
              <div className="text-2xl font-bold text-white mb-2">{task.day}</div>
              {task.completed && <CheckCircle className="w-5 h-5 text-green-400 mx-auto" />}
            </div>
          </button>
        ))}
      </div>

      {currentTask && (
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-xl font-bold text-white mb-2">{currentTask.title}</h3>
              <p className="text-gray-400">{currentTask.focus}</p>
              <div className="flex items-center gap-4 mt-2">
                <span className="text-sm text-gray-500 flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {currentTask.total_time_minutes} minutes
                </span>
              </div>
            </div>
            <button
              onClick={() => markDayComplete(currentTask.day)}
              className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${
                currentTask.completed
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {currentTask.completed ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Completed
                </>
              ) : (
                'Mark Complete'
              )}
            </button>
          </div>

          <div className="space-y-4">
            {currentTask.tasks.map((task, idx) => (
              <div key={idx} className="bg-slate-900/50 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-900/50 flex items-center justify-center flex-shrink-0">
                    {getTypeIcon(task.type)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-white">{task.activity}</h4>
                      <span className="text-sm text-gray-400">{task.duration_minutes} min</span>
                    </div>
                    <p className="text-sm text-gray-300 mb-2">{task.description}</p>
                    {task.recommendation && (
                      <div className="mt-3 p-3 bg-blue-900/20 border border-blue-700/30 rounded-lg">
                        <p className="text-xs font-medium text-blue-400 mb-1">Suggested Quiz:</p>
                        <p className="text-xs text-gray-400">
                          {task.recommendation.question_count} questions • {task.recommendation.difficulty} difficulty
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 p-4 bg-purple-900/20 border border-purple-700/30 rounded-lg">
            <h4 className="text-sm font-medium text-purple-400 mb-1 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Today's Goal
            </h4>
            <p className="text-sm text-gray-300">{currentTask.goal}</p>
          </div>
        </div>
      )}

      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Award className="w-5 h-5 text-yellow-400" />
          Weekly Goals
        </h3>
        <ul className="space-y-2">
          {studyPlan.weekly_goals.map((goal, idx) => (
            <li key={idx} className="flex items-start gap-2 text-gray-300">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
              <span>{goal}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="bg-gradient-to-r from-yellow-900/20 to-orange-900/20 border border-yellow-700/50 rounded-lg p-6">
        <h3 className="text-lg font-bold text-yellow-400 mb-4 flex items-center gap-2">
          <Lightbulb className="w-5 h-5" />
          Study Tips
        </h3>
        <ul className="space-y-2">
          {studyPlan.tips.map((tip, idx) => (
            <li key={idx} className="flex items-start gap-2 text-gray-300">
              <Zap className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

