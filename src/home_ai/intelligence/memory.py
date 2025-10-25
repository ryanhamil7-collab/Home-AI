"""Memory and RAG system for learning and context."""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from loguru import logger

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed. Install with: pip install chromadb")


@dataclass
class Memory:
    """Memory entry."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class MemorySystem:
    """
    Memory and RAG system for learning and context.
    
    Uses ChromaDB for vector storage and retrieval.
    Stores:
    - Execution history
    - Business frameworks
    - Platform documentation
    - Best practices
    - User preferences
    """
    
    def __init__(self):
        """Initialize memory system."""
        self.memory_dir = Path.home() / ".home_ai" / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=str(self.memory_dir)
                ))
                
                self.execution_history = self.client.get_or_create_collection("execution_history")
                self.frameworks = self.client.get_or_create_collection("frameworks")
                self.best_practices = self.client.get_or_create_collection("best_practices")
                
                logger.info("MemorySystem initialized with ChromaDB")
            except Exception as e:
                logger.error(f"ChromaDB initialization failed: {e}")
                self.client = None
        else:
            self.client = None
            logger.warning("ChromaDB not available, using fallback memory")
        
        self.fallback_memory: Dict[str, List[Memory]] = {
            "execution_history": [],
            "frameworks": [],
            "best_practices": []
        }
    
    def store_execution(self, execution_id: str, goal: str, outcome: Dict[str, Any],
                       lessons_learned: List[str]) -> bool:
        """
        Store execution history.
        
        Args:
            execution_id: Unique execution ID
            goal: Goal that was executed
            outcome: Execution outcome
            lessons_learned: Lessons learned
        
        Returns:
            True if successful
        """
        try:
            content = f"Goal: {goal}\nOutcome: {json.dumps(outcome)}\nLessons: {', '.join(lessons_learned)}"
            
            metadata = {
                "execution_id": execution_id,
                "goal": goal,
                "success": outcome.get("success", False),
                "type": "execution_history"
            }
            
            if self.client:
                self.execution_history.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[execution_id]
                )
            else:
                memory = Memory(
                    id=execution_id,
                    content=content,
                    metadata=metadata
                )
                self.fallback_memory["execution_history"].append(memory)
            
            logger.info(f"Stored execution: {execution_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store execution: {e}")
            return False
    
    def store_framework(self, framework_id: str, name: str, content: str,
                       category: str = "business") -> bool:
        """
        Store business framework.
        
        Args:
            framework_id: Unique framework ID
            name: Framework name
            content: Framework content
            category: Framework category
        
        Returns:
            True if successful
        """
        try:
            metadata = {
                "framework_id": framework_id,
                "name": name,
                "category": category,
                "type": "framework"
            }
            
            if self.client:
                self.frameworks.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[framework_id]
                )
            else:
                memory = Memory(
                    id=framework_id,
                    content=content,
                    metadata=metadata
                )
                self.fallback_memory["frameworks"].append(memory)
            
            logger.info(f"Stored framework: {name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store framework: {e}")
            return False
    
    def store_best_practice(self, practice_id: str, title: str, content: str,
                           domain: str = "general") -> bool:
        """
        Store best practice.
        
        Args:
            practice_id: Unique practice ID
            title: Practice title
            content: Practice content
            domain: Practice domain
        
        Returns:
            True if successful
        """
        try:
            metadata = {
                "practice_id": practice_id,
                "title": title,
                "domain": domain,
                "type": "best_practice"
            }
            
            if self.client:
                self.best_practices.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[practice_id]
                )
            else:
                memory = Memory(
                    id=practice_id,
                    content=content,
                    metadata=metadata
                )
                self.fallback_memory["best_practices"].append(memory)
            
            logger.info(f"Stored best practice: {title}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store best practice: {e}")
            return False
    
    def query_similar(self, query: str, collection: str = "execution_history",
                     n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query for similar memories.
        
        Args:
            query: Query text
            collection: Collection to search
            n_results: Number of results
        
        Returns:
            List of similar memories
        """
        try:
            if self.client:
                collection_obj = getattr(self, collection)
                results = collection_obj.query(
                    query_texts=[query],
                    n_results=n_results
                )
                
                memories = []
                for i in range(len(results["ids"][0])):
                    memories.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None
                    })
                
                return memories
            else:
                memories = self.fallback_memory.get(collection, [])
                matching = [
                    {
                        "id": m.id,
                        "content": m.content,
                        "metadata": m.metadata
                    }
                    for m in memories
                    if query.lower() in m.content.lower()
                ]
                return matching[:n_results]
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def get_relevant_context(self, goal: str) -> str:
        """
        Get relevant context for a goal.
        
        Args:
            goal: Goal to get context for
        
        Returns:
            Relevant context string
        """
        context_parts = []
        
        similar_executions = self.query_similar(goal, "execution_history", n_results=3)
        if similar_executions:
            context_parts.append("## Similar Past Executions:")
            for exec in similar_executions:
                context_parts.append(f"- {exec['content'][:200]}...")
        
        frameworks = self.query_similar(goal, "frameworks", n_results=2)
        if frameworks:
            context_parts.append("\n## Relevant Frameworks:")
            for fw in frameworks:
                context_parts.append(f"- {fw['metadata'].get('name', 'Unknown')}: {fw['content'][:200]}...")
        
        practices = self.query_similar(goal, "best_practices", n_results=2)
        if practices:
            context_parts.append("\n## Best Practices:")
            for bp in practices:
                context_parts.append(f"- {bp['metadata'].get('title', 'Unknown')}: {bp['content'][:200]}...")
        
        return "\n".join(context_parts) if context_parts else "No relevant context found."
    
    def initialize_default_knowledge(self):
        """Initialize with default business frameworks and best practices."""
        self.store_framework(
            "lean_canvas",
            "Lean Canvas",
            """Lean Canvas is a 1-page business plan template:
            1. Problem: Top 3 problems
            2. Solution: Top 3 features
            3. Unique Value Proposition: Single, clear message
            4. Unfair Advantage: Can't be easily copied
            5. Customer Segments: Target customers
            6. Key Metrics: Key activities to measure
            7. Channels: Path to customers
            8. Cost Structure: Customer acquisition costs
            9. Revenue Streams: Revenue model""",
            "business"
        )
        
        self.store_framework(
            "swot",
            "SWOT Analysis",
            """SWOT Analysis framework:
            - Strengths: Internal positive attributes
            - Weaknesses: Internal negative attributes
            - Opportunities: External positive factors
            - Threats: External negative factors""",
            "business"
        )
        
        self.store_best_practice(
            "mvp_first",
            "Build MVP First",
            "Always start with a Minimum Viable Product. Test core hypothesis before building full features.",
            "product"
        )
        
        self.store_best_practice(
            "customer_validation",
            "Customer Validation",
            "Talk to potential customers before building. Validate problem and solution fit.",
            "business"
        )
        
        logger.info("Initialized default knowledge base")


_memory_system: Optional[MemorySystem] = None


def get_memory_system() -> MemorySystem:
    """Get or create memory system instance."""
    global _memory_system
    if _memory_system is None:
        _memory_system = MemorySystem()
        _memory_system.initialize_default_knowledge()
    return _memory_system
