"""
Psychoacoustic Stimulus Generation
Generates gap detection and pitch discrimination stimuli using numpy/scipy.
"""
import numpy as np
from scipy import signal
from typing import Tuple
import logging

from config import (
    SAMPLE_RATE,
    GAP_NOISE_DURATION,
    GAP_NOISE_LOWCUT,
    GAP_NOISE_HIGHCUT,
    GAP_NOISE_AMPLITUDE,
    PITCH_TONE_DURATION,
    PITCH_TONE_AMPLITUDE,
    FADE_DURATION
)

logger = logging.getLogger(__name__)


class StimulusGenerator:
    """Generates psychoacoustic test stimuli."""
    
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        """
        Initialize stimulus generator.
        
        Parameters
        ----------
        sample_rate : int
            Audio sampling rate in Hz
        """
        self.sample_rate = sample_rate
        self.fade_samples = int(FADE_DURATION * sample_rate)
        logger.info(f"StimulusGenerator initialized (fs={sample_rate} Hz)")
    
    def generate_gap_stimulus(
        self,
        gap_duration: float,
        has_gap: bool
    ) -> np.ndarray:
        """
        Generate gap detection stimulus.
        
        Creates bandpass-filtered noise (100-8000 Hz) with optional gap in center.
        
        Parameters
        ----------
        gap_duration : float
            Duration of gap in seconds
        has_gap : bool
            Whether to insert gap in center of noise burst
        
        Returns
        -------
        np.ndarray
            Audio signal (mono)
        """
        # Calculate durations
        noise_duration = GAP_NOISE_DURATION
        total_duration = noise_duration + gap_duration if has_gap else noise_duration
        n_samples = int(total_duration * self.sample_rate)
        
        if has_gap:
            # Generate two noise segments with gap in between
            segment_duration = noise_duration / 2
            segment_samples = int(segment_duration * self.sample_rate)
            gap_samples = int(gap_duration * self.sample_rate)
            
            # First segment
            noise1 = self._generate_bandpass_noise(segment_samples)
            
            # Gap (silence)
            gap = np.zeros(gap_samples)
            
            # Second segment
            noise2 = self._generate_bandpass_noise(segment_samples)
            
            # Concatenate
            signal_out = np.concatenate([noise1, gap, noise2])
        else:
            # Continuous noise (no gap)
            signal_out = self._generate_bandpass_noise(n_samples)
        
        # Apply amplitude scaling
        signal_out = signal_out * GAP_NOISE_AMPLITUDE
        
        # Apply fade in/out to prevent clicks
        signal_out = self._apply_fade(signal_out)
        
        return signal_out
    
    def generate_pitch_stimulus(
        self,
        frequency: float,
        duration: float = PITCH_TONE_DURATION
    ) -> np.ndarray:
        """
        Generate pure tone for pitch discrimination.
        
        Parameters
        ----------
        frequency : float
            Tone frequency in Hz
        duration : float
            Tone duration in seconds
        
        Returns
        -------
        np.ndarray
            Audio signal (mono)
        """
        n_samples = int(duration * self.sample_rate)
        t = np.arange(n_samples) / self.sample_rate
        
        # Generate sine wave
        signal_out = PITCH_TONE_AMPLITUDE * np.sin(2 * np.pi * frequency * t)
        
        # Apply fade in/out
        signal_out = self._apply_fade(signal_out)
        
        return signal_out
    
    def _generate_bandpass_noise(self, n_samples: int) -> np.ndarray:
        """
        Generate bandpass-filtered white noise.
        
        Filters noise between 100-8000 Hz to match speech frequency range,
        as specified in the paper.
        
        Parameters
        ----------
        n_samples : int
            Number of samples to generate
        
        Returns
        -------
        np.ndarray
            Filtered noise signal
        """
        # Generate white noise
        noise = np.random.randn(n_samples)
        
        # Design bandpass filter (Butterworth, 4th order)
        nyquist = self.sample_rate / 2
        low = GAP_NOISE_LOWCUT / nyquist
        high = GAP_NOISE_HIGHCUT / nyquist
        
        b, a = signal.butter(4, [low, high], btype='band')
        
        # Apply filter
        filtered = signal.filtfilt(b, a, noise)
        
        # Normalize to prevent clipping
        filtered = filtered / np.max(np.abs(filtered))
        
        return filtered
    
    def _apply_fade(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply fade in/out to prevent clicks.
        
        Parameters
        ----------
        audio : np.ndarray
            Input audio signal
        
        Returns
        -------
        np.ndarray
            Audio with fades applied
        """
        audio_out = audio.copy()
        fade_samples = min(self.fade_samples, len(audio) // 4)
        
        # Fade in
        fade_in = np.linspace(0, 1, fade_samples)
        audio_out[:fade_samples] *= fade_in
        
        # Fade out
        fade_out = np.linspace(1, 0, fade_samples)
        audio_out[-fade_samples:] *= fade_out
        
        return audio_out
    
    def create_trial_pair(
        self,
        test_type: str,
        stimulus_value: float,
        target_interval: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create a pair of stimuli for a 2-interval forced choice trial.
        
        Parameters
        ----------
        test_type : str
            'gap' or 'pitch'
        stimulus_value : float
            Gap duration (seconds) or frequency difference (Hz)
        target_interval : int
            Which interval contains target (1 or 2)
        
        Returns
        -------
        tuple of np.ndarray
            (interval_1_audio, interval_2_audio)
        """
        if test_type == 'gap':
            # Gap detection: one interval has gap, other is continuous
            stim1 = self.generate_gap_stimulus(
                stimulus_value,
                has_gap=(target_interval == 1)
            )
            stim2 = self.generate_gap_stimulus(
                stimulus_value,
                has_gap=(target_interval == 2)
            )
        
        elif test_type == 'pitch':
            # Pitch discrimination: one interval is reference, other is reference + difference
            from config import PITCH_REFERENCE_FREQ
            
            freq1 = PITCH_REFERENCE_FREQ + stimulus_value if target_interval == 1 else PITCH_REFERENCE_FREQ
            freq2 = PITCH_REFERENCE_FREQ + stimulus_value if target_interval == 2 else PITCH_REFERENCE_FREQ
            
            stim1 = self.generate_pitch_stimulus(freq1)
            stim2 = self.generate_pitch_stimulus(freq2)
        
        else:
            raise ValueError(f"Unknown test_type: {test_type}")
        
        return stim1, stim2
    
    def normalize_audio(self, audio: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
        """
        Normalize audio to target RMS level.
        
        Parameters
        ----------
        audio : np.ndarray
            Input audio
        target_rms : float
            Target RMS amplitude (0-1)
        
        Returns
        -------
        np.ndarray
            Normalized audio
        """
        current_rms = np.sqrt(np.mean(audio ** 2))
        if current_rms > 0:
            scaling = target_rms / current_rms
            return audio * scaling
        return audio