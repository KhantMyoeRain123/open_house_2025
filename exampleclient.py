from utils.chataudioclient import ChatAudioClient
from pynput import keyboard
from dotenv import load_dotenv
import os
"""
Example audio chat bot.
We implement our UI and higher-level logic in subclasses derived from ChatAudioClient.
For processing the captured audio, we override the process_user_input function. 
We can implement anything in it, and for our demo, we write the RAG logic inside it.

音声チャットボットのサンプルです。
ChatAudioClient を継承したクラスで UI や上位レベルのロジックを実装します。
録音した音声の処理は process_user_input 関数をオーバーライドして行います。
ここに自由に処理を実装でき、デモでは RAG ロジックを記述しています。
"""
class TerminalAudioChatBot(ChatAudioClient):
    def __init__(self,api_key, system_instruction=""):
        super().__init__(api_key,system_instruction=system_instruction)
        # Define any additional instance variables here
        # 必要に応じてここにインスタンス変数を追加してください
    
    # override the processing
    async def process_user_input(self, pcm_bytes,session):
        print("Processing in terminal audio chat bot...")
        return await super().process_user_input(pcm_bytes,session)

    def run(self):
        super().run()
        print("Press 'r' to start recording, 's' to stop, and 'q' to quit.")
        
        # UI logic
        def on_press(key):
            try:
                # Start recording when 'r' is pressed
                # 'r' キーで録音開始
                if key.char == 'r':
                    self.start_recording()
                # Stop recording when 's' is pressed
                # 's' キーで録音停止
                elif key.char == 's':
                    self.stop_recording()
                # Quit the app when 'q' is pressed
                # 'q' キーで終了
                elif key.char == 'q':
                    print("Exiting...")
                    self.running = False
                    return False  # Stop listener
            except AttributeError:
                # Ignore special keys like shift, ctrl, etc.
                # ShiftやCtrlなどの特殊キーは無視します
                pass
        
        # Start keyboard listener and wait until stopped
        # キーボードリスナーを起動し、終了するまで待機します
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

if __name__ == "__main__":
    load_dotenv()
    GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
    app = TerminalAudioChatBot(GEMINI_API_KEY)
    app.run()

