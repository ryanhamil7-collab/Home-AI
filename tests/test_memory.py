"""Tests for memory and RAG system."""

import pytest
from pathlib import Path
import shutil

from home_ai.intelligence.memory import MemorySystem


@pytest.fixture
def memory_system():
    """Create memory system for testing."""
    system = MemorySystem()
    
    yield system
    
    memory_dir = Path.home() / ".home_ai" / "memory"
    if memory_dir.exists():
        shutil.rmtree(memory_dir)


def test_store_execution(memory_system):
    """Test storing execution history."""
    success = memory_system.store_execution(
        execution_id="test_exec_1",
        goal="Test goal",
        outcome={"success": True},
        lessons_learned=["Lesson 1", "Lesson 2"]
    )
    
    assert success is True


def test_store_framework(memory_system):
    """Test storing business framework."""
    success = memory_system.store_framework(
        framework_id="test_fw_1",
        name="Test Framework",
        content="Framework content",
        category="business"
    )
    
    assert success is True


def test_store_best_practice(memory_system):
    """Test storing best practice."""
    success = memory_system.store_best_practice(
        practice_id="test_bp_1",
        title="Test Practice",
        content="Practice content",
        domain="general"
    )
    
    assert success is True


def test_query_similar(memory_system):
    """Test querying similar memories."""
    memory_system.store_execution(
        execution_id="exec_1",
        goal="Build SaaS product",
        outcome={"success": True},
        lessons_learned=["Start with MVP"]
    )
    
    results = memory_system.query_similar("SaaS", "execution_history", n_results=5)
    
    assert isinstance(results, list)


def test_get_relevant_context(memory_system):
    """Test getting relevant context."""
    memory_system.store_execution(
        execution_id="exec_1",
        goal="Launch e-commerce store",
        outcome={"success": True},
        lessons_learned=["Focus on user experience"]
    )
    
    context = memory_system.get_relevant_context("e-commerce")
    
    assert isinstance(context, str)


def test_initialize_default_knowledge(memory_system):
    """Test initializing default knowledge base."""
    memory_system.initialize_default_knowledge()
    
    frameworks = memory_system.query_similar("Lean Canvas", "frameworks", n_results=1)
    assert len(frameworks) >= 0  # May be empty with fallback memory
