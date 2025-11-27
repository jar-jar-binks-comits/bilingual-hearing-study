# Bilingual Hearing Study

Experimental software for investigating how bilingual language context affects auditory processing thresholds.

## Overview

This study examines whether managing two languages (bilingual listening) temporarily reduces auditory sensitivity compared to monolingual listening. Participants listen to 10-minute audio conversations in different language conditions (English-only, German-only, or code-switched bilingual), then complete two psychoacoustic tests: gap detection and pitch discrimination.

**Research Question:** Does bilingual cognitive load affect low-level auditory processing?

## Study Design

- **Within-subjects design**: Each participant completes all three conditions
- **Conditions**: English monolingual, German monolingual, Bilingual (code-switching)
- **Counterbalancing**: Latin square design across participants
- **Tests**: Gap detection (temporal resolution) and Pitch discrimination (frequency resolution)
- **Duration**: Approximately 90 minutes per participant

## Requirements

- **Python**: 3.10 (tested on macOS)
- **Hardware**: Headphones or speakers, quiet testing environment
- **Audio files**: 10-minute MP3 files for each language condition

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/jar-jar-binks-comits/bilingual-hearing-study.git
cd bilingual-hearing-study
```

### 2. Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Prepare Audio Files

Place three 10-minute audio files in `data/audio/`:
- `english_10min.mp3` - English-only conversation
- `german_10min.mp3` - German-only conversation  
- `bilingual_10min.mp3` - Code-switched English-German conversation

## Running the Experiment

```bash
cd src
python experiment.py
```

### Participant Information

When the dialog appears, enter:
- **Participant ID**: Sequential integer (1, 2, 3, ...)
- **Age**: Participant age
- **Sex**: Male/Female/Other/Prefer not to say
- **Native Language**: L1
- **Other Languages**: L2, L3, etc.
- **Musical Training**: None / <2 years / 2-5 years / >5 years
- **Hearing Problems**: No / Yes (specify)

### Experimental Flow

1. **Welcome & Instructions**
2. **For each condition (3 total)**:
   - Audio priming (10 minutes)
   - Gap detection test (~10-15 minutes)
   - Pitch discrimination test (~10-15 minutes)
   - Break (5 minutes, skippable)
3. **Results summary**

### Controls

- **Spacebar**: Advance through instructions
- **1 / 2**: Respond to hearing tests (interval 1 or 2)
- **Escape**: Quit experiment (saves data collected so far)

## Data Output

### Raw Trial Data

Location: `data/raw/`

Files: `P{ID}_{condition}_{test_type}_{timestamp}.csv`

Columns:
- `participant_id`: Participant identifier
- `condition`: english/german/bilingual
- `test_type`: gap/pitch
- `trial_number`: Sequential trial number
- `stimulus_value`: Gap duration (seconds) or frequency difference (Hz)
- `target_interval`: Which interval (1 or 2) contained the target
- `response_interval`: Participant's response (1 or 2)
- `correct`: Boolean, was response correct
- `reaction_time`: Response time in seconds
- `reversal`: Boolean, was this a staircase reversal trial
- `timestamp`: ISO format timestamp

### Threshold Summaries

Location: `data/processed/`

Files: `P{ID}_thresholds_{timestamp}.csv`

Columns:
- `participant_id`: Participant identifier
- `condition`: english/german/bilingual
- `test_type`: gap/pitch
- `threshold`: Estimated threshold value
- `threshold_unit`: seconds (gap) or Hz (pitch)
- `n_trials`: Total number of trials completed
- `n_reversals`: Number of staircase reversals
- `timestamp`: ISO format timestamp

## Code Structure

```
bilingual-hearing-study/
├── src/
│   ├── config.py              # All experimental parameters
│   ├── staircase.py           # Adaptive staircase implementation
│   ├── stimuli.py             # Psychoacoustic stimulus generation
│   ├── tasks.py               # Gap detection & pitch discrimination tasks
│   └── experiment.py          # Main experimental controller
├── data/
│   ├── audio/                 # Language priming audio files
│   ├── raw/                   # Trial-by-trial data
│   └── processed/             # Threshold summaries
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Methodology

### Gap Detection

- **Stimulus**: Bandpass-filtered noise (100-8000 Hz)
- **Task**: Detect brief silence in center of noise burst
- **Measure**: Minimum detectable gap duration (milliseconds)
- **Interpretation**: Lower threshold = better temporal resolution

### Pitch Discrimination  

- **Stimulus**: Pure tones at 500 Hz reference
- **Task**: Identify which of two tones is higher in pitch
- **Measure**: Minimum detectable frequency difference (Hz)
- **Interpretation**: Lower threshold = better frequency discrimination

### Adaptive Staircase

Both tasks use a 3-down-1-up staircase procedure (Levitt, 1971):
- After 3 consecutive correct responses → stimulus decreases (harder)
- After 1 incorrect response → stimulus increases (easier)
- Converges at 79.4% correct performance
- Threshold calculated as mean of final 6 reversals

## Technical Details

### Audio Backend

- Language priming: macOS `afplay` system command
- Psychoacoustic stimuli: `sounddevice` library
- Sample rate: 44100 Hz

### Visual Design

- Color scheme: Solarized Dark (reduces eye strain)
- Font: Century Gothic
- Window: 1024x768 (configurable in `config.py`)

### Stimulus Generation

- Gap detection: Butterworth 4th-order bandpass filter (100-8000 Hz)
- Pitch discrimination: Pure sine wave generation
- All stimuli: 10ms cosine fade-in/out to prevent clicks

## Troubleshooting

### Audio Not Playing

**Symptom**: No sound during language priming or hearing tests

**Solution**: 
```bash
# Check if sounddevice is installed
pip install sounddevice soundfile

# Test audio output
python -c "import sounddevice as sd; import numpy as np; sd.play(np.sin(2*np.pi*440*np.arange(44100)/44100), 44100); sd.wait()"
```

### Window Not Appearing

**Symptom**: Experiment crashes immediately or window doesn't show

**Solution**: Check PsychoPy installation
```bash
pip uninstall psychopy
pip install psychopy
```

### Data Not Saving

**Symptom**: No CSV files in `data/` directories

**Solution**: Ensure directories exist
```bash
mkdir -p data/raw data/processed data/audio
```

## Author

Ella Capellini  
ecapellini.02@gmail.com

## License

This code is provided for academic and research purposes.
