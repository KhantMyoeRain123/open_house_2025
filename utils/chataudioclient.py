import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import threading
import time
import os

"""
    Handles audio capturing and output.
    Implements a chained architecture to enable functionalities like Retrieval-Augmented Generation (RAG).
    
    Flow: speech to text -> text -> text to speech
    
    音声の入力と出力を処理します。
    Retrieval-Augmented Generation（RAG）などの高度な機能をサポートするために
    チェーン形式のアーキテクチャを使用しています。

    処理の流れ：音声 → テキスト → テキスト処理 → 音声合成
"""
class ChatAudioClient:
    def __init__(self):
        self.running = True
        self.conversation_state = []

        self.audio_buffer = []
        self.is_recording = False
        self.record_event = threading.Event()

        # Audio settings
        # サンプルレート、チャンネル数、データ型を設定
        self.sample_rate = 16000
        self.channels = 1
        self.dtype = 'float32'

    def start_recording(self):
        # Starts the audio recording if not already recording
        # 録音が開始されていなければ、録音を開始する
        if not self.is_recording:
            self.record_event.set()
            self.is_recording = True
            print("Recording started.")  # 録音開始

    def stop_recording(self):
        # Stops the audio recording if it is currently recording
        # 録音中であれば録音を停止する
        if self.is_recording:
            self.record_event.clear()
            self.is_recording = False
            print("Recording stopped.")  # 録音停止

    def listen_to_user(self):
        # Waits for signal to start recording, captures audio input into buffer, and saves as WAV file
        # 録音開始の合図を待ち、音声をバッファに保存し、WAVファイルとして保存する
        self.record_event.clear()
        print("Listening...")  # リスニング開始
        self.record_event.wait()  # 録音開始のシグナルを待つ
        self.audio_buffer.clear()

        with sd.InputStream(samplerate=self.sample_rate,
                            channels=self.channels,
                            dtype=self.dtype) as stream:
            while self.record_event.is_set():
                data, _ = stream.read(1024)
                self.audio_buffer.append(data)
                time.sleep(0.01)  # 他のスレッドが実行できるように少し待機

            print(f"Captured {len(self.audio_buffer)} chunks of audio.")  # 音声チャンク数を表示
            audio = np.concatenate(self.audio_buffer, axis=0)
            os.makedirs("tmp", exist_ok=True)
            write("tmp/user.wav", self.sample_rate, audio)
            print("Saved as user.wav")  # ファイル保存完了

        # TODO: transcribe and add to conversation_state
        # TODO: 音声を文字起こしして会話状態に追加する処理を実装

    def process_user_input(self):
        # Processes the user's text input; place to implement RAG logic or other NLP processing
        # ユーザー入力のテキストを処理する。RAGなどのロジックをここに実装する
        pass

    def play_output(self):
        # Plays the output audio back to the user, e.g. synthesized speech from LLM output
        # LLMの出力音声などを再生する
        pass

    def loop(self):
        # Main loop: listens, processes input, and plays output repeatedly while running
        # メインループ：動作中は音声を聞き、入力を処理し、出力を再生し続ける
        while self.running:
            print("Chat audio client is running...")  # クライアント動作中
            self.listen_to_user()
            self.process_user_input()
            self.play_output()

    def run(self):
        # Starts the main loop in a separate daemon thread
        # メインループを別スレッドでデーモンとして起動する
        thread = threading.Thread(target=self.loop, daemon=True)
        thread.start()


