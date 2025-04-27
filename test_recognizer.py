import asyncio
from recognizer import ogg_2_wav, recognize_speech
import os

async def test_recognizer():
    ogg_file = './audio_2025-04-27_04-07-28.ogg'
    wav_file = './audio_2025-04-27_04-07-28.wav'
    
    await ogg_2_wav(ogg_file, wav_file)
    
    text = await recognize_speech(wav_file)
    print(text)
    
    
if __name__ == '__main__':
    asyncio.run(test_recognizer())