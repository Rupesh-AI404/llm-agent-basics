"""
Simple Autonomous Agent
- Works independently without user input
- Makes decisions based on its environment
- Completes tasks autonomously
"""

import time
from enum import Enum
from datetime import datetime
from typing import Dict, List

class TaskStatus(Enum):
    """Task statuses"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AutonomousAgent:
    """A simple autonomous agent that manages and executes tasks"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.tasks: Dict[int, Dict] = {}
        self.task_counter = 0
        self.memory: List[str] = []
        self.is_running = False
        
    def add_task(self, task_name: str, task_description: str, priority: int = 1) -> int:
        """Add a new task to the agent's queue"""
        task_id = self.task_counter
        self.task_counter += 1
        
        self.tasks[task_id] = {
            "id": task_id,
            "name": task_name,
            "description": task_description,
            "status": TaskStatus.PENDING,
            "priority": priority,
            "created_at": datetime.now(),
            "completed_at": None
        }
        
        log_msg = f"[{self.agent_name}] Added task: {task_name} (Priority: {priority})"
        self.memory.append(log_msg)
        print(log_msg)
        return task_id
    
    def get_next_task(self) -> Dict:
        """Get the highest priority pending task"""
        pending_tasks = [
            task for task in self.tasks.values() 
            if task["status"] == TaskStatus.PENDING
        ]
        
        if not pending_tasks:
            return None
        
        # Sort by priority (higher = more important)
        return max(pending_tasks, key=lambda x: x["priority"])
    
    def execute_task(self, task_id: int) -> bool:
        """Simulate executing a task"""
        if task_id not in self.tasks:
            print(f"[{self.agent_name}] Task {task_id} not found!")
            return False
        
        task = self.tasks[task_id]
        
        # Update status to in progress
        task["status"] = TaskStatus.IN_PROGRESS
        log_msg = f"[{self.agent_name}] Executing: {task['name']}"
        self.memory.append(log_msg)
        print(log_msg)
        
        # Simulate work
        time.sleep(0.5)
        
        # Mark as completed
        task["status"] = TaskStatus.COMPLETED
        task["completed_at"] = datetime.now()
        
        log_msg = f"[{self.agent_name}] Completed: {task['name']}"
        self.memory.append(log_msg)
        print(f"[DONE] {log_msg}")
        
        return True
    
    def run_autonomously(self, max_iterations: int = 10):
        """Run the agent autonomously, executing all pending tasks"""
        self.is_running = True
        iterations = 0
        
        print(f"\n{'='*60}")
        print(f"[AGENT] Autonomous Agent Started: {self.agent_name}")
        print(f"{'='*60}\n")
        
        while self.is_running and iterations < max_iterations:
            next_task = self.get_next_task()
            
            if not next_task:
                print(f"\n[{self.agent_name}] No more tasks. Agent idle.")
                break
            
            self.execute_task(next_task["id"])
            iterations += 1
            time.sleep(0.3)
        
        print(f"\n{'='*60}")
        print(f"Agent Summary for {self.agent_name}")
        print(f"{'='*60}")
        print(f"Total Tasks: {len(self.tasks)}")
        print(f"Completed: {sum(1 for t in self.tasks.values() if t['status'] == TaskStatus.COMPLETED)}")
        print(f"Pending: {sum(1 for t in self.tasks.values() if t['status'] == TaskStatus.PENDING)}")
        print(f"Failed: {sum(1 for t in self.tasks.values() if t['status'] == TaskStatus.FAILED)}")
        print(f"{'='*60}\n")
    
    def get_memory_log(self) -> str:
        """Return agent's memory log"""
        return "\n".join(self.memory)
    
    def stop(self):
        """Stop the agent"""
        self.is_running = False
        print(f"\n[{self.agent_name}] Stopped.")

    def start(self):
        """Start the agent"""
        self.is_running = True
        print(f"\n[{self.agent_name}] Started.")

    def end(self):
        """Stop the agent"""
        self.is_running = False
        print(f"\n[{self.agent_name}] Stopped.")

# Example usage
if __name__ == "__main__":
    # Create an autonomous agent
    agent = AutonomousAgent("TaskBot")
    agent.start()

    
    # Add tasks
    agent.add_task("Data Collection", "Gather data from sources", priority=3)
    agent.add_task("Data Processing", "Clean and process data", priority=2)
    agent.add_task("Analysis", "Analyze processed data", priority=1)
    agent.add_task("Report Generation", "Generate final report", priority=4)
    agent.add_task("Notification", "Send notifications", priority=2)
    agent.add_task("Report Generation", "Generate final report", priority=3)
    
    # Run autonomously
    agent.run_autonomously()
    
    # Print memory log
    print("\n[MEMORY] Agent Memory Log:")
    print("-" * 60)
    print(agent.get_memory_log())
