from enum import Enum, auto
import abc
import os
import re
import threading
from time import sleep
from TTS.api import TTS # type: ignore
import pyttsx3
from espeakng import ESpeakNG # type: ignore
import numpy as np
from torch.cuda import is_available
from contextlib import redirect_stdout
import io

class Voice(abc.ABC):
	class VoiceType(Enum):
		ESPEAK = "ESpeak"
		COQUI = "Coqui TTS"
		SYSTEM = "System Voices"

	def __new__(cls, voice_type, init_args=[], name="Unnamed"):
		if cls is Voice:
			if voice_type == cls.VoiceType.ESPEAK:
				return super().__new__(ESpeakVoice)
			elif voice_type == cls.VoiceType.COQUI:
				return super().__new__(CoquiVoice)
			elif voice_type == cls.VoiceType.SYSTEM:
				return super().__new__(SystemVoice)
		else:
			return super().__new__(cls)

	def __init__(self, voice_type, init_args=[], name="Unnamed"):
		self.voice_type = voice_type
		self.name = name
		self.voice_option = None

	@abc.abstractmethod
	def speak(self, text, file_name):
		pass

	def set_speed(self, speed):
		pass

	@abc.abstractmethod
	def set_voice_params(self, voice=None, pitch=None):
		pass

	@abc.abstractmethod
	def list_voice_options(self):
		pass

	def calibrate_rate(self):
		output_path = './output/calibration.wav'
		calibration_phrase_long = "In the early morning light, a vibrant scene unfolds as the quick brown fox jumps gracefully over the lazy dog. The fox's russet fur glistens in the sun, and its swift movements captivate onlookers. With a leap of agility, it soars through the air, showcasing its remarkable prowess. Meanwhile, the dog, relaxed and unperturbed, watches with half-closed eyes, acknowledging the fox's spirited display. The surrounding nature seems to hold its breath, enchanted by this charming spectacle. The gentle rustling of leaves and the distant chirping of birds provide a soothing soundtrack to this magical moment. The two animals, one lively and the other laid-back, showcase the beautiful harmony of nature, an ageless dance that continues to mesmerize all who witness it."
		calibration_phrase_chair = "A chair is a piece of furniture with a raised surface used to sit on, commonly for use by one person. Chairs are most often supported by four legs and have a back; however, a chair can have three legs or could have a different shape. A chair without a back or arm rests is a stool, or when raised up, a bar stool."
		calibration_phrase = "Hello? Testing, testing. Is.. is this thing on? Ah! Hello Gordon! I'm... assuming that's your real name... You wouldn't lie to us. Would you? Well... You finally did it! You survived the resonance cascade! You brought us all to hell and back, alive! You made it to the ultimate birthday bash at the end of the world! You beat the video game! And... now I imagine you'll... shut it down. Move on with your life. Onwards and upwards, ay Gordon? I don't.. know... how much longer I have to send this to you so I'll try to keep it brief. Not my specialty. Perhaps this is presumptuous of me but... Must this really be the end of our time together? Perhaps you could take the science team's data, transfer us somewhere else, hmm? Now... it doesn't have to be Super Punch-Out for the Super Nintendo Entertainment System. Maybe a USB drive, or a spare floppy disk. You could take us with you! We could see the world! We could... I'm getting a little ahead of myself, surely. Welp! The option's always there! You changed our lives, Gordon. I'd like to think it was for the better. And I don't know what's going to happen to us once you exit the game for good. But I know we'll never forget you. I hope you won't forget us. Well... This is where I get off. Goodbye Gordon!"
		self.speak(calibration_phrase, output_path)

	def get_wpm(words, duration):
		return (len(words.split(' ')) / duration * 60)

class ESpeakVoice(Voice):
	def __init__(self, init_args=[], name="Unnamed"):
		super().__init__(Voice.VoiceType.ESPEAK, init_args, name)
		self.set_voice_params(init_args)

	def speak(self, text, file_name):
		self.voice.synth_wav(text, file_name)

	def set_speed(self, speed):
		# current_speaker.set_speed(60*int((len(text.split(' ')) / (sub.end.total_seconds() - sub.start.total_seconds()))))
		self.voice.speed = speed

	def set_voice_params(self, voice=None, pitch=None):
		if voice:
			self.voice.voice = voice
		if pitch:
			self.voice.pitch = pitch

	def list_voice_options(self):
		# Optionally, you can return available voice options for ESpeak here
		pass

class CoquiVoice(Voice):
	def __init__(self, init_args=None, name="Coqui Voice"):
		super().__init__(Voice.VoiceType.COQUI, init_args, name)
		self.voice = TTS().to('cuda' if is_available() else 'cpu')
		self.langs = ["All Languages"] + list({lang.split("/")[1] for lang in self.voice.list_models()})
		self.langs.sort()
		self.selected_lang = 'en'
		self.is_multispeaker = False
		self.speaker = None

	def speak(self, text, file_path=None):
		if file_path:
			return self.voice.tts_to_file(
				text,
				file_path=file_path,
				speaker=self.speaker,
				language= 'en' if self.voice.is_multi_lingual else None
			)
		else:
			return np.array(self.voice.tts(
				text,
				speaker=self.speaker,
				language= 'en' if self.voice.is_multi_lingual else None
			))

	def set_voice_params(self, voice=None, speaker=None, progress=None):
		if voice and voice != self.voice_option:
			if progress:
				progress(0, "downloading")
				self.voice.load_tts_model_by_name(voice)
				progress(-1, "done!")
				# threading.Thread(target=self.voice.load_tts_model_by_name, args=(voice,)).start()
				#  Code for monitoring from STDOUT if I don't get around to making real progress hooks in the coqui repo
				# def extract_progress_info(line):
				# 	# extract params from this line:
				# 	#  26%|████████████████████████████████████▊                                                                                                        | 120M/459M [00:18<01:05, 5.14MiB/s]
				# 	progress_pattern = r'\d+%.*\[\d+[KMG]?/\d+[KMG]?\s.*\]'
				# 	match = re.search(progress_pattern, line)
				# 	if match:
				# 		return match.group(0)
				# 	return None
				
				# def monitor_progress():
				# 	x = 0
				# 	while x != -2:
				# 	f = io.StringIO()
				# 	with redirect_stdout(f):
				# 		help(pow)
				# 	s = f.getvalue()
				# 		progress(x)
				# 		if x == -1:
				# 			x = -2
				# 		sleep(0.1)
			else:
				self.voice.load_tts_model_by_name(voice)
			self.voice_option = self.voice.model_name
		self.is_multispeaker = self.voice.is_multi_speaker
		self.speaker = speaker

	def list_voice_options(self):	
		return self.voice.list_models()

	def is_model_downloaded(self, model_name):
		return os.path.exists(os.path.join(self.voice.manager.output_prefix, self.voice.manager._set_model_item(model_name)[1]))

	def list_speakers(self):
		return self.voice.speakers if self.voice.is_multi_speaker else []

class SystemVoice(Voice):
	def __init__(self, init_args=[], name="Unnamed"):
		super().__init__(Voice.VoiceType.SYSTEM, init_args, name)
		self.voice = pyttsx3.init()
		self.voice_option = self.voice.getProperty('voice')

	def speak(self, text, file_name):
		self.voice.save_to_file(text, file_name)
		self.voice.runAndWait()
		return file_name

	def set_speed(self, speed):
		self.voice.setProperty('rate', speed)

	def set_voice_params(self, voice=None, pitch=None):
		if voice:
			self.voice.setProperty('voice', voice)
			self.voice_option = self.voice.getProperty('voice')

	def list_voice_options(self):
		return [voice.name for voice in self.voice.getProperty('voices')]
