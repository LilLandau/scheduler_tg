import whisper
import ffmpeg
import os

model = whisper.load_model('small')

async def ogg_2_wav(input_path: str, output_path: str):
    try:
        process = (
            ffmpeg
            .input(input_path)
            .output(output_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        out, err = process.communicate()
    except Exception as e:
        print(e)
        raise
    
async def recognize_speech(audio_path: str) -> str:
    result = model.transcribe(audio_path, language='ru')
    return result['text']