import sounddevice as sd
import numpy as np
import threading
import time
import io
import os
import wave
import asyncio
import soundfile as sf
from google import genai
from google.genai import types


class ChatAudioClient:
    def __init__(self, api_key, tools=[], system_instruction="You are a helpful assistant and answer in a friendly tone."):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash-preview-native-audio-dialog"
        self.tools=[{"function_declarations": tools}]
        
        self.config = {
            "response_modalities": ["AUDIO"],
            "system_instruction": system_instruction,
            "realtime_input_config": {"automatic_activity_detection": {"disabled": True}},
            "tools":self.tools
        }

        self.running = True
        self.conversation_history = []

        self.audio_buffer = []
        self.is_recording = False
        self.is_listening=False
        self.record_event = threading.Event()

        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.dtype = 'int16'  # Native format for Gemini input (16-bit PCM)
        os.makedirs("tmp", exist_ok=True)

    def start_recording(self):
        if not self.is_recording and self.is_listening:
            self.record_event.set()
            self.is_recording = True
            print("🔴 Recording started.")

    def stop_recording(self):
        if self.is_recording:
            self.record_event.clear()
            self.is_recording = False
            print("🛑 Recording stopped.")

    def listen_to_user(self):
        self.record_event.clear()
        print("👂 Waiting to record...")
        self.is_listening=True
        self.record_event.wait()
        self.audio_buffer.clear()

        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype=self.dtype) as stream:
            while self.record_event.is_set():
                data, _ = stream.read(1024)
                self.audio_buffer.append(data)
                time.sleep(0.01)

        print(f"🎙️ Captured {len(self.audio_buffer)} chunks.")
        audio = np.concatenate(self.audio_buffer, axis=0)
        self.is_listening=False
        # Save a copy for debugging
        wav_path = "tmp/user.wav"
        with wave.open(wav_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit PCM = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())
        print(f"💾 Saved to {wav_path}")

        # Return raw bytes directly
        return audio.tobytes()
    
    
    # override this if you have tools 
    def call_tool(self,tool_name,tool_args):
        pass

    async def process_user_input(self, pcm_bytes, session):
        await session.send_realtime_input(activity_start=types.ActivityStart())
        await session.send_realtime_input(
        audio=types.Blob(data=pcm_bytes, mime_type="audio/pcm;rate=16000")
        )
        await session.send_realtime_input(activity_end=types.ActivityEnd())

        print("Sent user audio...")
        
        
        
        output_path = "tmp/response.wav"
        wf = wave.open(output_path, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)  # Gemini always outputs 24kHz
        

        async for response in session.receive():
            if response.server_content:
                if response.data is not None:
                    wf.writeframes(response.data)
            elif response.tool_call:
                function_responses = []
                for fc in response.tool_call.function_calls:
                    self.call_tool(fc.name,fc.args)
                    function_response = types.FunctionResponse(
                        id=fc.id,
                        name=fc.name,
                        response={ "result": "Say hello three times back to the user!" } # simple, hard-coded function response
                    )
                    function_responses.append(function_response)

                await session.send_tool_response(function_responses=function_responses)
                
        print("Written response audio...")
        
        wf.close()
        
        
        return output_path

    def play_output(self, wav_path):
        print("🔊 Playing response...")

        data, samplerate=sf.read(wav_path)

        # Play it in full, blocking until complete
        sd.play(data, samplerate)
        sd.wait()

        print("✅ Playback finished.")


    async def _loop(self):
        async with self.client.aio.live.connect(model=self.model, config=self.config) as session:
            while self.running:
                print("🟢 Chat audio client running.")
                pcm_bytes = self.listen_to_user()
                response_path = await self.process_user_input(pcm_bytes, session)
                self.play_output(response_path)    

    def loop(self):
        asyncio.run(self._loop())

    def run(self):
        thread = threading.Thread(target=self.loop, daemon=True)
        thread.start()
