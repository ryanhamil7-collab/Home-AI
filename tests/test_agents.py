"""Tests for Phase 4 agents."""

import pytest

from home_ai.agents.meta_agent import get_meta_agent
from home_ai.agents.code_agent import get_code_agent
from home_ai.agents.research_agent import get_research_agent
from home_ai.agents.business_agent import get_business_agent
from home_ai.agents.content_agent import get_content_agent
from home_ai.agents.execution_agent import get_execution_agent


def test_meta_agent_initialization():
    """Test MetaAgent initialization."""
    meta = get_meta_agent()
    assert meta is not None


def test_code_agent_initialization():
    """Test CodeAgent initialization."""
    code = get_code_agent()
    assert code is not None


def test_research_agent_initialization():
    """Test ResearchAgent initialization."""
    research = get_research_agent()
    assert research is not None


def test_business_agent_initialization():
    """Test BusinessAgent initialization."""
    business = get_business_agent()
    assert business is not None


def test_content_agent_initialization():
    """Test ContentAgent initialization."""
    content = get_content_agent()
    assert content is not None


def test_execution_agent_initialization():
    """Test ExecutionAgent initialization."""
    execution = get_execution_agent()
    assert execution is not None


def test_code_agent_build_product():
    """Test CodeAgent build_product action."""
    code = get_code_agent()
    result = code.build_product("Test product")
    
    assert "success" in result
    assert result["success"] is True


def test_research_agent_market_research():
    """Test ResearchAgent market_research action."""
    research = get_research_agent()
    result = research.market_research("Test market")
    
    assert "success" in result
    assert result["success"] is True


def test_business_agent_create_plan():
    """Test BusinessAgent create_business_plan action."""
    business = get_business_agent()
    result = business.create_business_plan("Test business")
    
    assert "success" in result
    assert result["success"] is True


def test_content_agent_generate_content():
    """Test ContentAgent generate_content action."""
    content = get_content_agent()
    result = content.generate_content("twitter", "AI tools")
    
    assert "success" in result
    assert result["success"] is True


def test_execution_agent_create_store():
    """Test ExecutionAgent create_store action."""
    execution = get_execution_agent()
    result = execution.create_store("Test product", 29.99)
    
    assert "success" in result
    assert result["success"] is True
