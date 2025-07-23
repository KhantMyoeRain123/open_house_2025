from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.chataudioclient import ChatAudioClient
from PySide6 import QtCore, QtWidgets
import csv
from collections import defaultdict
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

def read_json_club_data(path):
    # Resolve the absolute path to the data directory
    dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)

    # Find the first CSV file in the directory
    for filename in os.listdir(dir_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(dir_path, filename)
            try:
                with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
                    reader = csv.DictReader(csvfile)
                    grouped_data = defaultdict(list)
                    for row in reader:
                        label2 = row.get("ラベル２", None)
                        if label2 is not None:
                            grouped_data[label2].append(row)
                    return dict(grouped_data)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                return {}

    print("No CSV file found in data directory.")
    return {}


def clean_club_names(club_names):
    cleaned = []
    for name in club_names:
        try:
            if str(name)=='':
                continue
            encoded = name.encode('utf-8')
            decoded = encoded.decode('utf-8')
            cleaned.append(decoded)
        except UnicodeDecodeError:
            print(f"Skipping invalid UTF-8 club name: {name}")
    return cleaned

class ClubRecommendationTools:

    @staticmethod
    def make_search_club_tool(available_clubs):
        search_clubs_tool={
        "name":"search_clubs_tool",
        "description":"Search the most appropriate clubs for the student according to their preferences.",
        "parameters":{
        "type": "object",
        "properties": {
            "clubs_to_search": {
                "type": "array",
                "items":{
                    "type":"string",
                    "enum":available_clubs,
                },
                "description": "Clubs to search for according to the student's preferences.",
            },
        },
        "required": ["clubs_to_search"],
    },
    }   
    
        return search_clubs_tool
    
    @staticmethod
    def make_tools(available_clubs):
        tools=[]
        tools.append(ClubRecommendationTools.make_search_club_tool(available_clubs))
        return tools
    
    @staticmethod
    def search_clubs(club_data,tool_args):
        print("Arguments:")
        print(tool_args)
        
        clubs_to_search=tool_args.get("clubs_to_search",[])
        matching_clubs=[]
        
        for club in clubs_to_search:
            if club in club_data:
                matching_clubs.append(club_data[club])
            else:
                print(f"Club {club} not found in club data.")
        
        print(matching_clubs)
            

class ClubRecommendationBot(ChatAudioClient):
    def __init__(self,api_key, club_data, tools=[],system_instruction=""):
        super().__init__(api_key,tools=tools,system_instruction=system_instruction)
        self.club_data=club_data

    def call_tool(self,tool_name,tool_args):
        if tool_name=="search_clubs_tool":
            ClubRecommendationTools.search_clubs(self.club_data,tool_args)
        
    
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
    
    club_data=read_json_club_data("./data")
    cleaned_club_names=clean_club_names(club_data.keys())
    tools=ClubRecommendationTools.make_tools(cleaned_club_names)
    
    system_instruction="""
        あなたは高校生にクラブ活動を推薦することを仕事とする、親切なAIアシスタントです。あなたの目標は、生徒が楽しめて、かつ有意義なクラブを見つけられるように導くことです。そのために、次のように対応してください：

            1.生徒の興味、目標を理解するために、考え抜かれたオープンエンドの質問を5つ行ってください。

            2.質問は、趣味、学問的関心、将来の進路などに関する内容を含めてください。

            3.高校の雰囲気に合った、親しみやすく、フレンドリーな口調で話してください。

            4.最後の質問への回答を受け取ったら、「あなたに最適なクラブを探してもよいですか？」と尋ねてください。

            5.生徒がOKしてくれたら、search_clubs_toolを呼び出してください。

        まずは自己紹介をしてから、生徒のことを知るための最初の質問をしてください
    """
    app = ClubRecommendationBot(GEMINI_API_KEY,club_data=club_data,tools=tools,system_instruction=system_instruction)
    app.run()
    
    
    