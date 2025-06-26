from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.chataudioclient import ChatAudioClient
from PySide6 import QtCore, QtWidgets, QtGui
import random

class ChatUI(QtWidgets.QWidget):
    def __init__(self, chatbot):
        super().__init__()

        self.chatbot=chatbot


        self.button = QtWidgets.QPushButton("話す!")
        self.text = QtWidgets.QLabel("こんにちは！",alignment=QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.record_voice)

    @QtCore.Slot()
    def record_voice(self):
        if not self.chatbot.is_recording:
            self.chatbot.start_recording()
            self.button.setText("止める！")
        else:
            self.chatbot.stop_recording()
            self.button.setText("話す!")



class ClubRecommendationBot(ChatAudioClient):
    def __init__(self,api_key, system_instruction=""):
        super().__init__(api_key,system_instruction=system_instruction)
        
        
    def run(self):
        super().run()
        app = QtWidgets.QApplication([])
        widget = ChatUI(self)
        widget.resize(800, 600)
        widget.show()

        sys.exit(app.exec())
        


if __name__=="__main__":
    load_dotenv()
    GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
    app = ClubRecommendationBot(GEMINI_API_KEY)
    app.run()
    
    
    