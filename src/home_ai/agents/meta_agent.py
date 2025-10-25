"""MetaAgent: Orchestrator for multi-agent autonomous business system."""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from home_ai.security.audit_logger import get_audit_logger
from home_ai.security.policy_engine import get_policy_engine, Action, ActionScope, ActionRisk


@dataclass
class Goal:
    """High-level business goal."""
    description: str
    budget: float
    timeframe: str
    target_revenue: Optional[float] = None
    constraints: Optional[Dict[str, Any]] = None


@dataclass
class Plan:
    """Execution plan for achieving a goal."""
    goal: Goal
    steps: List[Dict[str, Any]]
    estimated_cost: float
    estimated_revenue: float
    estimated_timeframe: str
    risk_level: str
    success_criteria: List[str]


@dataclass
class ExecutionResult:
    """Result of plan execution."""
    plan: Plan
    success: bool
    actual_cost: float
    actual_revenue: float
    actual_timeframe: str
    outcomes: Dict[str, Any]
    lessons_learned: List[str]


class MetaAgent:
    """
    MetaAgent: Orchestrator for autonomous business operations.
    
    Coordinates specialized agents to achieve high-level business goals.
    Uses chain-of-thought reasoning and multi-sample planning.
    """
    
    def __init__(self):
        """Initialize MetaAgent."""
        self.audit_logger = get_audit_logger()
        self.policy_engine = get_policy_engine()
        
        self._code_agent = None
        self._research_agent = None
        self._business_agent = None
        self._content_agent = None
        self._execution_agent = None
        
        self.execution_history: List[ExecutionResult] = []
        self.learned_patterns: Dict[str, Any] = {}
        
        logger.info("MetaAgent initialized")
    
    @property
    def code_agent(self):
        """Lazy load CodeAgent."""
        if self._code_agent is None:
            from home_ai.agents.code_agent import get_code_agent
            self._code_agent = get_code_agent()
        return self._code_agent
    
    @property
    def research_agent(self):
        """Lazy load ResearchAgent."""
        if self._research_agent is None:
            from home_ai.agents.research_agent import get_research_agent
            self._research_agent = get_research_agent()
        return self._research_agent
    
    @property
    def business_agent(self):
        """Lazy load BusinessAgent."""
        if self._business_agent is None:
            from home_ai.agents.business_agent import get_business_agent
            self._business_agent = get_business_agent()
        return self._business_agent
    
    @property
    def content_agent(self):
        """Lazy load ContentAgent."""
        if self._content_agent is None:
            from home_ai.agents.content_agent import get_content_agent
            self._content_agent = get_content_agent()
        return self._content_agent
    
    @property
    def execution_agent(self):
        """Lazy load ExecutionAgent."""
        if self._execution_agent is None:
            from home_ai.agents.execution_agent import get_execution_agent
            self._execution_agent = get_execution_agent()
        return self._execution_agent
    
    def execute_goal(self, goal: str, budget: float, timeframe: str,
                    target_revenue: Optional[float] = None,
                    constraints: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        Execute a high-level business goal.
        
        Args:
            goal: Description of what to achieve
            budget: Maximum budget for execution
            timeframe: Expected timeframe (e.g., "30 days")
            target_revenue: Optional revenue target
            constraints: Optional constraints
        
        Returns:
            ExecutionResult with outcomes
        """
        goal_obj = Goal(
            description=goal,
            budget=budget,
            timeframe=timeframe,
            target_revenue=target_revenue,
            constraints=constraints or {}
        )
        
        self.audit_logger.log_action(
            action_type="meta_agent",
            action="execute_goal",
            status="started",
            details={
                "goal": goal,
                "budget": budget,
                "timeframe": timeframe
            }
        )
        
        logger.info(f"Executing goal: {goal}")
        
        try:
            plans = self._generate_plans(goal_obj)
            
            best_plan = self._select_best_plan(plans, goal_obj)
            
            if not self._get_approval(best_plan):
                logger.warning("Plan not approved")
                return ExecutionResult(
                    plan=best_plan,
                    success=False,
                    actual_cost=0.0,
                    actual_revenue=0.0,
                    actual_timeframe="0 days",
                    outcomes={"error": "Plan not approved"},
                    lessons_learned=["User approval required"]
                )
            
            result = self._execute_plan(best_plan)
            
            self._learn_from_execution(result)
            
            self.audit_logger.log_action(
                action_type="meta_agent",
                action="execute_goal",
                status="completed",
                details={
                    "goal": goal,
                    "success": result.success,
                    "cost": result.actual_cost,
                    "revenue": result.actual_revenue
                }
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Goal execution failed: {e}")
            
            return ExecutionResult(
                plan=Plan(
                    goal=goal_obj,
                    steps=[],
                    estimated_cost=0.0,
                    estimated_revenue=0.0,
                    estimated_timeframe="0 days",
                    risk_level="unknown",
                    success_criteria=[]
                ),
                success=False,
                actual_cost=0.0,
                actual_revenue=0.0,
                actual_timeframe="0 days",
                outcomes={"error": str(e)},
                lessons_learned=[f"Execution failed: {e}"]
            )
    
    def _generate_plans(self, goal: Goal) -> List[Plan]:
        """
        Generate multiple candidate plans using idea tournament.
        
        Args:
            goal: Goal to achieve
        
        Returns:
            List of candidate plans
        """
        logger.info("Generating candidate plans...")
        
        plans = []
        
        for i in range(3):
            plan = self._generate_single_plan(goal, approach=i)
            plans.append(plan)
        
        logger.info(f"Generated {len(plans)} candidate plans")
        return plans
    
    def _generate_single_plan(self, goal: Goal, approach: int = 0) -> Plan:
        """Generate a single plan for the goal."""
        
        
        steps = []
        
        steps.append({
            "agent": "research",
            "action": "market_research",
            "params": {"goal": goal.description},
            "estimated_cost": goal.budget * 0.05,
            "estimated_time": "2 days"
        })
        
        steps.append({
            "agent": "business",
            "action": "create_business_plan",
            "params": {"goal": goal.description},
            "estimated_cost": 0.0,
            "estimated_time": "1 day"
        })
        
        steps.append({
            "agent": "code",
            "action": "build_product",
            "params": {"goal": goal.description},
            "estimated_cost": goal.budget * 0.40,
            "estimated_time": "14 days"
        })
        
        steps.append({
            "agent": "content",
            "action": "create_marketing_campaign",
            "params": {"goal": goal.description},
            "estimated_cost": goal.budget * 0.30,
            "estimated_time": "7 days"
        })
        
        steps.append({
            "agent": "execution",
            "action": "launch_business",
            "params": {"goal": goal.description},
            "estimated_cost": goal.budget * 0.25,
            "estimated_time": "7 days"
        })
        
        total_cost = sum(step["estimated_cost"] for step in steps)
        
        return Plan(
            goal=goal,
            steps=steps,
            estimated_cost=total_cost,
            estimated_revenue=goal.target_revenue or total_cost * 5,
            estimated_timeframe=goal.timeframe,
            risk_level="medium",
            success_criteria=[
                "Product launched",
                "Revenue > $0",
                "Cost within budget",
                "Positive user feedback"
            ]
        )
    
    def _select_best_plan(self, plans: List[Plan], goal: Goal) -> Plan:
        """
        Score plans and select the best one.
        
        Scoring criteria:
        - Cost efficiency
        - Revenue potential
        - Risk level
        - Feasibility
        - Alignment with goal
        """
        logger.info("Scoring and selecting best plan...")
        
        scored_plans = []
        
        for plan in plans:
            score = 0.0
            
            if plan.estimated_cost <= goal.budget:
                score += 25.0 * (1 - plan.estimated_cost / goal.budget)
            
            if goal.target_revenue:
                roi = plan.estimated_revenue / max(plan.estimated_cost, 1)
                score += 25.0 * min(roi / 5.0, 1.0)
            
            risk_scores = {"low": 25.0, "medium": 15.0, "high": 5.0}
            score += risk_scores.get(plan.risk_level, 10.0)
            
            score += 25.0 * (1 - len(plan.steps) / 10.0)
            
            scored_plans.append((score, plan))
        
        scored_plans.sort(key=lambda x: x[0], reverse=True)
        best_plan = scored_plans[0][1]
        
        logger.info(f"Selected plan with score: {scored_plans[0][0]:.2f}")
        return best_plan
    
    def _get_approval(self, plan: Plan) -> bool:
        """
        Request user approval for plan execution.
        
        Args:
            plan: Plan to approve
        
        Returns:
            True if approved
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="execute_business_plan",
            risk=ActionRisk.HIGH,
            params={
                "estimated_cost": plan.estimated_cost,
                "estimated_revenue": plan.estimated_revenue
            },
            description=f"Execute business plan: {plan.goal.description}",
            requires_confirmation=True
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        
        if not allowed:
            logger.warning(f"Plan execution blocked: {reason}")
            return False
        
        logger.info("Plan approved for execution")
        return True
    
    def _execute_plan(self, plan: Plan) -> ExecutionResult:
        """
        Execute the approved plan.
        
        Args:
            plan: Plan to execute
        
        Returns:
            ExecutionResult
        """
        logger.info(f"Executing plan with {len(plan.steps)} steps...")
        
        start_time = datetime.now()
        actual_cost = 0.0
        actual_revenue = 0.0
        outcomes = {}
        
        for i, step in enumerate(plan.steps):
            logger.info(f"Executing step {i+1}/{len(plan.steps)}: {step['action']}")
            
            try:
                agent_name = step["agent"]
                action = step["action"]
                params = step["params"]
                
                if agent_name == "research":
                    result = self.research_agent.execute_action(action, params)
                elif agent_name == "business":
                    result = self.business_agent.execute_action(action, params)
                elif agent_name == "code":
                    result = self.code_agent.execute_action(action, params)
                elif agent_name == "content":
                    result = self.content_agent.execute_action(action, params)
                elif agent_name == "execution":
                    result = self.execution_agent.execute_action(action, params)
                else:
                    result = {"success": False, "error": f"Unknown agent: {agent_name}"}
                
                outcomes[f"step_{i+1}"] = result
                
                actual_cost += step.get("estimated_cost", 0.0)
                
                if not result.get("success", False):
                    logger.warning(f"Step {i+1} failed: {result.get('error')}")
            
            except Exception as e:
                logger.error(f"Step {i+1} error: {e}")
                outcomes[f"step_{i+1}"] = {"success": False, "error": str(e)}
        
        end_time = datetime.now()
        actual_timeframe = f"{(end_time - start_time).days} days"
        
        success = all(
            outcomes.get(f"step_{i+1}", {}).get("success", False)
            for i in range(len(plan.steps))
        )
        
        return ExecutionResult(
            plan=plan,
            success=success,
            actual_cost=actual_cost,
            actual_revenue=actual_revenue,
            actual_timeframe=actual_timeframe,
            outcomes=outcomes,
            lessons_learned=self._extract_lessons(outcomes)
        )
    
    def _extract_lessons(self, outcomes: Dict[str, Any]) -> List[str]:
        """Extract lessons learned from execution outcomes."""
        lessons = []
        
        for step_key, result in outcomes.items():
            if not result.get("success", False):
                error = result.get("error", "Unknown error")
                lessons.append(f"{step_key}: {error}")
        
        return lessons
    
    def _learn_from_execution(self, result: ExecutionResult):
        """
        Learn from execution results to improve future plans.
        
        Args:
            result: Execution result to learn from
        """
        self.execution_history.append(result)
        
        goal_type = result.plan.goal.description[:50]
        
        if goal_type not in self.learned_patterns:
            self.learned_patterns[goal_type] = {
                "executions": 0,
                "successes": 0,
                "avg_cost": 0.0,
                "avg_revenue": 0.0
            }
        
        pattern = self.learned_patterns[goal_type]
        pattern["executions"] += 1
        
        if result.success:
            pattern["successes"] += 1
        
        n = pattern["executions"]
        pattern["avg_cost"] = (pattern["avg_cost"] * (n-1) + result.actual_cost) / n
        pattern["avg_revenue"] = (pattern["avg_revenue"] * (n-1) + result.actual_revenue) / n
        
        logger.info(f"Learned from execution: {goal_type}")
    
    def get_execution_history(self) -> List[ExecutionResult]:
        """Get execution history."""
        return self.execution_history
    
    def get_learned_patterns(self) -> Dict[str, Any]:
        """Get learned patterns."""
        return self.learned_patterns


_meta_agent: Optional[MetaAgent] = None


def get_meta_agent() -> MetaAgent:
    """Get or create global MetaAgent instance."""
    global _meta_agent
    if _meta_agent is None:
        _meta_agent = MetaAgent()
    return _meta_agent
