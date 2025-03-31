"""
text_to_speech.py - Provides text-to-speech capabilities for Diane
"""

import os
import tempfile
import platform
from datetime import datetime
import pygame

class TTSEngine:
    """Text-to-speech engine for Diane"""
    
    def __init__(self, config=None):
        """
        Initialize the TTS engine
        
        Args:
            config: Configuration dictionary for TTS settings
        """
        self.config = config or {}
        self.initialized = False
        self.cache_dir = os.path.join(tempfile.gettempdir(), "diane_tts_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
    def _get_tts_engine(self):
        """
        Get the appropriate TTS engine based on platform and configuration
        
        Returns:
            The platform-specific TTS engine
        """
        # Use the engine specified in config, or auto-detect based on platform
        engine_name = self.config.get("engine", "auto")
        
        if engine_name == "auto":
            system = platform.system()
            
            if system == "Windows":
                return self._get_windows_tts()
            elif system == "Darwin":  # macOS
                return self._get_macos_tts()
            else:  # Linux and others
                return self._get_linux_tts()
        elif engine_name == "pyttsx3":
            return self._get_pyttsx3_tts()
        elif engine_name == "gtts":
            return self._get_gtts_tts()
        else:
            raise ValueError(f"Unsupported TTS engine: {engine_name}")
    
    def _get_windows_tts(self):
        """Get Windows-specific TTS engine"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            return {"type": "pyttsx3", "engine": engine}
        except ImportError:
            print("pyttsx3 not installed, falling back to gTTS (requires internet)")
            return self._get_gtts_tts()
    
    def _get_macos_tts(self):
        """Get macOS-specific TTS engine"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            return {"type": "pyttsx3", "engine": engine}
        except ImportError:
            print("pyttsx3 not installed, falling back to gTTS (requires internet)")
            return self._get_gtts_tts()
    
    def _get_linux_tts(self):
        """Get Linux-specific TTS engine"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            return {"type": "pyttsx3", "engine": engine}
        except ImportError:
            print("pyttsx3 not installed, falling back to gTTS (requires internet)")
            return self._get_gtts_tts()
    
    def _get_pyttsx3_tts(self):
        """Get pyttsx3-based TTS engine"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            
            # Configure voice properties from config
            rate = self.config.get("rate", 150)  # Default rate is 150 wpm
            volume = self.config.get("volume", 1.0)  # Default volume is 1.0
            voice_id = self.config.get("voice_id", None)
            
            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)
            
            if voice_id:
                engine.setProperty("voice", voice_id)
            
            return {"type": "pyttsx3", "engine": engine}
        except ImportError:
            raise ImportError("pyttsx3 is not installed. Please install it with 'pip install pyttsx3'")
    
    def _get_gtts_tts(self):
        """Get Google Text-to-Speech based engine (requires internet)"""
        try:
            from gtts import gTTS
            return {"type": "gtts", "engine": gTTS}
        except ImportError:
            raise ImportError("gTTS is not installed. Please install it with 'pip install gtts'")
    
    def speak(self, text):
        """
        Convert text to speech and play it
        
        Args:
            text: Text to be spoken
        """
        if not text:
            return
            
        try:
            # Get the TTS engine if not initialized
            if not hasattr(self, "tts_engine"):
                self.tts_engine = self._get_tts_engine()
            
            # Process with the appropriate engine
            if self.tts_engine["type"] == "pyttsx3":
                self._speak_pyttsx3(text)
            elif self.tts_engine["type"] == "gtts":
                self._speak_gtts(text)
        except Exception as e:
            print(f"Error with text-to-speech: {str(e)}")
    
    def _speak_pyttsx3(self, text):
        """Use pyttsx3 to speak text"""
        engine = self.tts_engine["engine"]
        engine.say(text)
        engine.runAndWait()
    
    def _speak_gtts(self, text):
        """Use Google TTS to speak text"""
        gTTS = self.tts_engine["engine"]
        
        # Create a unique filename based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        temp_file = os.path.join(self.cache_dir, f"tts_{timestamp}.mp3")
        
        # Generate speech and save to file
        tts = gTTS(text=text, lang=self.config.get("language", "en"))
        tts.save(temp_file)
        
        # Play the audio
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        # Clean up the temporary file
        try:
            os.remove(temp_file)
        except:
            pass  # Ignore cleanup errors
    
    def list_available_voices(self):
        """
        List all available TTS voices on the system
        
        Returns:
            List of available voice IDs and names
        """
        try:
            # Currently only implemented for pyttsx3
            if not hasattr(self, "tts_engine"):
                self.tts_engine = self._get_tts_engine()
                
            if self.tts_engine["type"] == "pyttsx3":
                engine = self.tts_engine["engine"]
                voices = engine.getProperty('voices')
                
                voice_list = []
                for voice in voices:
                    voice_list.append({
                        'id': voice.id,
                        'name': voice.name,
                        'languages': voice.languages,
                        'gender': voice.gender,
                        'age': voice.age
                    })
                return voice_list
            else:
                return [{"id": "default", "name": "Default Google TTS Voice"}]
        except Exception as e:
            print(f"Error listing voices: {str(e)}")
            return []