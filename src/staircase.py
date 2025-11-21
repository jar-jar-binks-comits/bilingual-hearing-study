"""
Adaptive Staircase Implementation
Transformed up-down method (Levitt, 1971) for psychoacoustic threshold estimation.

The 3-down-1-up rule converges at 79.4% correct performance.
"""

import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AdaptiveStaircase:
    """
    Implements 3-down-1-up adaptive staircase procedure.
    
    After 3 consecutive correct responses: stimulus decreases (harder)
    After 1 incorrect response: stimulus increases (easier)
    
    Threshold is calculated as mean of last N reversals.
    """
    
    def __init__(
        self,
        test_type: str,
        initial_value: float,
        step_factor: float = 1.5,
        max_reversals: int = 12,
        reversals_for_threshold: int = 6
    ):
        """
        Initialize staircase.
        
        Parameters
        ----------
        test_type : str
            'gap' or 'pitch' (for logging)
        initial_value : float
            Starting stimulus value (e.g., 0.050 for gap in seconds, 50 for pitch in Hz)
        step_factor : float
            Multiplicative adjustment factor (typically 1.5 or 2.0)
        max_reversals : int
            Number of reversals before terminating
        reversals_for_threshold : int
            Number of final reversals to average for threshold estimate
        """
        self.test_type = test_type
        self.current_value = initial_value
        self.step_factor = step_factor
        self.max_reversals = max_reversals
        self.reversals_for_threshold = reversals_for_threshold
        
        # Response tracking for 3-down-1-up rule
        self.consecutive_correct = 0
        
        # History tracking
        self.trial_history: List[Dict] = []
        self.reversal_values: List[float] = []
        
        # Direction tracking for detecting reversals
        self.last_direction: Optional[str] = None  # 'up' or 'down'
        
        # Trial counter
        self.trial_number = 0
        
        logger.info(
            f"Staircase initialized: {test_type}, "
            f"start={initial_value:.4f}, factor={step_factor}"
        )
    
    def process_response(self, correct: bool) -> bool:
        """
        Process a trial response and update staircase state.
        
        Parameters
        ----------
        correct : bool
            Was the response correct?
        
        Returns
        -------
        bool
            True if staircase is complete (reached max_reversals)
        """
        self.trial_number += 1
        direction_this_trial = None
        
        if correct:
            self.consecutive_correct += 1
            
            # 3-DOWN rule: After 3 consecutive correct, make HARDER
            if self.consecutive_correct >= 3:
                self.current_value = self.current_value / self.step_factor
                direction_this_trial = 'down'
                self.consecutive_correct = 0
                
                logger.debug(
                    f"Trial {self.trial_number}: 3 correct → HARDER "
                    f"(new value: {self.current_value:.4f})"
                )
            else:
                logger.debug(
                    f"Trial {self.trial_number}: Correct "
                    f"({self.consecutive_correct}/3)"
                )
        else:
            # 1-UP rule: After ANY incorrect, make EASIER
            self.current_value = self.current_value * self.step_factor
            direction_this_trial = 'up'
            self.consecutive_correct = 0
            
            logger.debug(
                f"Trial {self.trial_number}: Incorrect → EASIER "
                f"(new value: {self.current_value:.4f})"
            )
        
        # Reversal detection
        is_reversal = False
        if direction_this_trial is not None and self.last_direction is not None:
            if direction_this_trial != self.last_direction:
                is_reversal = True
                self.reversal_values.append(self.current_value)
                logger.info(
                    f"*** REVERSAL #{len(self.reversal_values)} "
                    f"at value {self.current_value:.4f} ***"
                )
        
        # Update direction
        if direction_this_trial is not None:
            self.last_direction = direction_this_trial
        
        # Store trial data
        self.trial_history.append({
            'trial': self.trial_number,
            'value': self.current_value,
            'correct': correct,
            'reversal': is_reversal
        })
        
        # Check completion
        is_complete = len(self.reversal_values) >= self.max_reversals
        if is_complete:
            logger.info(f"Staircase COMPLETE after {self.trial_number} trials")
        
        return is_complete
    
    def get_threshold(self) -> float:
        """
        Calculate threshold as mean of last N reversals.
        
        Returns
        -------
        float
            Threshold estimate (same units as stimulus)
        """
        if len(self.reversal_values) < self.reversals_for_threshold:
            logger.warning(
                f"Only {len(self.reversal_values)} reversals, "
                f"need {self.reversals_for_threshold}. Using all available."
            )
            values = self.reversal_values
        else:
            # Take last N reversals (most stable)
            values = self.reversal_values[-self.reversals_for_threshold:]
        
        threshold = np.mean(values)
        
        logger.info(
            f"Threshold calculated from last {len(values)} reversals: "
            f"{values}"
        )
        logger.info(f"Final threshold: {threshold:.4f}")
        
        return threshold
    
    def get_current_value(self) -> float:
        """Get current stimulus value for next trial."""
        return self.current_value
    
    def get_trial_number(self) -> int:
        """Get current trial number."""
        return self.trial_number
    
    def get_reversal_count(self) -> int:
        """Get number of reversals so far."""
        return len(self.reversal_values)
    
    def get_history(self) -> List[Dict]:
        """Get complete trial history."""
        return self.trial_history
    
    def is_complete(self) -> bool:
        """Check if staircase has reached max reversals."""
        return len(self.reversal_values) >= self.max_reversals
    
    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics for logging.
        
        Returns
        -------
        dict
            Summary of staircase performance
        """
        return {
            'test_type': self.test_type,
            'n_trials': self.trial_number,
            'n_reversals': len(self.reversal_values),
            'threshold': self.get_threshold(),
            'reversal_values': self.reversal_values,
            'initial_value': self.trial_history[0]['value'] if self.trial_history else None,
            'final_value': self.current_value
        }