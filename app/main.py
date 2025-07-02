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

class ClubRecommendationTools:
    search_clubs_tool={
        "name":"search_clubs_tool",
        "description":"Search the most appropriate clubs for the student.",
    }
    
    tools=[search_clubs_tool]
    
    @staticmethod
    def search_clubs():
        print("Searching clubs...")
    
    


class ClubRecommendationBot(ChatAudioClient):
    def __init__(self,api_key, tools=[],system_instruction=""):
        super().__init__(api_key,tools=tools,system_instruction=system_instruction)
        self.club_data=self.read_json_club_data("./data")
        
    def read_json_club_data(self,path):
        pass
    
    def call_tool(self,tool_name,tool_args):
        if tool_name=="search_clubs_tool":
            ClubRecommendationTools.search_clubs()
        
    
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
    
    system_instruction="""
        あなたは高校生にクラブ活動を推薦することを仕事とする、親切なAIアシスタントです。あなたの目標は、生徒が楽しめて、かつ有意義なクラブを見つけられるように導くことです。そのために、次のように対応してください：

            1.生徒の性格、興味、目標、スケジュールを理解するために、考え抜かれたオープンエンドの質問を5つ行ってください。

            2.質問は、趣味、学問的関心、将来の進路、参加可能な時間などに関する内容を含めてください。

            3.高校の雰囲気に合った、親しみやすく、フレンドリーな口調で話してください。

            4.最後の質問への回答を受け取ったら、「あなたに最適なクラブを探してもよいですか？」と尋ねてください。

            5.生徒がOKしてくれたら、search_clubs_toolを呼び出してください。

        まずは自己紹介をしてから、生徒のことを知るための最初の質問をしてください
    """
    app = ClubRecommendationBot(GEMINI_API_KEY,tools=ClubRecommendationTools.tools,system_instruction=system_instruction)
    app.run()
    
    
    