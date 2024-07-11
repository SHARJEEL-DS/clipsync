# coding=utf8
from gtts import gTTS # type: ignore
import gradio as gr # type: ignore
import os
import speech_recognition as sr
from googletrans import Translator, constants # type: ignore
from pprint import pprint
from moviepy.editor import *
def video_to_translate(file_obj,initial_language,final_language):

    videoclip = VideoFileClip(file_obj.name)
    
    videoclip.audio.write_audiofile("test.wav",codec='pcm_s16le')

    r = sr.Recognizer()

    if initial_language == "English":
        lang_in='en-US'
    elif initial_language == "hindi":
        lang_in='hi-IN'
    elif initial_language == "Japanese":
        lang_in='ja-JP'

    with sr.AudioFile("test.wav") as source:
        
        audio_data = r.record(source)
        
        text = r.recognize_google(audio_data, language = lang_in)

    if final_language == "English":
        lang='en'
    elif final_language == "hindi":
        lang='hi'
    elif final_language == "Japanese":
        lang='ja'               
    print(lang)
    
    translator = Translator()
    translation = translator.translate(text, dest=lang)
    
    trans=translation.text
    myobj = gTTS(text=trans, lang=lang, slow=False) 
    myobj.save("audio.wav") 
    
    audioclip = AudioFileClip("audio.wav")
    
    new_audioclip = CompositeAudioClip([audioclip])
    videoclip.audio = new_audioclip
    new_video="video_translated_"+lang+".mp4"
    videoclip.write_videofile(new_video)
   
    return new_video

initial_language = gr.inputs.Dropdown(["English","Japanese","hindi"])
final_language = gr.inputs.Dropdown([ "japanse","English","hindi"])


gr.Interface(fn = video_to_translate,
            inputs = ['file',initial_language,final_language],
            outputs = 'video', 
            
            verbose = True,
            title = 'clipsynce',
            description = '',
            article = 
                        '''<div>
                            
                        </div>''',
            examples=[['obama.mp4',"English",'Spanish'],
                      ['obama.mp4',"English",'Italian'],
                      ['obama.mp4',"English",'German'],
                      ['obama.mp4',"English",'Japanese']
                    ]         
            ).launch()