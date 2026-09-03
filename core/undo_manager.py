"""
Lylis Karaoke Studio - 50-Step Undo/Redo & Autosave Manager
"""
import copy
from typing import List, Callable, Optional

class UndoRedoManager:
    def __init__(self, max_depth: int = 50):
        self.max_depth = max_depth
        self.undo_stack: List[dict] = []
        self.redo_stack: List[dict] = []
        self._is_performing = False
        self.on_state_changed: Optional[Callable[[], None]] = None

    def push_state(self, state_dict: dict):
        if self._is_performing:
            return
        
        # Deep copy snapshot
        snapshot = copy.deepcopy(state_dict)
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > self.max_depth:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        
        if self.on_state_changed:
            self.on_state_changed()

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 1

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def undo(self, current_state: dict) -> Optional[dict]:
        if not self.can_undo():
            return None

        self._is_performing = True
        try:
            current_snapshot = self.undo_stack.pop()
            self.redo_stack.append(current_snapshot)
            previous_state = copy.deepcopy(self.undo_stack[-1])
            return previous_state
        finally:
            self._is_performing = False
            if self.on_state_changed:
                self.on_state_changed()

    def redo(self, current_state: dict) -> Optional[dict]:
        if not self.can_redo():
            return None

        self._is_performing = True
        try:
            next_snapshot = self.redo_stack.pop()
            self.undo_stack.append(next_snapshot)
            return copy.deepcopy(next_snapshot)
        finally:
            self._is_performing = False
            if self.on_state_changed:
                self.on_state_changed()
