"""
Experimental Configuration
All parameters for the bilingual hearing study in one place.
"""

from pathlib import Path

# ============================================
# PATHS
# ============================================
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
AUDIO_DIR = DATA_DIR / "audio"

# Create directories if they don't exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, AUDIO_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================
# AUDIO PRIMING
# ============================================
AUDIO_FILES = {
    'english': AUDIO_DIR / 'english_10min.mp3',
    'german': AUDIO_DIR / 'german_10min.mp3',
    'bilingual': AUDIO_DIR / 'bilingual_10min.mp3'
}

AUDIO_DURATION = 600  # 10 minutes in seconds

# ============================================
# EXPERIMENTAL DESIGN
# ============================================
# Latin square counterbalancing for 3 conditions
CONDITION_ORDERS = {
    1: ['english', 'german', 'bilingual'],
    2: ['german', 'bilingual', 'english'],
    3: ['bilingual', 'english', 'german']
}

# Break duration between conditions (seconds)
BREAK_DURATION = 300  # 5 minutes

# ============================================
# PSYCHOACOUSTIC STIMULI
# ============================================
SAMPLE_RATE = 44100  # Hz - standard audio sampling rate

# Gap Detection Parameters
GAP_NOISE_DURATION = 0.3  # seconds - total duration of noise burst
GAP_INITIAL_VALUE = 0.050  # seconds - starting gap duration (50ms)
GAP_STEP_FACTOR = 1.5  # multiplicative adjustment factor
GAP_NOISE_LOWCUT = 100  # Hz - bandpass filter lower bound
GAP_NOISE_HIGHCUT = 8000  # Hz - bandpass filter upper bound
GAP_NOISE_AMPLITUDE = 0.3  # amplitude scaling (0-1)

# Pitch Discrimination Parameters  
PITCH_REFERENCE_FREQ = 500  # Hz - reference tone frequency
PITCH_INITIAL_DIFFERENCE = 50  # Hz - starting frequency difference
PITCH_STEP_FACTOR = 1.5  # multiplicative adjustment factor
PITCH_TONE_DURATION = 0.25  # seconds - duration of each tone
PITCH_TONE_AMPLITUDE = 0.3  # amplitude scaling (0-1)

# Stimulus timing
INTERSTIMULUS_INTERVAL = 0.5  # seconds - gap between interval 1 and 2
FADE_DURATION = 0.01  # seconds - fade in/out to prevent clicks

# ============================================
# STAIRCASE PARAMETERS
# ============================================
# 3-down-1-up rule converges at 79.4% correct
MAX_REVERSALS = 12  # total reversals before stopping
REVERSALS_FOR_THRESHOLD = 6  # number of final reversals to average
CONSECUTIVE_CORRECT_NEEDED = 3  # for 3-down rule

# ============================================
# PRESENTATION PARAMETERS
# ============================================
FIXATION_DURATION = 0.5  # seconds - fixation cross before stimulus
RESPONSE_KEYS = {
    'interval_1': '1',
    'interval_2': '2',
    'quit': 'escape'
}

# Visual display
WINDOW_SIZE = (1024, 768)
WINDOW_FULLSCREEN = False
WINDOW_COLOR = '#002b36'  # Solarized Dark base03
TEXT_COLOR = '#839496'  # Solarized Dark base0
TEXT_HEIGHT = 0.04  # proportion of window height
FONT = 'Century Gothic'  # Primary font

# ============================================
# DATA LOGGING
# ============================================
# Trial-level data columns
TRIAL_COLUMNS = [
    'participant_id',
    'condition',
    'test_type',
    'trial_number',
    'stimulus_value',
    'target_interval',
    'response_interval',
    'correct',
    'reaction_time',
    'reversal',
    'timestamp'
]

# Threshold summary columns
THRESHOLD_COLUMNS = [
    'participant_id',
    'condition',
    'test_type',
    'threshold',
    'threshold_unit',
    'n_trials',
    'n_reversals',
    'timestamp'
]

# ============================================
# PARTICIPANT INFO
# ============================================
PARTICIPANT_INFO_FIELDS = {
    'participant_id': 0,  # will be auto-incremented
    'age': 0,
    'sex': ['Male', 'Female', 'Other', 'Prefer not to say'],
    'native_language': '',
    'other_languages': '',
    'musical_training': ['None', 'Less than 2 years', '2-5 years', 'More than 5 years'],
    'hearing_problems': ['No', 'Yes (please specify)']
}

# ============================================
# INSTRUCTIONS TEXT
# ============================================
INSTRUCTIONS = {
    'welcome': """
    Welcome to the Bilingual Hearing Study
    
    This experiment examines how language context affects auditory perception.
    
    You will:
    1. Listen to 10-minute conversations (in different languages)
    2. Complete two brief hearing tests
    3. Take a 5-minute break
    4. Repeat this 3 times
    
    Total time: approximately 90 minutes
    
    Press SPACE to continue
    """,
    
    'audio_priming': """
    Language Listening Phase
    
    You will now listen to a 10-minute conversation.
    
    Please:
    - Listen attentively (as if listening to a podcast)
    - Remain seated and relaxed
    - Do not use your phone or other devices
    
    The hearing tests will begin immediately after the audio ends.
    
    Press SPACE when ready to start
    """,
    
    'gap_detection': """
    Gap Detection Test
    
    You will hear TWO bursts of noise on each trial.
    ONE of them contains a brief silence (gap) in the middle.
    
    Your task: Identify which burst contained the gap
    - Press '1' if the FIRST burst had the gap
    - Press '2' if the SECOND burst had the gap
    
    The gap will get shorter or longer based on your performance.
    There is no time limit - respond when you're ready.
    
    Press SPACE to begin
    """,
    
    'pitch_discrimination': """
    Pitch Discrimination Test
    
    You will hear TWO tones in sequence on each trial.
    ONE of them is higher in pitch.
    
    Your task: Identify which tone was higher
    - Press '1' if the FIRST tone was higher
    - Press '2' if the SECOND tone was higher
    
    The pitch difference will get smaller or larger based on your performance.
    There is no time limit - respond when you're ready.
    
    Press SPACE to begin
    """,
    
    'break': """
    Break Time (5 minutes)
    
    Please take a break. You may:
    - Walk around
    - Have a drink or snack
    - Rest quietly
    
    Please DO NOT:
    - Use your phone (no texting, social media, etc.)
    - Engage in conversation
    
    This ensures the next condition starts with a clean cognitive state.
    
    The experiment will automatically continue when the break ends,
    or you can press SPACE to continue early.
    """,
    
    'completion': """
    Experiment Complete!
    
    Thank you for your participation.
    
    Your data has been saved.
    
    Press SPACE to view your results summary
    """
}