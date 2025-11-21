"""
Psychoacoustic Test Tasks
Implements gap detection and pitch discrimination using PsychoPy.
"""

import numpy as np
from psychopy import visual, core, event
from typing import Dict, List
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
import sounddevice as sd

from config import (
    RESPONSE_KEYS,
    FIXATION_DURATION,
    INTERSTIMULUS_INTERVAL,
    GAP_INITIAL_VALUE,
    GAP_STEP_FACTOR,
    PITCH_INITIAL_DIFFERENCE,
    PITCH_STEP_FACTOR,
    MAX_REVERSALS,
    REVERSALS_FOR_THRESHOLD,
    SAMPLE_RATE,
    RAW_DATA_DIR,
    TRIAL_COLUMNS,
    FONT
)
from staircase import AdaptiveStaircase
from stimuli import StimulusGenerator

logger = logging.getLogger(__name__)


class PsychoacousticTask:
    """Base class for psychoacoustic tasks."""
    
    def __init__(
        self,
        window: visual.Window,
        participant_id: str,
        condition: str
    ):
        """
        Initialize task.
        
        Parameters
        ----------
        window : visual.Window
            PsychoPy window for display
        participant_id : str
            Participant identifier
        condition : str
            Experimental condition ('english', 'german', 'bilingual')
        """
        self.win = window
        self.participant_id = participant_id
        self.condition = condition
        
        # Initialize stimulus generator
        self.stim_gen = StimulusGenerator(sample_rate=SAMPLE_RATE)
        
        # Visual elements
        self.fixation = visual.TextStim(
            self.win,
            text='+',
            height=0.1,
            color='white',
            font=FONT
        )
        
        self.instruction_text = visual.TextStim(
            self.win,
            text='',
            height=0.05,
            wrapWidth=1.5,
            color='white',
            font=FONT
        )
        
        self.feedback_text = visual.TextStim(
            self.win,
            text='',
            height=0.04,
            color='white',
            pos=(0, -0.3),
            font=FONT
        )
        
        # Trial data storage
        self.trial_data: List[Dict] = []
        
        # Timing
        self.clock = core.Clock()
    
    def show_fixation(self):
        """Display fixation cross."""
        self.fixation.draw()
        self.win.flip()
        core.wait(FIXATION_DURATION)
    
    def present_audio_pair(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray
    ):
        """
        Present two audio stimuli with interstimulus interval.
        
        Parameters
        ----------
        audio1 : np.ndarray
            First interval audio
        audio2 : np.ndarray
            Second interval audio
        """
        # Show interval indicator
        self.instruction_text.text = "Interval 1"
        self.instruction_text.draw()
        self.win.flip()
        
        # Play first interval using sounddevice
        sd.play(audio1, samplerate=SAMPLE_RATE)
        sd.wait()
        
        # Interstimulus interval
        self.win.flip()  # blank screen
        core.wait(INTERSTIMULUS_INTERVAL)
        
        # Show interval indicator
        self.instruction_text.text = "Interval 2"
        self.instruction_text.draw()
        self.win.flip()
        
        # Play second interval
        sd.play(audio2, samplerate=SAMPLE_RATE)
        sd.wait()
        
        # Clear screen
        self.win.flip()
    
    def get_response(self) -> int:
        """
        Wait for participant response.
        
        Returns
        -------
        int
            Response interval (1 or 2), or -1 if quit
        """
        self.instruction_text.text = "Which interval?\nPress 1 or 2"
        self.instruction_text.draw()
        self.win.flip()
        
        self.clock.reset()
        keys = event.waitKeys(
            keyList=[RESPONSE_KEYS['interval_1'], 
                    RESPONSE_KEYS['interval_2'],
                    RESPONSE_KEYS['quit']]
        )
        
        rt = self.clock.getTime()
        
        if RESPONSE_KEYS['quit'] in keys:
            return -1
        elif RESPONSE_KEYS['interval_1'] in keys:
            return 1
        elif RESPONSE_KEYS['interval_2'] in keys:
            return 2
    
    def save_trial_data(self, trial_info: Dict):
        """Add trial data to storage."""
        self.trial_data.append(trial_info)
    
    def save_to_file(self, test_type: str):
        """
        Save trial data to CSV file.
        
        Parameters
        ----------
        test_type : str
            'gap' or 'pitch'
        """
        if not self.trial_data:
            logger.warning("No trial data to save")
            return
        
        df = pd.DataFrame(self.trial_data)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.participant_id}_{self.condition}_{test_type}_{timestamp}.csv"
        filepath = RAW_DATA_DIR / filename
        
        # Save
        df.to_csv(filepath, index=False)
        logger.info(f"Trial data saved to {filepath}")


class GapDetectionTask(PsychoacousticTask):
    """Gap detection psychoacoustic task."""
    
    def __init__(self, window: visual.Window, participant_id: str, condition: str):
        super().__init__(window, participant_id, condition)
        self.test_type = 'gap'
        
        # Initialize staircase
        self.staircase = AdaptiveStaircase(
            test_type='gap',
            initial_value=GAP_INITIAL_VALUE,
            step_factor=GAP_STEP_FACTOR,
            max_reversals=MAX_REVERSALS,
            reversals_for_threshold=REVERSALS_FOR_THRESHOLD
        )
    
    def run(self) -> Dict:
        """
        Run complete gap detection test.
        
        Returns
        -------
        dict
            Test results including threshold
        """
        logger.info(f"Starting gap detection: {self.participant_id}, {self.condition}")
        
        while not self.staircase.is_complete():
            # Check for quit
            if event.getKeys([RESPONSE_KEYS['quit']]):
                logger.warning("Task aborted by user")
                return None
            
            # Get current gap duration
            gap_duration = self.staircase.get_current_value()
            
            # Randomize target interval
            target_interval = np.random.choice([1, 2])
            
            # Generate stimuli
            audio1, audio2 = self.stim_gen.create_trial_pair(
                test_type='gap',
                stimulus_value=gap_duration,
                target_interval=target_interval
            )
            
            # Show fixation
            self.show_fixation()
            
            # Present stimuli
            self.present_audio_pair(audio1, audio2)
            
            # Get response
            response = self.get_response()
            
            if response == -1:  # Quit
                logger.warning("Task aborted by user")
                return None
            
            # Check correctness
            correct = (response == target_interval)
            
            # Save trial data
            trial_info = {
                'participant_id': self.participant_id,
                'condition': self.condition,
                'test_type': self.test_type,
                'trial_number': self.staircase.get_trial_number() + 1,
                'stimulus_value': gap_duration,
                'target_interval': target_interval,
                'response_interval': response,
                'correct': correct,
                'reaction_time': self.clock.getTime(),
                'reversal': False,  # Will be updated
                'timestamp': datetime.now().isoformat()
            }
            
            # Process response in staircase
            is_complete = self.staircase.process_response(correct)
            
            # Update reversal info
            if self.staircase.get_history():
                trial_info['reversal'] = self.staircase.get_history()[-1]['reversal']
            
            self.save_trial_data(trial_info)
            
            # Show progress
            self.feedback_text.text = (
                f"Trial {self.staircase.get_trial_number()} | "
                f"Reversals: {self.staircase.get_reversal_count()}/{MAX_REVERSALS}"
            )
            self.feedback_text.draw()
            self.win.flip()
            core.wait(0.5)
        
        # Calculate threshold
        threshold = self.staircase.get_threshold()
        
        # Save data
        self.save_to_file('gap')
        
        # Return results
        results = {
            'test_type': 'gap',
            'threshold': threshold,
            'threshold_unit': 'seconds',
            'n_trials': self.staircase.get_trial_number(),
            'n_reversals': self.staircase.get_reversal_count()
        }
        
        logger.info(f"Gap detection complete. Threshold: {threshold*1000:.2f} ms")
        return results


class PitchDiscriminationTask(PsychoacousticTask):
    """Pitch discrimination psychoacoustic task."""
    
    def __init__(self, window: visual.Window, participant_id: str, condition: str):
        super().__init__(window, participant_id, condition)
        self.test_type = 'pitch'
        
        # Initialize staircase
        self.staircase = AdaptiveStaircase(
            test_type='pitch',
            initial_value=PITCH_INITIAL_DIFFERENCE,
            step_factor=PITCH_STEP_FACTOR,
            max_reversals=MAX_REVERSALS,
            reversals_for_threshold=REVERSALS_FOR_THRESHOLD
        )
    
    def run(self) -> Dict:
        """
        Run complete pitch discrimination test.
        
        Returns
        -------
        dict
            Test results including threshold
        """
        logger.info(f"Starting pitch discrimination: {self.participant_id}, {self.condition}")
        
        while not self.staircase.is_complete():
            # Check for quit
            if event.getKeys([RESPONSE_KEYS['quit']]):
                logger.warning("Task aborted by user")
                return None
            
            # Get current frequency difference
            freq_diff = self.staircase.get_current_value()
            
            # Randomize target interval
            target_interval = np.random.choice([1, 2])
            
            # Generate stimuli
            audio1, audio2 = self.stim_gen.create_trial_pair(
                test_type='pitch',
                stimulus_value=freq_diff,
                target_interval=target_interval
            )
            
            # Show fixation
            self.show_fixation()
            
            # Present stimuli
            self.present_audio_pair(audio1, audio2)
            
            # Get response
            response = self.get_response()
            
            if response == -1:  # Quit
                logger.warning("Task aborted by user")
                return None
            
            # Check correctness
            correct = (response == target_interval)
            
            # Save trial data
            trial_info = {
                'participant_id': self.participant_id,
                'condition': self.condition,
                'test_type': self.test_type,
                'trial_number': self.staircase.get_trial_number() + 1,
                'stimulus_value': freq_diff,
                'target_interval': target_interval,
                'response_interval': response,
                'correct': correct,
                'reaction_time': self.clock.getTime(),
                'reversal': False,
                'timestamp': datetime.now().isoformat()
            }
            
            # Process response
            is_complete = self.staircase.process_response(correct)
            
            # Update reversal info
            if self.staircase.get_history():
                trial_info['reversal'] = self.staircase.get_history()[-1]['reversal']
            
            self.save_trial_data(trial_info)
            
            # Show progress
            self.feedback_text.text = (
                f"Trial {self.staircase.get_trial_number()} | "
                f"Reversals: {self.staircase.get_reversal_count()}/{MAX_REVERSALS}"
            )
            self.feedback_text.draw()
            self.win.flip()
            core.wait(0.5)
        
        # Calculate threshold
        threshold = self.staircase.get_threshold()
        
        # Save data
        self.save_to_file('pitch')
        
        # Return results
        results = {
            'test_type': 'pitch',
            'threshold': threshold,
            'threshold_unit': 'Hz',
            'n_trials': self.staircase.get_trial_number(),
            'n_reversals': self.staircase.get_reversal_count()
        }
        
        logger.info(f"Pitch discrimination complete. Threshold: {threshold:.2f} Hz")
        return results