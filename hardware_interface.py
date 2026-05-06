"""
Hardware Interface Module - Real speaker/haptic output drivers for embedded systems.
Supports Raspberry Pi GPIO, I2S audio, and fallback implementations for testing.
"""

import os
import sys
import time
import threading
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Platform Detection
# ============================================================================

class PlatformType(Enum):
    RASPBERRY_PI = "raspberry_pi"
    DESKTOP_WINDOWS = "desktop_windows"
    DESKTOP_LINUX = "desktop_linux"
    DESKTOP_MAC = "desktop_mac"
    UNKNOWN = "unknown"


def detect_platform():
    """Detect the current platform for hardware initialization."""
    if sys.platform.startswith('linux'):
        try:
            # Check if this is Raspberry Pi
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().strip()
                if 'Raspberry Pi' in model or 'BCM' in model:
                    return PlatformType.RASPBERRY_PI
        except FileNotFoundError:
            pass
        return PlatformType.DESKTOP_LINUX
    elif sys.platform == 'win32':
        return PlatformType.DESKTOP_WINDOWS
    elif sys.platform == 'darwin':
        return PlatformType.DESKTOP_MAC
    return PlatformType.UNKNOWN


CURRENT_PLATFORM = detect_platform()

# ============================================================================
# Haptic Driver (GPIO/Vibration Motor)
# ============================================================================

class HapticDriver:
    """Base class for haptic feedback drivers."""
    
    def vibrate(self, duration_ms=150):
        """Trigger vibration for specified duration (ms)."""
        raise NotImplementedError
    
    def stop(self):
        """Stop any ongoing vibration immediately."""
        raise NotImplementedError
    
    def close(self):
        """Cleanup resources."""
        pass


class RPiGPIOHapticDriver(HapticDriver):
    """
    Raspberry Pi GPIO-based haptic driver for vibration motors.
    
    Requires:
    - RPi.GPIO library or gpiozero library
    - Motor connected to GPIO pin (default: GPIO17, pin 11)
    - Optional: PWM control for varying intensity
    """
    
    def __init__(self, gpio_pin=17, frequency_hz=50):
        """
        Initialize Raspberry Pi GPIO haptic driver.
        
        Args:
            gpio_pin: GPIO pin number for vibration motor (default: 17)
            frequency_hz: PWM frequency (default: 50 Hz)
        """
        self.gpio_pin = gpio_pin
        self.frequency_hz = frequency_hz
        self.pwm = None
        self.gpio = None
        self.is_vibrating = False
        self.vibration_thread = None
        
        try:
            import RPi.GPIO as GPIO
            self.gpio = GPIO
            self.gpio.setmode(GPIO.BCM)
            self.gpio.setup(self.gpio_pin, GPIO.OUT)
            self.pwm = self.gpio.PWM(self.gpio_pin, self.frequency_hz)
            logger.info(f"✅ RPi GPIO Haptic Driver initialized on pin {gpio_pin}")
        except ImportError:
            logger.warning("⚠️ RPi.GPIO not available. Install with: pip install RPi.GPIO")
            self.gpio = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize GPIO: {e}")
            self.gpio = None
    
    def vibrate(self, duration_ms=150):
        """Vibrate for specified duration using PWM."""
        if self.gpio is None or self.pwm is None:
            logger.debug(f"[HAPTIC-FALLBACK] Vibrate for {duration_ms}ms (GPIO not available)")
            return
        
        try:
            if self.is_vibrating:
                return  # Already vibrating
            
            self.is_vibrating = True
            
            def _vibrate_thread():
                try:
                    self.pwm.start(75)  # 75% duty cycle for strong vibration
                    time.sleep(duration_ms / 1000.0)
                    self.pwm.stop()
                    self.is_vibrating = False
                    logger.debug(f"✓ Haptic vibration complete ({duration_ms}ms)")
                except Exception as e:
                    logger.error(f"Vibration error: {e}")
                    self.is_vibrating = False
            
            self.vibration_thread = threading.Thread(target=_vibrate_thread, daemon=True)
            self.vibration_thread.start()
        except Exception as e:
            logger.error(f"❌ Vibration failed: {e}")
            self.is_vibrating = False
    
    def stop(self):
        """Stop vibration immediately."""
        if self.pwm is not None:
            try:
                self.pwm.stop()
                self.is_vibrating = False
                logger.debug("✓ Haptic vibration stopped")
            except Exception as e:
                logger.error(f"Failed to stop vibration: {e}")
    
    def close(self):
        """Cleanup GPIO resources."""
        if self.gpio is not None:
            try:
                self.stop()
                self.gpio.cleanup(self.gpio_pin)
                logger.info("✓ GPIO resources cleaned up")
            except Exception as e:
                logger.error(f"Cleanup error: {e}")


class FallbackHapticDriver(HapticDriver):
    """Fallback haptic driver for systems without hardware (prints vibration events)."""
    
    def __init__(self):
        logger.info("ℹ️ Using fallback haptic driver (no hardware)")
    
    def vibrate(self, duration_ms=150):
        """Log vibration event (no actual hardware control)."""
        print(f"[HAPTIC] Vibrate for {duration_ms}ms")
    
    def stop(self):
        """No-op for fallback."""
        pass


# ============================================================================
# Speaker Driver (Audio Output)
# ============================================================================

class SpeakerDriver:
    """Base class for speaker/audio output drivers."""
    
    def speak(self, message):
        """Play text-to-speech message."""
        raise NotImplementedError
    
    def play_tone(self, frequency_hz=1000, duration_ms=100):
        """Play a simple tone (for alerts)."""
        raise NotImplementedError
    
    def close(self):
        """Cleanup resources."""
        pass


class PyTTSXSpeakerDriver(SpeakerDriver):
    """
    pyttsx3-based text-to-speech driver.
    Works on all platforms (Windows, Linux, macOS).
    """
    
    def __init__(self, rate=150):
        """
        Initialize pyttsx3 TTS engine.
        
        Args:
            rate: Speech rate (words per minute, default: 150)
        """
        self.rate = rate
        self.engine = None
        
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', rate)
            # Try to set voice to female if available
            voices = self.engine.getProperty('voices')
            if len(voices) > 1:
                self.engine.setProperty('voice', voices[1].id)
            logger.info(f"✅ TTS Speaker initialized (pyttsx3, rate={rate} wpm)")
        except Exception as e:
            logger.warning(f"⚠️ pyttsx3 TTS failed to initialize: {e}")
            self.engine = None
    
    def speak(self, message):
        """Speak message using TTS."""
        if self.engine is not None:
            try:
                self.engine.say(message)
                self.engine.runAndWait()
                logger.debug(f"✓ TTS: {message[:50]}...")
            except Exception as e:
                logger.error(f"TTS error: {e}")
                print(f"[SPEAKER] {message}")
        else:
            print(f"[SPEAKER] {message}")
    
    def play_tone(self, frequency_hz=1000, duration_ms=100):
        """Play a tone using TTS (buzzing sound)."""
        if self.engine is not None:
            # Play a simple beep using TTS
            self.engine.say("beep")
            self.engine.runAndWait()
        else:
            print(f"[TONE] {frequency_hz}Hz for {duration_ms}ms")
    
    def close(self):
        """Cleanup TTS resources."""
        if self.engine is not None:
            self.engine.stop()


class I2SSpeakerDriver(SpeakerDriver):
    """
    I2S audio driver for Raspberry Pi with external I2S speaker.
    Requires: alsa-utils, speaker-test, or PyAudio
    """
    
    def __init__(self, i2s_device="default"):
        """
        Initialize I2S speaker driver.
        
        Args:
            i2s_device: ALSA device name (default: "default")
        """
        self.i2s_device = i2s_device
        self.has_alsa = False
        
        try:
            import subprocess
            result = subprocess.run(['which', 'aplay'], capture_output=True)
            self.has_alsa = result.returncode == 0
            if self.has_alsa:
                logger.info(f"✅ I2S Speaker driver initialized (ALSA device: {i2s_device})")
            else:
                logger.warning("⚠️ ALSA aplay not found. Install with: sudo apt-get install alsa-utils")
        except Exception as e:
            logger.warning(f"⚠️ I2S driver initialization failed: {e}")
    
    def speak(self, message):
        """Speak using festival TTS and I2S output."""
        if not self.has_alsa:
            print(f"[SPEAKER] {message}")
            return
        
        try:
            import subprocess
            # Use festival TTS if available
            process = subprocess.Popen(
                ['festival', '--tts'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.communicate(input=message.encode())
            logger.debug(f"✓ Festival TTS: {message[:50]}...")
        except FileNotFoundError:
            logger.warning("Festival TTS not found. Install with: sudo apt-get install festival")
            print(f"[SPEAKER] {message}")
        except Exception as e:
            logger.error(f"I2S speaker error: {e}")
            print(f"[SPEAKER] {message}")
    
    def play_tone(self, frequency_hz=1000, duration_ms=100):
        """Play a tone via I2S."""
        if not self.has_alsa:
            print(f"[TONE] {frequency_hz}Hz for {duration_ms}ms")
            return
        
        try:
            import subprocess
            # Use speaker-test for tone generation
            speaker_test_cmd = [
                'speaker-test',
                '-c', '2',
                '-l', '1',
                '-f', str(frequency_hz),
                '-t', 'sine'
            ]
            subprocess.run(speaker_test_cmd, timeout=duration_ms / 1000.0, capture_output=True)
            logger.debug(f"✓ Tone: {frequency_hz}Hz for {duration_ms}ms")
        except Exception as e:
            logger.error(f"Tone playback error: {e}")
            print(f"[TONE] {frequency_hz}Hz for {duration_ms}ms")


class FallbackSpeakerDriver(SpeakerDriver):
    """Fallback speaker driver for systems without audio (prints output)."""
    
    def __init__(self):
        logger.info("ℹ️ Using fallback speaker driver (console output only)")
    
    def speak(self, message):
        """Print message to console."""
        print(f"[SPEAKER] {message}")
    
    def play_tone(self, frequency_hz=1000, duration_ms=100):
        """Print tone info."""
        print(f"[TONE] {frequency_hz}Hz for {duration_ms}ms")


# ============================================================================
# Hardware Interface Factory
# ============================================================================

class HardwareInterface:
    """
    Main interface for all hardware I/O (speaker + haptic).
    Automatically selects appropriate drivers based on platform.
    """
    
    def __init__(self, platform=None, haptic_gpio_pin=17):
        """
        Initialize hardware interface.
        
        Args:
            platform: PlatformType override (auto-detect if None)
            haptic_gpio_pin: GPIO pin for vibration motor (RPi only)
        """
        self.platform = platform or CURRENT_PLATFORM
        
        # Initialize speaker
        self.speaker = self._init_speaker()
        
        # Initialize haptic
        self.haptic = self._init_haptic(haptic_gpio_pin)
        
        logger.info(f"🔧 Hardware Interface initialized on {self.platform.value}")
    
    def _init_speaker(self):
        """Initialize appropriate speaker driver for platform."""
        if self.platform == PlatformType.RASPBERRY_PI:
            try:
                # Try I2S first, fallback to TTS
                i2s_driver = I2SSpeakerDriver()
                if i2s_driver.has_alsa:
                    return i2s_driver
            except Exception as e:
                logger.debug(f"I2S init failed: {e}")
            
            # Fallback to TTS on RPi
            tts_driver = PyTTSXSpeakerDriver()
            return tts_driver if tts_driver.engine else FallbackSpeakerDriver()
        else:
            # Desktop platforms: use TTS
            tts_driver = PyTTSXSpeakerDriver()
            return tts_driver if tts_driver.engine else FallbackSpeakerDriver()
    
    def _init_haptic(self, gpio_pin):
        """Initialize appropriate haptic driver for platform."""
        if self.platform == PlatformType.RASPBERRY_PI:
            try:
                gpio_driver = RPiGPIOHapticDriver(gpio_pin=gpio_pin)
                return gpio_driver if gpio_driver.gpio is not None else FallbackHapticDriver()
            except Exception as e:
                logger.debug(f"GPIO init failed: {e}")
                return FallbackHapticDriver()
        else:
            # Desktop platforms: fallback driver
            return FallbackHapticDriver()
    
    def speak(self, message):
        """Speak a message via speaker."""
        self.speaker.speak(message)
    
    def vibrate(self, duration_ms=150):
        """Trigger haptic vibration."""
        self.haptic.vibrate(duration_ms)
    
    def alert(self, message, severity="caution"):
        """
        Combined audio + haptic alert with severity-based timing.
        
        Args:
            message: Alert message to speak
            severity: 'critical' | 'warning' | 'caution' | 'info'
        """
        # Haptic timing based on severity
        severity_timings = {
            "critical": 300,   # 300ms strong vibration
            "warning": 200,    # 200ms vibration
            "caution": 150,    # 150ms vibration
            "info": 100,       # 100ms vibration
        }
        duration = severity_timings.get(severity, 150)
        
        # Trigger haptic in background
        self.vibrate(duration)
        
        # Speak message
        self.speak(message)
    
    def tone(self, frequency_hz=1000, duration_ms=100):
        """Play a simple tone (useful for non-verbal alerts)."""
        self.speaker.play_tone(frequency_hz, duration_ms)
    
    def close(self):
        """Cleanup all hardware resources."""
        try:
            self.speaker.close()
            self.haptic.close()
            logger.info("✓ Hardware interface closed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# ============================================================================
# Convenience Functions
# ============================================================================

_hardware_interface = None


def init_hardware(platform=None, gpio_pin=17):
    """
    Initialize global hardware interface.
    
    Args:
        platform: PlatformType override
        gpio_pin: GPIO pin for haptic (RPi only)
    
    Returns:
        HardwareInterface instance
    """
    global _hardware_interface
    _hardware_interface = HardwareInterface(platform=platform, haptic_gpio_pin=gpio_pin)
    return _hardware_interface


def get_hardware():
    """Get the global hardware interface (initializes if needed)."""
    global _hardware_interface
    if _hardware_interface is None:
        _hardware_interface = HardwareInterface()
    return _hardware_interface


def speak(message):
    """Convenience: speak a message via global hardware interface."""
    get_hardware().speak(message)


def vibrate(duration_ms=150):
    """Convenience: vibrate via global hardware interface."""
    get_hardware().vibrate(duration_ms)


def alert(message, severity="caution"):
    """Convenience: combined audio + haptic alert."""
    get_hardware().alert(message, severity)


def tone(frequency_hz=1000, duration_ms=100):
    """Convenience: play a tone via global hardware interface."""
    get_hardware().tone(frequency_hz, duration_ms)


def close_hardware():
    """Cleanup global hardware interface."""
    global _hardware_interface
    if _hardware_interface is not None:
        _hardware_interface.close()
        _hardware_interface = None


if __name__ == "__main__":
    """Test hardware interface."""
    print(f"Platform detected: {CURRENT_PLATFORM.value}\n")
    
    # Initialize
    hw = init_hardware()
    
    # Test speaker
    print("Testing speaker...")
    hw.speak("System online. Speaker test.")
    time.sleep(1)
    
    # Test haptic
    print("Testing haptic feedback...")
    hw.vibrate(150)
    time.sleep(1)
    
    # Test combined alert
    print("Testing alert system...")
    hw.alert("Danger: Person directly ahead", severity="critical")
    time.sleep(2)
    
    hw.alert("Warning: Object on your right", severity="warning")
    time.sleep(2)
    
    hw.alert("Caution: Uneven surface ahead", severity="caution")
    time.sleep(2)
    
    # Cleanup
    close_hardware()
    print("\nHardware interface test complete.")
