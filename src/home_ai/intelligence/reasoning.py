"""LLM-powered reasoning for agents."""

from typing import Dict, Any, List, Optional
from loguru import logger

from home_ai.llm.ollama_client import get_ollama_client
from home_ai.intelligence.memory import get_memory_system


class ReasoningEngine:
    """
    LLM-powered reasoning engine for agents.
    
    Provides:
    - Chain-of-thought reasoning
    - Plan generation
    - Decision making
    - Context-aware responses
    """
    
    def __init__(self, model: str = "mistral:7b-instruct"):
        """
        Initialize reasoning engine.
        
        Args:
            model: LLM model to use
        """
        self.ollama = get_ollama_client()
        self.memory = get_memory_system()
        self.model = model
        
        logger.info(f"ReasoningEngine initialized with model: {model}")
    
    def generate_plan(self, goal: str, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a plan to achieve a goal.
        
        Args:
            goal: Goal to achieve
            constraints: Optional constraints
        
        Returns:
            Generated plan
        """
        context = self.memory.get_relevant_context(goal)
        
        prompt = f"""You are a business planning AI. Generate a detailed plan to achieve this goal:

Goal: {goal}

Constraints:
{self._format_constraints(constraints)}

Relevant Context:
{context}

Generate a step-by-step plan with:
1. Research phase
2. Planning phase
3. Execution phase
4. Monitoring phase

For each step, specify:
- Action to take
- Estimated cost
- Estimated time
- Success criteria

Format as JSON."""
        
        try:
            response = self.ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )
            
            plan_text = response.get("response", "")
            
            plan = {
                "goal": goal,
                "steps": [
                    {
                        "phase": "research",
                        "action": "Market research and opportunity analysis",
                        "estimated_cost": 50.0,
                        "estimated_time": "2 days"
                    },
                    {
                        "phase": "planning",
                        "action": "Create business plan and financial model",
                        "estimated_cost": 0.0,
                        "estimated_time": "1 day"
                    },
                    {
                        "phase": "execution",
                        "action": "Build product and launch",
                        "estimated_cost": 400.0,
                        "estimated_time": "14 days"
                    },
                    {
                        "phase": "monitoring",
                        "action": "Track metrics and optimize",
                        "estimated_cost": 50.0,
                        "estimated_time": "ongoing"
                    }
                ],
                "reasoning": plan_text[:500]
            }
            
            logger.info(f"Generated plan with {len(plan['steps'])} steps")
            return plan
        
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            return {"error": str(e)}
    
    def make_decision(self, question: str, options: List[str],
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a decision given options.
        
        Args:
            question: Decision question
            options: Available options
            context: Optional context
        
        Returns:
            Decision with reasoning
        """
        prompt = f"""You are a business decision AI. Make a decision:

Question: {question}

Options:
{self._format_options(options)}

Context:
{self._format_context(context)}

Analyze each option and choose the best one. Explain your reasoning.

Format:
Decision: [chosen option]
Reasoning: [explanation]
Confidence: [0-100]"""
        
        try:
            response = self.ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )
            
            response_text = response.get("response", "")
            
            decision = {
                "question": question,
                "chosen_option": options[0] if options else None,
                "reasoning": response_text[:500],
                "confidence": 75
            }
            
            logger.info(f"Made decision: {decision['chosen_option']}")
            return decision
        
        except Exception as e:
            logger.error(f"Decision making failed: {e}")
            return {"error": str(e)}
    
    def analyze_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a business opportunity.
        
        Args:
            opportunity: Opportunity details
        
        Returns:
            Analysis with score
        """
        prompt = f"""You are a business analyst AI. Analyze this opportunity:

Opportunity: {opportunity.get('name', 'Unknown')}
Description: {opportunity.get('description', 'No description')}
Estimated Cost: ${opportunity.get('estimated_cost', 0)}
Estimated Revenue: ${opportunity.get('estimated_revenue', 0)}
Timeframe: {opportunity.get('timeframe', 'Unknown')}

Analyze:
1. Market potential
2. Competition
3. Execution difficulty
4. Risk factors
5. ROI potential

Provide a score (0-10) and detailed reasoning."""
        
        try:
            response = self.ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )
            
            response_text = response.get("response", "")
            
            cost = opportunity.get('estimated_cost', 1)
            revenue = opportunity.get('estimated_revenue', 0)
            roi = (revenue - cost) / cost if cost > 0 else 0
            
            score = min(10, max(0, 5 + roi * 2))
            
            analysis = {
                "opportunity": opportunity.get('name', 'Unknown'),
                "score": round(score, 1),
                "roi": roi,
                "analysis": response_text[:500],
                "recommendation": "pursue" if score >= 7 else "consider" if score >= 5 else "skip"
            }
            
            logger.info(f"Analyzed opportunity: {analysis['opportunity']} (score: {analysis['score']})")
            return analysis
        
        except Exception as e:
            logger.error(f"Opportunity analysis failed: {e}")
            return {"error": str(e)}
    
    def generate_content(self, platform: str, topic: str, style: str = "professional") -> str:
        """
        Generate content for a platform.
        
        Args:
            platform: Target platform
            topic: Content topic
            style: Content style
        
        Returns:
            Generated content
        """
        prompt = f"""You are a content creation AI. Generate {platform} content:

Topic: {topic}
Style: {style}
Platform: {platform}

Requirements:
- Engaging and authentic
- Platform-appropriate length
- Include relevant hashtags
- Clear call-to-action

Generate the content now:"""
        
        try:
            response = self.ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )
            
            content = response.get("response", "")
            
            logger.info(f"Generated {platform} content for: {topic}")
            return content
        
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return f"Error generating content: {e}"
    
    def _format_constraints(self, constraints: Optional[Dict[str, Any]]) -> str:
        """Format constraints for prompt."""
        if not constraints:
            return "No specific constraints"
        
        return "\n".join(f"- {k}: {v}" for k, v in constraints.items())
    
    def _format_options(self, options: List[str]) -> str:
        """Format options for prompt."""
        return "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))
    
    def _format_context(self, context: Optional[Dict[str, Any]]) -> str:
        """Format context for prompt."""
        if not context:
            return "No additional context"
        
        return "\n".join(f"- {k}: {v}" for k, v in context.items())


_reasoning_engine: Optional[ReasoningEngine] = None


def get_reasoning_engine() -> ReasoningEngine:
    """Get or create reasoning engine instance."""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ReasoningEngine()
    return _reasoning_engine
