"""
Tests for DAG-based task execution engine
"""

import unittest
from unittest.mock import MagicMock, patch
from dataclasses import field
from typing import List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.ai_agent.core_processing.five_phase_engine import (
    Task, TaskStatus, PipelineContext, FivePhaseEngine
)


class TestTask(unittest.TestCase):
    """Test the Task dataclass"""
    
    def test_task_creation(self):
        """Test basic task creation"""
        task = Task(id="task_1", action="Do something", waiting_for=[])
        self.assertEqual(task.id, "task_1")
        self.assertEqual(task.action, "Do something")
        self.assertEqual(task.waiting_for, [])
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNone(task.result)
        self.assertIsNone(task.error)
    
    def test_task_with_dependencies(self):
        """Test task with dependencies"""
        task = Task(id="task_2", action="Do something else", waiting_for=["task_1"])
        self.assertEqual(task.waiting_for, ["task_1"])
    
    def test_task_default_status(self):
        """Test that default status is PENDING"""
        task = Task(id="task_1", action="Test")
        self.assertEqual(task.status, TaskStatus.PENDING)


class TestGetExecutableTasks(unittest.TestCase):
    """Test the _get_executable_tasks method"""
    
    def setUp(self):
        self.engine = FivePhaseEngine(config={})
    
    def test_no_tasks(self):
        """Test with empty task list"""
        result = self.engine._get_executable_tasks([])
        self.assertEqual(result, [])
    
    def test_single_executable_task(self):
        """Test with single executable task"""
        tasks = [Task(id="task_1", action="Do something", waiting_for=[])]
        result = self.engine._get_executable_tasks(tasks)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "task_1")
        self.assertEqual(result[0].status, TaskStatus.EXECUTABLE)
    
    def test_mixed_tasks(self):
        """Test with mix of executable and non-executable tasks"""
        tasks = [
            Task(id="task_1", action="First", waiting_for=[]),
            Task(id="task_2", action="Second", waiting_for=["task_1"]),
            Task(id="task_3", action="Third", waiting_for=[]),
        ]
        result = self.engine._get_executable_tasks(tasks)
        self.assertEqual(len(result), 2)
        ids = [t.id for t in result]
        self.assertIn("task_1", ids)
        self.assertIn("task_3", ids)
    
    def test_already_completed_tasks(self):
        """Test that completed tasks are not returned"""
        tasks = [
            Task(id="task_1", action="First", waiting_for=[], status=TaskStatus.COMPLETED),
            Task(id="task_2", action="Second", waiting_for=[]),
        ]
        result = self.engine._get_executable_tasks(tasks)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "task_2")


class TestCheckDeadlock(unittest.TestCase):
    """Test the _check_deadlock method"""
    
    def setUp(self):
        self.engine = FivePhaseEngine(config={})
    
    def test_no_deadlock_all_completed(self):
        """Test no deadlock when all tasks completed"""
        tasks = [
            Task(id="task_1", action="First", waiting_for=[], status=TaskStatus.COMPLETED),
            Task(id="task_2", action="Second", waiting_for=["task_1"], status=TaskStatus.COMPLETED),
        ]
        self.assertFalse(self.engine._check_deadlock(tasks))
    
    def test_deadlock_detected(self):
        """Test deadlock detection when tasks have unmet dependencies"""
        tasks = [
            Task(id="task_1", action="First", waiting_for=["task_2"], status=TaskStatus.PENDING),
            Task(id="task_2", action="Second", waiting_for=["task_1"], status=TaskStatus.PENDING),
        ]
        self.assertTrue(self.engine._check_deadlock(tasks))
    
    def test_no_deadlock_with_executable(self):
        """Test no deadlock when there are executable tasks"""
        tasks = [
            Task(id="task_1", action="First", waiting_for=[], status=TaskStatus.PENDING),
            Task(id="task_2", action="Second", waiting_for=["task_1"], status=TaskStatus.PENDING),
        ]
        self.assertFalse(self.engine._check_deadlock(tasks))
    
    def test_empty_task_list(self):
        """Test with empty task list"""
        self.assertFalse(self.engine._check_deadlock([]))


class TestMarkTaskCompleted(unittest.TestCase):
    """Test the _mark_task_completed method"""
    
    def setUp(self):
        self.engine = FivePhaseEngine(config={})
    
    def test_mark_completed(self):
        """Test marking a task as completed"""
        tasks = [
            Task(id="task_1", action="First", waiting_for=[]),
            Task(id="task_2", action="Second", waiting_for=["task_1"]),
        ]
        self.engine._mark_task_completed(tasks[0], tasks)
        self.assertEqual(tasks[0].status, TaskStatus.COMPLETED)
        self.assertEqual(tasks[1].waiting_for, [])
    
    def test_remove_from_multiple_dependencies(self):
        """Test removing completed task from multiple dependencies"""
        tasks = [
            Task(id="task_1", action="First", waiting_for=[]),
            Task(id="task_2", action="Second", waiting_for=["task_1"]),
            Task(id="task_3", action="Third", waiting_for=["task_1"]),
        ]
        self.engine._mark_task_completed(tasks[0], tasks)
        self.assertEqual(tasks[1].waiting_for, [])
        self.assertEqual(tasks[2].waiting_for, [])


class TestMarkTaskFailed(unittest.TestCase):
    """Test the _mark_task_failed method"""
    
    def setUp(self):
        self.engine = FivePhaseEngine(config={})
    
    def test_mark_failed(self):
        """Test marking a task as failed"""
        tasks = [
            Task(id="task_1", action="First", waiting_for=[]),
            Task(id="task_2", action="Second", waiting_for=["task_1"]),
        ]
        self.engine._mark_task_failed(tasks[0], tasks)
        self.assertEqual(tasks[0].status, TaskStatus.FAILED)
        self.assertEqual(tasks[1].status, TaskStatus.BLOCKED)
    
    def test_block_multiple_dependents(self):
        """Test blocking multiple dependent tasks"""
        tasks = [
            Task(id="task_1", action="First", waiting_for=[]),
            Task(id="task_2", action="Second", waiting_for=["task_1"]),
            Task(id="task_3", action="Third", waiting_for=["task_1"]),
            Task(id="task_4", action="Fourth", waiting_for=[]),
        ]
        self.engine._mark_task_failed(tasks[0], tasks)
        self.assertEqual(tasks[1].status, TaskStatus.BLOCKED)
        self.assertEqual(tasks[2].status, TaskStatus.BLOCKED)
        self.assertEqual(tasks[3].status, TaskStatus.PENDING)


class TestParseTaskList(unittest.TestCase):
    """Test the _parse_task_list method"""
    
    def setUp(self):
        self.engine = FivePhaseEngine(config={})
    
    def test_parse_json_format(self):
        """Test parsing JSON format tasks"""
        tasks_text = '''
        {"id": "task_1", "action": "First step", "waiting_for": []},
        {"id": "task_2", "action": "Second step", "waiting_for": ["task_1"]}
        '''
        result = self.engine._parse_task_list(tasks_text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "task_1")
        self.assertEqual(result[0]["action"], "First step")
        self.assertEqual(result[0]["waiting_for"], [])
        self.assertEqual(result[1]["id"], "task_2")
        self.assertEqual(result[1]["waiting_for"], ["task_1"])
    
    def test_parse_key_value_format(self):
        """Test parsing key-value format tasks"""
        tasks_text = '''
        id: task_1
        action: First step
        waiting_for: []
        
        id: task_2
        action: Second step
        waiting_for: [task_1]
        '''
        result = self.engine._parse_task_list(tasks_text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "task_1")
        self.assertEqual(result[1]["id"], "task_2")
    
    def test_parse_empty_input(self):
        """Test parsing empty input"""
        result = self.engine._parse_task_list("")
        self.assertEqual(result, [])


class TestParseVexisCommands(unittest.TestCase):
    """Test the _parse_vexis_commands method"""
    
    def setUp(self):
        self.engine = FivePhaseEngine(config={})
    
    def test_parse_tasks_command(self):
        """Test parsing tasks command"""
        text = '''
        action_type [run_command]
        tasks [
        {"id": "task_1", "action": "First step", "waiting_for": []},
        {"id": "task_2", "action": "Second step", "waiting_for": ["task_1"]}
        ]
        '''
        result = self.engine._parse_vexis_commands(text)
        self.assertIn("tasks", result)
        self.assertEqual(len(result["tasks"]), 2)
        self.assertEqual(result["action_type"], "run_command")
    
    def test_parse_step_list_fallback(self):
        """Test parsing step_list when tasks not present"""
        text = '''
        action_type [run_command]
        step_list [1. First step
        2. Second step]
        '''
        result = self.engine._parse_vexis_commands(text)
        self.assertIn("step_list", result)
        self.assertEqual(len(result["step_list"]), 2)


class TestDagExecution(unittest.TestCase):
    """Test the DAG execution engine"""
    
    @patch.object(FivePhaseEngine, '_execute_single_task')
    def test_simple_dag_execution(self, mock_execute):
        """Test simple DAG execution with sequential tasks"""
        mock_execute.return_value = True
        
        engine = FivePhaseEngine(config={})
        context = PipelineContext(
            user_prompt="Test task",
            tasks=[
                Task(id="task_1", action="First step", waiting_for=[]),
                Task(id="task_2", action="Second step", waiting_for=["task_1"]),
            ]
        )
        
        result = engine._execute_dag_tasks(context)
        
        self.assertTrue(result)
        self.assertEqual(context.tasks[0].status, TaskStatus.COMPLETED)
        self.assertEqual(context.tasks[1].status, TaskStatus.COMPLETED)
    
    @patch.object(FivePhaseEngine, '_execute_single_task')
    def test_dag_with_failure(self, mock_execute):
        """Test DAG execution with a task failure"""
        mock_execute.side_effect = [True, False, True]  # task_1 succeeds, task_2 fails, task_3 succeeds
        
        engine = FivePhaseEngine(config={})
        context = PipelineContext(
            user_prompt="Test task",
            tasks=[
                Task(id="task_1", action="First step", waiting_for=[]),
                Task(id="task_2", action="Second step", waiting_for=["task_1"]),
                Task(id="task_3", action="Third step", waiting_for=[]),
            ]
        )
        
        result = engine._execute_dag_tasks(context)
        
        self.assertFalse(result)
        self.assertEqual(context.tasks[0].status, TaskStatus.COMPLETED)
        self.assertEqual(context.tasks[1].status, TaskStatus.FAILED)
        self.assertEqual(context.tasks[2].status, TaskStatus.COMPLETED)
    
    @patch.object(FivePhaseEngine, '_execute_single_task')
    def test_dag_with_blocked_tasks(self, mock_execute):
        """Test that dependent tasks are blocked when prerequisite fails"""
        mock_execute.side_effect = [False]  # task_1 fails
        
        engine = FivePhaseEngine(config={})
        context = PipelineContext(
            user_prompt="Test task",
            tasks=[
                Task(id="task_1", action="First step", waiting_for=[]),
                Task(id="task_2", action="Second step", waiting_for=["task_1"]),
                Task(id="task_3", action="Third step", waiting_for=["task_2"]),
            ]
        )
        
        result = engine._execute_dag_tasks(context)
        
        self.assertFalse(result)
        self.assertEqual(context.tasks[0].status, TaskStatus.FAILED)
        self.assertEqual(context.tasks[1].status, TaskStatus.BLOCKED)
        self.assertEqual(context.tasks[2].status, TaskStatus.BLOCKED)


if __name__ == '__main__':
    unittest.main()
