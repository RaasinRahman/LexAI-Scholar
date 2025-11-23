"""
Analytics Service
Tracks user progress, quiz performance, and learning analytics
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class AnalyticsService:
    """
    Service for tracking and analyzing user learning progress
    Provides insights into quiz performance, learning trends, and knowledge gaps
    """
    
    def __init__(self):
        """Initialize Analytics Service"""
        print("[ANALYTICS] Initialized successfully")
    
    def record_quiz_session(
        self,
        user_id: str,
        quiz_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Record a completed quiz session for analytics
        
        Args:
            user_id: User identifier
            quiz_data: Quiz session data including questions, answers, scores
            
        Returns:
            Success confirmation with session summary
        """
        try:
            # Extract key metrics
            total_questions = quiz_data.get('total_questions', 0)
            correct_answers = quiz_data.get('correct_answers', 0)
            score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
            
            # Calculate time spent (if available)
            start_time = quiz_data.get('start_time')
            end_time = quiz_data.get('end_time', datetime.utcnow().isoformat())
            
            time_spent = 0
            if start_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                time_spent = (end_dt - start_dt).total_seconds()
            
            session_record = {
                "user_id": user_id,
                "quiz_id": quiz_data.get('quiz_id'),
                "document_ids": quiz_data.get('document_ids', []),
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "score_percentage": score_percentage,
                "difficulty": quiz_data.get('difficulty', 'medium'),
                "question_types": quiz_data.get('question_types', []),
                "time_spent_seconds": time_spent,
                "completed_at": end_time,
                "performance_by_type": quiz_data.get('performance_by_type', {}),
                "topics_covered": quiz_data.get('topics_covered', [])
            }
            
            print(f"[ANALYTICS] Recorded quiz session for user {user_id}: {score_percentage:.1f}% score")
            
            return {
                "success": True,
                "session_record": session_record,
                "message": "Quiz session recorded successfully"
            }
            
        except Exception as e:
            print(f"[ANALYTICS] Error recording quiz session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_progress_metrics(
        self,
        quiz_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive progress metrics from quiz history
        
        Args:
            quiz_history: List of completed quiz sessions
            
        Returns:
            Dictionary of progress metrics and analytics
        """
        try:
            if not quiz_history:
                return {
                    "success": True,
                    "total_quizzes": 0,
                    "message": "No quiz history available"
                }
            
            # Sort by date
            sorted_history = sorted(
                quiz_history,
                key=lambda x: x.get('completed_at', ''),
                reverse=False
            )
            
            # Basic metrics
            total_quizzes = len(quiz_history)
            total_questions = sum(q.get('total_questions', 0) for q in quiz_history)
            total_correct = sum(q.get('correct_answers', 0) for q in quiz_history)
            
            # Average scores
            scores = [q.get('score_percentage', 0) for q in quiz_history]
            average_score = statistics.mean(scores) if scores else 0
            median_score = statistics.median(scores) if scores else 0
            
            # Recent performance (last 5 quizzes)
            recent_scores = scores[-5:] if len(scores) >= 5 else scores
            recent_average = statistics.mean(recent_scores) if recent_scores else 0
            
            # Improvement trend
            improvement = 0
            if len(scores) >= 2:
                first_half_avg = statistics.mean(scores[:len(scores)//2])
                second_half_avg = statistics.mean(scores[len(scores)//2:])
                improvement = second_half_avg - first_half_avg
            
            # Performance by difficulty
            by_difficulty = defaultdict(lambda: {"total": 0, "correct": 0, "questions": 0})
            for quiz in quiz_history:
                diff = quiz.get('difficulty', 'medium')
                by_difficulty[diff]["total"] += 1
                by_difficulty[diff]["correct"] += quiz.get('correct_answers', 0)
                by_difficulty[diff]["questions"] += quiz.get('total_questions', 0)
            
            difficulty_stats = {}
            for diff, data in by_difficulty.items():
                if data["questions"] > 0:
                    difficulty_stats[diff] = {
                        "quizzes_taken": data["total"],
                        "accuracy": (data["correct"] / data["questions"] * 100)
                    }
            
            # Performance by question type
            by_type = defaultdict(lambda: {"correct": 0, "total": 0})
            for quiz in quiz_history:
                perf_by_type = quiz.get('performance_by_type', {})
                for qtype, stats in perf_by_type.items():
                    by_type[qtype]["correct"] += stats.get('correct', 0)
                    by_type[qtype]["total"] += stats.get('total', 0)
            
            type_stats = {}
            for qtype, data in by_type.items():
                if data["total"] > 0:
                    type_stats[qtype] = {
                        "accuracy": (data["correct"] / data["total"] * 100),
                        "questions_answered": data["total"]
                    }
            
            # Time analysis
            total_time_spent = sum(q.get('time_spent_seconds', 0) for q in quiz_history)
            avg_time_per_quiz = total_time_spent / total_quizzes if total_quizzes > 0 else 0
            
            # Learning streak
            streak = self._calculate_learning_streak(sorted_history)
            
            # Topic analysis
            topic_performance = self._analyze_topic_performance(quiz_history)
            
            # Study consistency (days active)
            unique_dates = set()
            for quiz in quiz_history:
                completed = quiz.get('completed_at', '')
                if completed:
                    try:
                        date = datetime.fromisoformat(completed.replace('Z', '+00:00')).date()
                        unique_dates.add(date)
                    except:
                        pass
            
            days_active = len(unique_dates)
            
            metrics = {
                "success": True,
                "overview": {
                    "total_quizzes": total_quizzes,
                    "total_questions_answered": total_questions,
                    "total_correct_answers": total_correct,
                    "overall_accuracy": (total_correct / total_questions * 100) if total_questions > 0 else 0,
                    "average_score": round(average_score, 2),
                    "median_score": round(median_score, 2),
                    "days_active": days_active
                },
                "performance": {
                    "recent_average": round(recent_average, 2),
                    "improvement_trend": round(improvement, 2),
                    "best_score": max(scores) if scores else 0,
                    "worst_score": min(scores) if scores else 0,
                    "consistency": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0
                },
                "by_difficulty": difficulty_stats,
                "by_question_type": type_stats,
                "time_stats": {
                    "total_time_spent_minutes": round(total_time_spent / 60, 2),
                    "average_time_per_quiz_minutes": round(avg_time_per_quiz / 60, 2)
                },
                "learning_streak": streak,
                "topic_performance": topic_performance,
                "score_history": [
                    {
                        "date": q.get('completed_at', ''),
                        "score": q.get('score_percentage', 0),
                        "difficulty": q.get('difficulty', 'medium')
                    }
                    for q in sorted_history
                ]
            }
            
            print(f"[ANALYTICS] Calculated metrics: {total_quizzes} quizzes, {average_score:.1f}% avg score")
            
            return metrics
            
        except Exception as e:
            print(f"[ANALYTICS] Error calculating progress metrics: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_learning_streak(self, sorted_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate current and longest learning streaks"""
        try:
            if not sorted_history:
                return {"current": 0, "longest": 0}
            
            dates = []
            for quiz in sorted_history:
                completed = quiz.get('completed_at', '')
                if completed:
                    try:
                        date = datetime.fromisoformat(completed.replace('Z', '+00:00')).date()
                        dates.append(date)
                    except:
                        pass
            
            if not dates:
                return {"current": 0, "longest": 0}
            
            # Remove duplicates and sort
            unique_dates = sorted(set(dates))
            
            current_streak = 1
            longest_streak = 1
            temp_streak = 1
            
            for i in range(1, len(unique_dates)):
                diff = (unique_dates[i] - unique_dates[i-1]).days
                
                if diff == 1:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1
            
            # Check if current streak is active (last date is recent)
            today = datetime.utcnow().date()
            if unique_dates:
                last_date = unique_dates[-1]
                days_since = (today - last_date).days
                
                if days_since <= 1:
                    # Count backwards from today
                    current_streak = 1
                    for i in range(len(unique_dates) - 2, -1, -1):
                        if (unique_dates[i + 1] - unique_dates[i]).days == 1:
                            current_streak += 1
                        else:
                            break
                else:
                    current_streak = 0
            
            return {
                "current": current_streak,
                "longest": longest_streak,
                "last_activity": unique_dates[-1].isoformat() if unique_dates else None
            }
            
        except Exception as e:
            print(f"[ANALYTICS] Error calculating streak: {e}")
            return {"current": 0, "longest": 0}
    
    def _analyze_topic_performance(self, quiz_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance across different topics"""
        try:
            topic_stats = defaultdict(lambda: {"correct": 0, "total": 0, "quizzes": 0})
            
            for quiz in quiz_history:
                topics = quiz.get('topics_covered', [])
                score = quiz.get('score_percentage', 0)
                
                for topic in topics:
                    topic_stats[topic]["quizzes"] += 1
                    topic_stats[topic]["total"] += quiz.get('total_questions', 0)
                    topic_stats[topic]["correct"] += quiz.get('correct_answers', 0)
            
            result = {}
            for topic, stats in topic_stats.items():
                if stats["total"] > 0:
                    result[topic] = {
                        "accuracy": round(stats["correct"] / stats["total"] * 100, 2),
                        "quizzes_taken": stats["quizzes"],
                        "questions_answered": stats["total"]
                    }
            
            return result
            
        except Exception as e:
            print(f"[ANALYTICS] Error analyzing topics: {e}")
            return {}
    
    def identify_knowledge_gaps(
        self,
        quiz_history: List[Dict[str, Any]],
        min_accuracy_threshold: float = 70.0
    ) -> Dict[str, Any]:
        """
        Identify areas where user needs improvement
        
        Args:
            quiz_history: List of completed quiz sessions
            min_accuracy_threshold: Minimum acceptable accuracy percentage
            
        Returns:
            Analysis of knowledge gaps and weak areas
        """
        try:
            gaps = {
                "weak_topics": [],
                "weak_question_types": [],
                "struggling_documents": [],
                "recommendations": []
            }
            
            # Analyze by difficulty
            by_difficulty = defaultdict(lambda: {"correct": 0, "total": 0})
            for quiz in quiz_history:
                diff = quiz.get('difficulty', 'medium')
                by_difficulty[diff]["correct"] += quiz.get('correct_answers', 0)
                by_difficulty[diff]["total"] += quiz.get('total_questions', 0)
            
            # Check each difficulty level
            for diff, stats in by_difficulty.items():
                if stats["total"] > 0:
                    accuracy = (stats["correct"] / stats["total"] * 100)
                    if accuracy < min_accuracy_threshold:
                        gaps["recommendations"].append({
                            "area": f"{diff.capitalize()} difficulty questions",
                            "accuracy": round(accuracy, 2),
                            "suggestion": f"Focus on {diff} difficulty questions to build confidence"
                        })
            
            # Analyze by question type
            by_type = defaultdict(lambda: {"correct": 0, "total": 0})
            for quiz in quiz_history:
                perf_by_type = quiz.get('performance_by_type', {})
                for qtype, perf in perf_by_type.items():
                    by_type[qtype]["correct"] += perf.get('correct', 0)
                    by_type[qtype]["total"] += perf.get('total', 0)
            
            for qtype, stats in by_type.items():
                if stats["total"] > 0:
                    accuracy = (stats["correct"] / stats["total"] * 100)
                    if accuracy < min_accuracy_threshold:
                        gaps["weak_question_types"].append({
                            "type": qtype,
                            "accuracy": round(accuracy, 2),
                            "questions_answered": stats["total"]
                        })
            
            # Analyze by document
            by_document = defaultdict(lambda: {"correct": 0, "total": 0, "quizzes": 0})
            for quiz in quiz_history:
                doc_ids = quiz.get('document_ids', [])
                for doc_id in doc_ids:
                    by_document[doc_id]["correct"] += quiz.get('correct_answers', 0)
                    by_document[doc_id]["total"] += quiz.get('total_questions', 0)
                    by_document[doc_id]["quizzes"] += 1
            
            for doc_id, stats in by_document.items():
                if stats["total"] > 0:
                    accuracy = (stats["correct"] / stats["total"] * 100)
                    if accuracy < min_accuracy_threshold:
                        gaps["struggling_documents"].append({
                            "document_id": doc_id,
                            "accuracy": round(accuracy, 2),
                            "quizzes_taken": stats["quizzes"]
                        })
            
            # Analyze topics
            topic_perf = self._analyze_topic_performance(quiz_history)
            for topic, stats in topic_perf.items():
                if stats["accuracy"] < min_accuracy_threshold:
                    gaps["weak_topics"].append({
                        "topic": topic,
                        "accuracy": round(stats["accuracy"], 2),
                        "questions_answered": stats["questions_answered"]
                    })
            
            # Generate specific recommendations
            if gaps["weak_topics"]:
                gaps["recommendations"].append({
                    "area": "Topic mastery",
                    "suggestion": f"Review {', '.join([t['topic'] for t in gaps['weak_topics'][:3]])}",
                    "priority": "high"
                })
            
            if gaps["weak_question_types"]:
                gaps["recommendations"].append({
                    "area": "Question type practice",
                    "suggestion": f"Practice {gaps['weak_question_types'][0]['type']} questions",
                    "priority": "medium"
                })
            
            print(f"[ANALYTICS] Identified {len(gaps['weak_topics'])} weak topics, {len(gaps['weak_question_types'])} weak types")
            
            return {
                "success": True,
                "gaps": gaps,
                "summary": {
                    "weak_areas_count": len(gaps["weak_topics"]) + len(gaps["weak_question_types"]),
                    "needs_attention": len(gaps["recommendations"])
                }
            }
            
        except Exception as e:
            print(f"[ANALYTICS] Error identifying knowledge gaps: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_performance_summary(
        self,
        quiz_history: List[Dict[str, Any]],
        time_period_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of performance for a specific time period
        
        Args:
            quiz_history: List of quiz sessions
            time_period_days: Number of days to analyze (None for all time)
            
        Returns:
            Performance summary for the period
        """
        try:
            # Filter by time period if specified
            if time_period_days:
                cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
                filtered_history = []
                for quiz in quiz_history:
                    completed = quiz.get('completed_at', '')
                    if completed:
                        try:
                            quiz_date = datetime.fromisoformat(completed.replace('Z', '+00:00'))
                            if quiz_date >= cutoff_date:
                                filtered_history.append(quiz)
                        except:
                            pass
                quiz_history = filtered_history
            
            if not quiz_history:
                return {
                    "success": True,
                    "message": "No quiz data for this period",
                    "period_days": time_period_days
                }
            
            # Calculate key metrics
            total_quizzes = len(quiz_history)
            scores = [q.get('score_percentage', 0) for q in quiz_history]
            average_score = statistics.mean(scores) if scores else 0
            
            # Grade distribution
            grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
            for score in scores:
                if score >= 90:
                    grade_counts["A"] += 1
                elif score >= 80:
                    grade_counts["B"] += 1
                elif score >= 70:
                    grade_counts["C"] += 1
                elif score >= 60:
                    grade_counts["D"] += 1
                else:
                    grade_counts["F"] += 1
            
            return {
                "success": True,
                "period_days": time_period_days or "all_time",
                "total_quizzes": total_quizzes,
                "average_score": round(average_score, 2),
                "best_score": max(scores) if scores else 0,
                "grade_distribution": grade_counts,
                "completion_rate": 100.0  # All quizzes in history are completed
            }
            
        except Exception as e:
            print(f"[ANALYTICS] Error getting performance summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }

