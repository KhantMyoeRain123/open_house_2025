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
        self.model = "gemini-live-2.5-flash-preview"
        self.tools=[{"function_declarations": tools}]
        
        self.config = {
            "response_modalities": ["AUDIO"],
            "system_instruction": system_instruction,
            "realtime_input_config": {"automatic_activity_detection": {"disabled": True}},
            "tools":self.tools,
            "speech_config": {
            "language_code": "ja-JP"
            }
        }

        self.running = True
        self.conversation_history = []

        self.audio_buffer = []
        self.is_recording = False
        self.is_listening=False
        self.is_replying=False
        self.reset=False
        self.record_event = threading.Event()

        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.dtype = 'int16'  # Native format for Gemini input (16-bit PCM)
        os.makedirs("tmp", exist_ok=True)
        print(sd.query_devices())

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
        while not self.record_event.wait(timeout=0.1):
            if self.reset:
                print("❌ Reset detected while waiting to record.")
                self.is_listening = False
                return b""
        self.audio_buffer.clear()

        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype=self.dtype) as stream:
            while self.record_event.is_set():
                if self.reset:
                    print("❌ Reset detected during recording.")
                    break
                data, _ = stream.read(1024)
                self.audio_buffer.append(data)
                time.sleep(0.01)

        print(f"🎙️ Captured {len(self.audio_buffer)} chunks.")
        audio = np.concatenate(self.audio_buffer, axis=0)
        self.is_listening=False
        self.is_replying=True
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
        
        
        
        '''output_path = "tmp/response.wav"
        wf = wave.open(output_path, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)  # Gemini always outputs 24kHz
        '''
        async for response in session.receive():
            if response.server_content:
                if response.data is not None:
                    #wf.writeframes(response.data)
                    yield response.data
            elif response.tool_call:
                for fc in response.tool_call.function_calls:
                    result=self.call_tool(fc.name,fc.args)
                    function_response = types.FunctionResponse(
                        id=fc.id,
                        name=fc.name,
                        response={ "result": result } # simple, hard-coded function response
                    )
                    await session.send_tool_response(function_responses=[function_response])
                
        print("Written response audio...")
        
        #wf.close()
        
        
        #return output_path


    async def _loop(self):
        queue = asyncio.Queue()
        playback_done_event=asyncio.Event()
        async def playback():
            samplerate = 24000
            blocksize = 4800  # 4800 frames = 0.2s at 24kHz
            block_bytes = blocksize * 2  # 2 bytes per int16 sample (mono)
            write_interval = blocksize / samplerate  # 0.2 seconds

            buffer = bytearray()

            with sd.RawOutputStream(samplerate=samplerate, blocksize=blocksize,
                                    channels=1, dtype='int16') as stream:
                while True:
                    try:
                        # Try to fill buffer for up to `write_interval` seconds
                        while len(buffer) < block_bytes:
                            chunk = await asyncio.wait_for(queue.get(), timeout=write_interval)
                            if chunk is None:
                                if not self.reset:
                                    playback_done_event.set()
                                    continue
                                else:
                                    # Flush remaining buffered audio
                                    if buffer:
                                        stream.write(buffer)
                                        buffer.clear()
                                    playback_done_event.set()
                                    return
                            buffer.extend(chunk)
                    except asyncio.TimeoutError:
                        # No chunk arrived within interval; continue to write silence if needed
                        pass

                    # Write a full block, or pad with silence if not enough data
                    if len(buffer) >= block_bytes:
                        stream.write(buffer[:block_bytes])
                        buffer = buffer[block_bytes:]
                    else:
                        # Pad remaining bytes with silence to reach a full block
                        padding = bytes(block_bytes - len(buffer))
                        stream.write(buffer + padding)
                        buffer.clear()

        while self.running: 
            print("Entering")  
            async with self.client.aio.live.connect(model=self.model, config=self.config) as session:
                playback_task = asyncio.create_task(playback())
                
                while True:
                    if self.reset:
                        print("🔁 Reset requested. Restarting session...")
                        self.reset = False
                        break  # Exit inner loop to reconnect
                    
                    playback_done_event.clear()
                    print("🟢 Chat audio client running.")
                    pcm_bytes = self.listen_to_user()
                    if not self.reset:
                        gen = self.process_user_input(pcm_bytes, session)
                        async for chunk in gen:
                            if self.reset:
                                print("Reset during playback...")
                                await gen.aclose()
                                while not queue.empty():
                                    try:
                                        queue.get_nowait()
                                    except asyncio.QueueEmpty:
                                        break
                                await queue.put(None)
                            else:
                                await queue.put(chunk)
                    
                    await queue.put(None)
                    await playback_done_event.wait()
                    self.is_replying=False
                        
                await queue.put(None)
                await playback_task
                


    def loop(self):
        asyncio.run(self._loop())

    def run(self):
        thread = threading.Thread(target=self.loop, daemon=True)
        thread.start()
