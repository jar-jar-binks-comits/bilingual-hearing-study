"""
Main Experiment Script
Bilingual Hearing Study - Full experimental protocol
"""

import sys
from pathlib import Path
from psychopy import visual, core, event, gui, prefs
from datetime import datetime
import pandas as pd
import logging
import subprocess

# Force pygame audio backend (most compatible on Mac)
prefs.hardware['audioLib'] = ['pygame']

# Import sound AFTER setting prefs
from psychopy import sound

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    CONDITION_ORDERS,
    AUDIO_FILES,
    BREAK_DURATION,
    WINDOW_SIZE,
    WINDOW_FULLSCREEN,
    WINDOW_COLOR,
    TEXT_COLOR,
    TEXT_HEIGHT,
    FONT,
    INSTRUCTIONS,
    PARTICIPANT_INFO_FIELDS,
    PROCESSED_DATA_DIR,
    THRESHOLD_COLUMNS
)
from tasks import GapDetectionTask, PitchDiscriminationTask

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('experiment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BilingualHearingExperiment:
    """Main experiment controller."""
    
    def __init__(self):
        """Initialize experiment."""
        self.participant_id = None
        self.participant_info = {}
        self.condition_order = []
        self.test_order_per_condition = []
        self.results = []
        
        # Create window
        self.win = visual.Window(
            size=WINDOW_SIZE,
            fullscr=WINDOW_FULLSCREEN,
            color=WINDOW_COLOR,
            units='height'
        )
        
        # Text stimulus for instructions
        self.instruction_text = visual.TextStim(
            self.win,
            height=TEXT_HEIGHT,
            color=TEXT_COLOR,
            wrapWidth=1.5,
            font=FONT
        )
        
        logger.info("Experiment initialized")
    
    def get_participant_info(self) -> bool:
        """
        Show dialog to collect participant information.
        
        Returns
        -------
        bool
            True if dialog completed, False if cancelled
        """
        dlg = gui.DlgFromDict(
            dictionary=PARTICIPANT_INFO_FIELDS,
            title='Bilingual Hearing Study',
            order=['participant_id', 'age', 'sex', 'native_language', 
                   'other_languages', 'musical_training', 'hearing_problems']
        )
        
        if dlg.OK:
            self.participant_info = PARTICIPANT_INFO_FIELDS.copy()
            self.participant_id = f"P{self.participant_info['participant_id']:03d}"
            
            # Determine condition order based on participant ID
            participant_num = self.participant_info['participant_id']
            order_key = ((participant_num - 1) % 3) + 1
            self.condition_order = CONDITION_ORDERS[order_key]
            
            # Counterbalance test order within each condition
            # Even conditions: gap first, Odd conditions: pitch first
            self.test_order_per_condition = []
            for i in range(len(self.condition_order)):
                if i % 2 == 0:
                    self.test_order_per_condition.append(['gap', 'pitch'])
                else:
                    self.test_order_per_condition.append(['pitch', 'gap'])
            
            logger.info(f"Participant: {self.participant_id}")
            logger.info(f"Condition order: {self.condition_order}")
            logger.info(f"Test orders: {self.test_order_per_condition}")
            
            return True
        else:
            return False
    
    def show_instructions(self, instruction_key: str, wait_for_space: bool = True):
        """
        Display instructions.
        
        Parameters
        ----------
        instruction_key : str
            Key from INSTRUCTIONS dict
        wait_for_space : bool
            Whether to wait for spacebar press
        """
        self.instruction_text.text = INSTRUCTIONS[instruction_key]
        self.instruction_text.draw()
        self.win.flip()
        
        if wait_for_space:
            event.waitKeys(keyList=['space', 'escape'])
    
    def play_audio_priming(self, condition: str):
        """
        Play language priming audio using system player.
        
        Parameters
        ----------
        condition : str
            'english', 'german', or 'bilingual'
        """
        import subprocess
        import threading
        
        logger.info(f"Playing audio priming: {condition}")
        
        # Show condition label
        condition_labels = {
            'english': 'English Only Conversation',
            'german': 'German Only Conversation',
            'bilingual': 'Bilingual (Code-Switching) Conversation'
        }
        
        audio_file = AUDIO_FILES[condition]
        
        if not audio_file.exists():
            logger.error(f"Audio file not found: {audio_file}")
            self.instruction_text.text = f"ERROR: Audio file not found\n{audio_file}\n\nPress SPACE to continue anyway"
            self.instruction_text.draw()
            self.win.flip()
            event.waitKeys(keyList=['space'])
            return
        
        # Play audio using afplay (Mac system command)
        self.instruction_text.text = (
            f"Condition: {condition_labels[condition]}\n\n"
            f"Listening...\n\n"
            f"(Audio playing via system player)"
        )
        self.instruction_text.draw()
        self.win.flip()
        
        # Run afplay in subprocess
        process = subprocess.Popen(['afplay', str(audio_file)])
        
        # Wait for completion while keeping window responsive
        while process.poll() is None:
            self.win.flip()
            core.wait(0.5)
        
        logger.info(f"Audio priming complete: {condition}")
    
    def run_hearing_tests(self, condition: str, test_order: list) -> list:
        """
        Run both hearing tests for a condition.
        
        Parameters
        ----------
        condition : str
            Current condition
        test_order : list
            Order of tests ['gap', 'pitch'] or ['pitch', 'gap']
        
        Returns
        -------
        list
            Results from both tests
        """
        results = []
        
        for test_type in test_order:
            # Show instructions
            if test_type == 'gap':
                self.show_instructions('gap_detection')
                task = GapDetectionTask(self.win, self.participant_id, condition)
            else:
                self.show_instructions('pitch_discrimination')
                task = PitchDiscriminationTask(self.win, self.participant_id, condition)
            
            # Run test
            result = task.run()
            
            if result is None:  # User quit
                return None
            
            result['condition'] = condition
            result['participant_id'] = self.participant_id
            result['timestamp'] = datetime.now().isoformat()
            results.append(result)
            
            # Brief pause between tests
            self.instruction_text.text = "Test complete.\n\nBrief pause..."
            self.instruction_text.draw()
            self.win.flip()
            core.wait(2)
        
        return results
    
    def show_break(self):
        """Show break screen with countdown."""
        logger.info("Break started")
        
        remaining = BREAK_DURATION
        
        while remaining > 0:
            minutes = remaining // 60
            seconds = remaining % 60
            
            self.instruction_text.text = (
                INSTRUCTIONS['break'] + 
                f"\n\nTime remaining: {minutes}:{seconds:02d}\n\n"
                "(Press SPACE to skip break)"
            )
            self.instruction_text.draw()
            self.win.flip()
            
            # Check for skip
            keys = event.getKeys(keyList=['space'], timeStamped=False)
            if 'space' in keys:
                logger.info("Break skipped by participant")
                break
            
            core.wait(1)
            remaining -= 1
        
        logger.info("Break complete")
    
    def show_results_summary(self):
        """Display summary of results to participant."""
        if not self.results:
            return
        
        # Create summary table
        summary_text = "Your Results:\n\n"
        summary_text += f"{'Condition':<15} {'Gap (ms)':<12} {'Pitch (Hz)':<12}\n"
        summary_text += "-" * 45 + "\n"
        
        # Group by condition
        for condition in self.condition_order:
            condition_results = [r for r in self.results if r['condition'] == condition]
            
            gap_threshold = None
            pitch_threshold = None
            
            for r in condition_results:
                if r['test_type'] == 'gap':
                    gap_threshold = r['threshold'] * 1000  # Convert to ms
                elif r['test_type'] == 'pitch':
                    pitch_threshold = r['threshold']
            
            gap_str = f"{gap_threshold:.2f}" if gap_threshold else "N/A"
            pitch_str = f"{pitch_threshold:.2f}" if pitch_threshold else "N/A"
            
            summary_text += f"{condition:<15} {gap_str:<12} {pitch_str:<12}\n"
        
        self.instruction_text.text = summary_text + "\n\nPress SPACE to finish"
        self.instruction_text.draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])
    
    def save_results(self):
        """Save threshold summary to CSV."""
        if not self.results:
            logger.warning("No results to save")
            return
        
        df = pd.DataFrame(self.results)
        
        # Reorder columns
        df = df[THRESHOLD_COLUMNS]
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.participant_id}_thresholds_{timestamp}.csv"
        filepath = PROCESSED_DATA_DIR / filename
        
        # Save
        df.to_csv(filepath, index=False)
        logger.info(f"Threshold summary saved to {filepath}")
    
    def run(self):
        """Run complete experiment."""
        try:
            # Get participant info
            if not self.get_participant_info():
                logger.info("Experiment cancelled by user")
                return
            
            # Welcome screen
            self.show_instructions('welcome')
            
            # Main experimental loop
            for i, condition in enumerate(self.condition_order):
                logger.info(f"Starting condition {i+1}/{len(self.condition_order)}: {condition}")
                
                # Audio priming instructions
                self.show_instructions('audio_priming')
                
                # Play audio
                self.play_audio_priming(condition)
                
                # Run hearing tests
                test_order = self.test_order_per_condition[i]
                results = self.run_hearing_tests(condition, test_order)
                
                if results is None:  # User quit
                    logger.warning("Experiment aborted by user")
                    break
                
                self.results.extend(results)
                
                # Show break (unless last condition)
                if i < len(self.condition_order) - 1:
                    self.show_break()
            
            # Completion
            self.show_instructions('completion')
            
            # Save results
            self.save_results()
            
            # Show summary
            self.show_results_summary()
            
            logger.info("Experiment completed successfully")
        
        except Exception as e:
            logger.error(f"Experiment error: {e}", exc_info=True)
            raise
        
        finally:
            self.win.close()
            core.quit()


def main():
    """Entry point."""
    experiment = BilingualHearingExperiment()
    experiment.run()


if __name__ == '__main__':
    main()