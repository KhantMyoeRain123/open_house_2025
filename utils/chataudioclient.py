import asyncio
import os
import threading
import time
import wave

import numpy as np
import sounddevice as sd
import soundfile as sf
from google import genai
from google.genai import types


class ChatAudioClient:
    def __init__(
        self, api_key, tools=[], system_instruction="You are a helpful assistant and answer in a friendly tone."
    ):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-live-2.5-flash-preview"
        self.tools = [{"function_declarations": tools}]

        self.config = {
            "response_modalities": ["AUDIO"],
            "system_instruction": system_instruction,
            "realtime_input_config": {"automatic_activity_detection": {"disabled": True}},
            "tools": self.tools,
            "speech_config": {"language_code": "ja-JP"},
        }

        self.running = True

        self.audio_buffer = []
        self.is_recording = False
        self.is_listening = False
        self.is_processing = False
        self.is_speaking = False
        self.record_event = threading.Event()

        # UI callback
        self.ui_callback = None

        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.dtype = "int16"  # Native format for Gemini input (16-bit PCM)
        os.makedirs("tmp", exist_ok=True)

    def set_ui_callback(self, callback):
        """UIコールバック関数を設定"""
        self.ui_callback = callback

    def notify_ui(self, event, data=None):
        """UIに状態変化を通知"""
        if self.ui_callback:
            self.ui_callback(event, data)

    def start_recording(self):
        if not self.is_recording and self.is_listening:
            self.record_event.set()
            self.is_recording = True
            self.notify_ui("recording_started")
            print("🔴 Recording started.")

    def stop_recording(self):
        if self.is_recording:
            self.record_event.clear()
            self.is_recording = False
            self.notify_ui("recording_stopped")
            print("⏹️ Recording stopped.")

    def listen_to_user(self):
        self.record_event.clear()
        print("👂 Waiting to record...")
        self.is_listening = True
        self.notify_ui("listening_started")
        self.record_event.wait()
        self.audio_buffer.clear()

        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype=self.dtype) as stream:
            while self.record_event.is_set():
                data, _ = stream.read(1024)
                self.audio_buffer.append(data)
                time.sleep(0.01)

        print(f"🎙️ Captured {len(self.audio_buffer)} chunks.")
        audio = np.concatenate(self.audio_buffer, axis=0)
        self.is_listening = False
        self.notify_ui("listening_finished")
        # Save a copy for debugging
        wav_path = "tmp/user.wav"
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit PCM = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())
        print(f"💾 Saved to {wav_path}")

        # Return raw bytes directly
        return audio.tobytes()

    # override this if you have tools
    def call_tool(self, tool_name, tool_args):
        pass

    async def process_user_input(self, pcm_bytes, session):
        self.is_processing = True
        self.notify_ui("processing_started")

        await session.send_realtime_input(activity_start=types.ActivityStart())
        await session.send_realtime_input(audio=types.Blob(data=pcm_bytes, mime_type="audio/pcm;rate=16000"))
        await session.send_realtime_input(activity_end=types.ActivityEnd())

        print("Sent user audio...")

        """output_path = "tmp/response.wav"
        wf = wave.open(output_path, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)  # Gemini always outputs 24kHz
        """

        async for response in session.receive():
            if response.server_content:
                if response.data is not None:
                    # wf.writeframes(response.data)
                    yield response.data
            elif response.tool_call:
                for fc in response.tool_call.function_calls:
                    result = self.call_tool(fc.name, fc.args)
                    function_response = types.FunctionResponse(
                        id=fc.id,
                        name=fc.name,
                        response={"result": result},  # simple, hard-coded function response
                    )
                    await session.send_tool_response(function_responses=[function_response])

        print("Written response audio...")

        # wf.close()

        # return output_path

    def play_output(self, wav_path):
        print("🔊 Playing response...")

        data, samplerate = sf.read(wav_path)

        # Play it in full, blocking until complete
        sd.play(data, samplerate)
        sd.wait()

        print("✅ Playback finished.")

    async def _loop(self):
        queue = asyncio.Queue()
        playback_done_event = asyncio.Event()

        async def playback():
            """
            音声チャンクをバッファリングし、一定のブロックサイズで再生する。
            これにより、音声の途切れ（アンダーラン）を防ぎ、再生を安定させる。
            """
            samplerate = 24000
            blocksize = 4800  # 4800フレーム = 24000 Hzで0.2秒
            block_bytes = blocksize * 2  # int16は2バイト/サンプル
            write_interval = blocksize / samplerate  # 0.2秒

            buffer = bytearray()

            with sd.RawOutputStream(samplerate=samplerate, blocksize=blocksize, channels=1, dtype="int16") as stream:
                while True:
                    try:
                        # 次のブロックを書き込むのに十分なデータがバッファに溜まるまで待つ
                        while len(buffer) < block_bytes:
                            # タイムアウト付きでキューからチャンクを取得
                            chunk = await asyncio.wait_for(queue.get(), timeout=write_interval * 2)

                            if chunk is None:
                                # 発話終了の合図(None)を受け取った
                                # バッファに残っているデータを再生する
                                if buffer:
                                    stream.write(buffer)
                                    buffer.clear()

                                playback_done_event.set()  # メインループに再生完了を通知

                                if not self.running:
                                    return  # アプリケーション全体が終了する場合、タスクを終了
                                else:
                                    # アプリは続行中。次の発話を待つためにループを続ける
                                    continue

                            buffer.extend(chunk)

                    except asyncio.TimeoutError:
                        # 新しい音声チャンクが時間内に届かなかった場合（例：ネットワーク遅延）
                        # バッファにデータが残っていれば、無音でパディングして再生する
                        if buffer:
                            padding = bytes(block_bytes - len(buffer))
                            stream.write(buffer + padding)
                            buffer.clear()
                        # バッファが空なら何もしない（無音を再生し続けることになる）
                        continue

                    # バッファから1ブロック分のデータを書き出す
                    stream.write(buffer[:block_bytes])
                    # 書き出した分をバッファから削除
                    buffer = buffer[block_bytes:]

        # --- メインループ (最初のコードのロジックを維持) ---
        async with self.client.aio.live.connect(model=self.model, config=self.config) as session:
            playback_task = asyncio.create_task(playback())

            while self.running:
                playback_done_event.clear()
                print("🟢 Chat audio client running.")

                # 各サイクル開始時に状態をリセット
                self.is_processing = False
                self.is_speaking = False

                pcm_bytes = self.listen_to_user()

                # ここで is_processing = True を設定するのが一般的
                # self.is_processing = True
                # self.notify_ui("processing_started")

                response_started = False

                async for chunk in self.process_user_input(pcm_bytes, session):
                    if not response_started:
                        # 最初のレスポンスチャンクを受け取ったら発話開始
                        self.is_processing = False
                        self.is_speaking = True
                        self.notify_ui("speaking_started")
                        response_started = True

                    await queue.put(chunk)

                # 発話データの送信が完了したことをplaybackタスクに伝える
                await queue.put(None)
                # playbackタスクが全ての音声データを再生し終えるのを待つ
                await playback_done_event.wait()

                # 発話終了をUIに通知
                self.is_speaking = False
                self.notify_ui("speaking_finished")

            # ループを抜けた後、クリーンアップ
            await queue.put(None)
            await playback_task

    def loop(self):
        asyncio.run(self._loop())

    def run(self):
        thread = threading.Thread(target=self.loop, daemon=True)
        thread.start()
