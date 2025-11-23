"""
Study Plan Recommendation Engine
AI-powered personalized study plan generation based on user performance
"""

from typing import List, Dict, Any, Optional
import openai
import os
from datetime import datetime, timedelta
import json


class StudyPlanService:
    """
    Service for generating personalized study plans and recommendations
    Uses AI to analyze performance and create customized learning paths
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize Study Plan Service
        
        Args:
            openai_api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        openai.api_key = self.api_key
        self.model = model
        
        print(f"[STUDY PLAN] Initialized with model: {model}")
    
    def generate_study_plan(
        self,
        user_performance: Dict[str, Any],
        available_documents: List[Dict[str, Any]],
        goals: Optional[Dict[str, Any]] = None,
        time_commitment: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Generate a personalized study plan based on performance analytics
        
        Args:
            user_performance: Analytics data including scores, weak areas, etc.
            available_documents: List of documents user has access to
            goals: Optional user goals (exam date, target score, etc.)
            time_commitment: 'light' (15min/day), 'moderate' (30min/day), 'intensive' (1hr/day)
            
        Returns:
            Comprehensive study plan with daily recommendations
        """
        try:
            print(f"[STUDY PLAN] Generating plan for time commitment: {time_commitment}")
            
            # Prepare context for AI
            context = self._prepare_context(user_performance, available_documents, goals, time_commitment)
            
            # Generate study plan using AI
            prompt = self._create_study_plan_prompt(context)
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert learning consultant who creates personalized study plans for legal students and professionals."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2500
            )
            
            plan_text = response.choices[0].message.content.strip()
            
            # Parse the study plan
            study_plan = self._parse_study_plan(plan_text)
            
            # Add metadata
            study_plan["generated_at"] = datetime.utcnow().isoformat()
            study_plan["time_commitment"] = time_commitment
            study_plan["user_level"] = self._determine_user_level(user_performance)
            study_plan["goals"] = goals or {}
            
            # Calculate usage
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            print(f"[STUDY PLAN] Generated plan with {len(study_plan.get('daily_tasks', []))} daily tasks")
            
            return {
                "success": True,
                "study_plan": study_plan,
                "model": self.model,
                "usage": usage
            }
            
        except Exception as e:
            print(f"[STUDY PLAN] Error generating study plan: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_context(
        self,
        performance: Dict[str, Any],
        documents: List[Dict[str, Any]],
        goals: Optional[Dict[str, Any]],
        time_commitment: str
    ) -> Dict[str, Any]:
        """Prepare context data for AI study plan generation"""
        
        context = {
            "performance": {
                "total_quizzes": performance.get('overview', {}).get('total_quizzes', 0),
                "average_score": performance.get('overview', {}).get('average_score', 0),
                "recent_average": performance.get('performance', {}).get('recent_average', 0),
                "improvement_trend": performance.get('performance', {}).get('improvement_trend', 0),
                "learning_streak": performance.get('learning_streak', {}),
                "weak_areas": []
            },
            "available_resources": {
                "document_count": len(documents),
                "documents": [
                    {
                        "id": doc.get('id'),
                        "name": doc.get('filename', 'Unknown'),
                        "title": doc.get('title'),
                        "page_count": doc.get('page_count', 0)
                    }
                    for doc in documents[:10]  # Limit to first 10
                ]
            },
            "goals": goals or {},
            "time_commitment": time_commitment
        }
        
        # Add weak areas from knowledge gaps if available
        if 'gaps' in performance:
            gaps = performance['gaps']
            weak_topics = gaps.get('weak_topics', [])
            weak_types = gaps.get('weak_question_types', [])
            
            context["performance"]["weak_areas"] = [
                f"Topic: {t.get('topic')} ({t.get('accuracy')}% accuracy)"
                for t in weak_topics[:3]
            ] + [
                f"Question type: {t.get('type')} ({t.get('accuracy')}% accuracy)"
                for t in weak_types[:2]
            ]
        
        return context
    
    def _create_study_plan_prompt(self, context: Dict[str, Any]) -> str:
        """Create the prompt for study plan generation"""
        
        perf = context["performance"]
        resources = context["available_resources"]
        goals = context["goals"]
        time_commitment = context["time_commitment"]
        
        # Time commitment mapping
        time_map = {
            "light": "15-20 minutes per day",
            "moderate": "30-45 minutes per day",
            "intensive": "1-2 hours per day"
        }
        daily_time = time_map.get(time_commitment, "30 minutes per day")
        
        weak_areas_text = "\n".join(perf["weak_areas"]) if perf["weak_areas"] else "No specific weak areas identified yet"
        
        goals_text = ""
        if goals:
            if goals.get('target_score'):
                goals_text += f"\n- Target Score: {goals['target_score']}%"
            if goals.get('exam_date'):
                goals_text += f"\n- Exam Date: {goals['exam_date']}"
            if goals.get('focus_areas'):
                goals_text += f"\n- Focus Areas: {', '.join(goals['focus_areas'])}"
        
        prompt = f"""Create a personalized study plan for a legal student/professional based on their performance and available resources.

PERFORMANCE ANALYSIS:
- Total Quizzes Completed: {perf['total_quizzes']}
- Average Score: {perf['average_score']:.1f}%
- Recent Performance: {perf['recent_average']:.1f}%
- Learning Streak: {perf['learning_streak'].get('current', 0)} days
- Improvement Trend: {perf['improvement_trend']:.1f}% {'improvement' if perf['improvement_trend'] > 0 else 'decline'}

WEAK AREAS TO ADDRESS:
{weak_areas_text}

AVAILABLE RESOURCES:
- {resources['document_count']} documents available for study
- Key documents: {', '.join([d['name'] for d in resources['documents'][:3]])}

TIME COMMITMENT:
- {daily_time}
{goals_text}

REQUIREMENTS:
1. Create a 7-day study plan (daily tasks)
2. Each day should include:
   - Primary focus area
   - Specific activities (reading, quizzes, review)
   - Time allocation
   - Success metrics
3. Address identified weak areas
4. Build on strengths
5. Include variety to maintain engagement
6. Be realistic given time commitment

OUTPUT FORMAT (JSON):
{{
  "plan_overview": {{
    "duration_days": 7,
    "focus_areas": ["area1", "area2", "area3"],
    "expected_outcome": "Brief description of expected improvement"
  }},
  "daily_tasks": [
    {{
      "day": 1,
      "title": "Day 1: Foundation Review",
      "focus": "Core concepts",
      "tasks": [
        {{
          "activity": "Review document X",
          "duration_minutes": 15,
          "description": "Focus on key sections...",
          "type": "reading"
        }},
        {{
          "activity": "Take practice quiz",
          "duration_minutes": 15,
          "description": "5 medium difficulty questions",
          "type": "practice",
          "recommendation": {{
            "document_id": "optional_doc_id",
            "question_count": 5,
            "difficulty": "medium",
            "question_types": ["multiple_choice"]
          }}
        }}
      ],
      "goal": "What to achieve today",
      "total_time_minutes": 30
    }}
  ],
  "weekly_goals": [
    "Improve weak areas by 10%",
    "Complete 5 practice quizzes",
    "Review all key documents"
  ],
  "tips": [
    "Study tip 1",
    "Study tip 2",
    "Study tip 3"
  ],
  "progress_milestones": [
    {{
      "day": 3,
      "milestone": "Mid-week check-in",
      "action": "Take assessment quiz"
    }},
    {{
      "day": 7,
      "milestone": "Week completion",
      "action": "Review progress and adjust plan"
    }}
  ]
}}

Generate the study plan now as valid JSON:"""
        
        return prompt
    
    def _parse_study_plan(self, plan_text: str) -> Dict[str, Any]:
        """Parse the AI-generated study plan"""
        try:
            # Extract JSON from response
            if "```json" in plan_text:
                start = plan_text.find("```json") + 7
                end = plan_text.find("```", start)
                plan_text = plan_text[start:end].strip()
            elif "```" in plan_text:
                start = plan_text.find("```") + 3
                end = plan_text.find("```", start)
                plan_text = plan_text[start:end].strip()
            
            # Parse JSON
            study_plan = json.loads(plan_text)
            
            # Validate required fields
            if "daily_tasks" not in study_plan:
                study_plan["daily_tasks"] = []
            
            if "plan_overview" not in study_plan:
                study_plan["plan_overview"] = {
                    "duration_days": len(study_plan.get("daily_tasks", [])),
                    "focus_areas": [],
                    "expected_outcome": "Improve overall performance"
                }
            
            return study_plan
            
        except json.JSONDecodeError as e:
            print(f"[STUDY PLAN] JSON parse error: {e}")
            # Return a basic plan as fallback
            return self._create_fallback_plan()
    
    def _create_fallback_plan(self) -> Dict[str, Any]:
        """Create a basic fallback study plan"""
        return {
            "plan_overview": {
                "duration_days": 7,
                "focus_areas": ["Review", "Practice", "Assessment"],
                "expected_outcome": "Gradual improvement through consistent practice"
            },
            "daily_tasks": [
                {
                    "day": i,
                    "title": f"Day {i}: Study Session",
                    "focus": "General review and practice",
                    "tasks": [
                        {
                            "activity": "Document review",
                            "duration_minutes": 20,
                            "description": "Review key concepts",
                            "type": "reading"
                        },
                        {
                            "activity": "Practice quiz",
                            "duration_minutes": 10,
                            "description": "Take a short quiz",
                            "type": "practice"
                        }
                    ],
                    "goal": "Reinforce learning",
                    "total_time_minutes": 30
                }
                for i in range(1, 8)
            ],
            "weekly_goals": [
                "Complete all daily sessions",
                "Improve accuracy by 5%"
            ],
            "tips": [
                "Study consistently every day",
                "Focus on understanding, not memorization",
                "Review mistakes carefully"
            ]
        }
    
    def _determine_user_level(self, performance: Dict[str, Any]) -> str:
        """Determine user's current level based on performance"""
        avg_score = performance.get('overview', {}).get('average_score', 0)
        
        if avg_score >= 85:
            return "advanced"
        elif avg_score >= 70:
            return "intermediate"
        elif avg_score >= 50:
            return "beginner"
        else:
            return "novice"
    
    def get_daily_recommendations(
        self,
        study_plan: Dict[str, Any],
        current_day: int
    ) -> Dict[str, Any]:
        """
        Get today's study recommendations from the plan
        
        Args:
            study_plan: Generated study plan
            current_day: Current day number (1-7)
            
        Returns:
            Today's tasks and recommendations
        """
        try:
            daily_tasks = study_plan.get('daily_tasks', [])
            
            # Find today's tasks
            today_task = None
            for task in daily_tasks:
                if task.get('day') == current_day:
                    today_task = task
                    break
            
            if not today_task:
                return {
                    "success": False,
                    "message": "No tasks found for today"
                }
            
            return {
                "success": True,
                "day": current_day,
                "tasks": today_task,
                "progress": {
                    "current_day": current_day,
                    "total_days": len(daily_tasks),
                    "completion_percentage": (current_day / len(daily_tasks) * 100)
                }
            }
            
        except Exception as e:
            print(f"[STUDY PLAN] Error getting daily recommendations: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_quick_recommendations(
        self,
        user_performance: Dict[str, Any],
        recent_quiz_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate quick study recommendations without a full plan
        
        Args:
            user_performance: User's performance metrics
            recent_quiz_results: Recent quiz results
            
        Returns:
            Quick actionable recommendations
        """
        try:
            recommendations = []
            
            # Check recent performance trend
            recent_avg = user_performance.get('performance', {}).get('recent_average', 0)
            overall_avg = user_performance.get('overview', {}).get('average_score', 0)
            
            if recent_avg < overall_avg - 5:
                recommendations.append({
                    "type": "alert",
                    "priority": "high",
                    "title": "Performance Dip Detected",
                    "message": "Your recent scores are lower than your average. Consider reviewing foundational concepts.",
                    "action": "Review easier material before attempting harder questions"
                })
            elif recent_avg > overall_avg + 10:
                recommendations.append({
                    "type": "success",
                    "priority": "low",
                    "title": "Great Progress!",
                    "message": "Your recent performance shows improvement. Keep up the momentum!",
                    "action": "Try increasing difficulty level"
                })
            
            # Check learning streak
            streak = user_performance.get('learning_streak', {})
            if streak.get('current', 0) == 0:
                recommendations.append({
                    "type": "motivation",
                    "priority": "medium",
                    "title": "Start Your Learning Streak",
                    "message": "Build consistency by studying every day. Even 10 minutes makes a difference!",
                    "action": "Take a quick 5-question quiz today"
                })
            elif streak.get('current', 0) >= 7:
                recommendations.append({
                    "type": "achievement",
                    "priority": "low",
                    "title": f"Amazing! {streak['current']}-Day Streak",
                    "message": "You're building excellent study habits. Keep it going!",
                    "action": "Continue your daily practice"
                })
            
            # Check weak areas
            gaps = user_performance.get('gaps', {})
            weak_types = gaps.get('weak_question_types', [])
            
            if weak_types:
                top_weak = weak_types[0]
                recommendations.append({
                    "type": "improvement",
                    "priority": "high",
                    "title": f"Focus on {top_weak.get('type', 'Unknown')} Questions",
                    "message": f"Your accuracy is {top_weak.get('accuracy', 0):.1f}% on these. Practice makes perfect!",
                    "action": f"Generate a quiz with only {top_weak.get('type')} questions"
                })
            
            # Time-based recommendation
            total_quizzes = user_performance.get('overview', {}).get('total_quizzes', 0)
            if total_quizzes < 5:
                recommendations.append({
                    "type": "guidance",
                    "priority": "medium",
                    "title": "Build Your Foundation",
                    "message": "Complete more quizzes to get accurate insights into your strengths and weaknesses.",
                    "action": "Aim for at least 10 practice quizzes"
                })
            
            return {
                "success": True,
                "recommendations": recommendations,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"[STUDY PLAN] Error generating quick recommendations: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_study_plan_progress(
        self,
        study_plan: Dict[str, Any],
        completed_day: int,
        performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update study plan based on progress and performance
        
        Args:
            study_plan: Current study plan
            completed_day: Day just completed
            performance: Performance on completed day's tasks
            
        Returns:
            Updated study plan with adjustments
        """
        try:
            # Mark day as completed
            daily_tasks = study_plan.get('daily_tasks', [])
            
            for task in daily_tasks:
                if task.get('day') == completed_day:
                    task['completed'] = True
                    task['actual_score'] = performance.get('score', 0)
                    task['completed_at'] = datetime.utcnow().isoformat()
            
            # Calculate progress
            completed_days = sum(1 for task in daily_tasks if task.get('completed', False))
            total_days = len(daily_tasks)
            progress_percentage = (completed_days / total_days * 100) if total_days > 0 else 0
            
            study_plan['progress'] = {
                "completed_days": completed_days,
                "total_days": total_days,
                "progress_percentage": progress_percentage,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            print(f"[STUDY PLAN] Updated progress: {completed_days}/{total_days} days ({progress_percentage:.1f}%)")
            
            return {
                "success": True,
                "study_plan": study_plan,
                "message": "Study plan updated successfully"
            }
            
        except Exception as e:
            print(f"[STUDY PLAN] Error updating study plan: {e}")
            return {
                "success": False,
                "error": str(e)
            }

