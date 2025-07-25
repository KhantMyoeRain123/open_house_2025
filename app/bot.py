import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.chataudioclient import ChatAudioClient
from PySide6 import QtCore, QtWidgets
import csv
from collections import defaultdict
from PySide6 import QtWidgets, QtCore
from chat_ui import ChatUI

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
    def make_search_clubs_tool(available_clubs):
        search_clubs_tool={
        "name":"search_clubs_tool",
        "description":"学生の希望に基づいて、最も適したサークルを検索します。",
        "parameters":{
        "type": "object",
        "properties": {
            "clubs_to_search": {
                "type": "array",
                "items":{
                    "type":"string",
                    "enum":available_clubs,
                },
                "description": "学生の希望に基づいて検索するサークル。",
            },
        },
        "required": ["clubs_to_search"],
    },
    }   
    
        return search_clubs_tool
    
    
    @staticmethod
    def make_filter_clubs_tool():
        filter_clubs_tool={
        "name":"filter_clubs_tool",
        "description":"学生のスケジュールとサークルの活動内容に基づいて、最も適したサークルを絞り込みます。",
        "parameters":{
        "type": "object",
        "properties": {
            "clubs_to_choose": {
                "type": "array",
                "items":{
                    "type":"integer",
                },
                "description": "学生のスケジュールと希望に合致し、提示されるサークルの番号。",
            },
        },
        "required": ["clubs_to_choose"],
    },
    }   
    
        return filter_clubs_tool
        
    
    @staticmethod
    def make_tools(available_clubs):
        tools=[]
        tools.append(ClubRecommendationTools.make_search_clubs_tool(available_clubs))
        tools.append(ClubRecommendationTools.make_filter_clubs_tool())
        return tools
    
    @staticmethod
    def search_clubs(club_data,tool_args):
        print("Arguments:")
        print(tool_args)
        
        clubs_to_search=tool_args.get("clubs_to_search",[])
        matching_clubs=[]
        
        for club in clubs_to_search:
            if club in club_data:
                matching_clubs.extend(club_data[club])
            else:
                print(f"Club {club} not found in club data.")
        
        result_lines = []
        for i,club in enumerate(matching_clubs):
            club_info = []
            club_info.append(f"サークル {i}")
            club_info.append(f"サークル: {club.get('サークル', 'N/A')}")
            club_info.append(f"活動内容: {club.get('活動内容', 'N/A')}")
            club_info.append(f"活動日時・場所: {club.get('活動日時・場所', 'N/A')}")
            club_info.append(f"ラベル1: {club.get('ラベル1', 'N/A')}")
            club_info.append(f"ラベル２: {club.get('ラベル２', 'N/A')}")
            result_lines.append('\n'.join(club_info))
            result_lines.append("-" * 40)

        result_str = '\n'.join(result_lines).strip() + '\n'
        print(result_str)
        return matching_clubs,result_str
        
    @staticmethod
    def filter_clubs(founded_clubs, tool_args):
        print(tool_args)
        print("Filtering clubs...")
        
        # For example, tool_args might be a dict like {"clubs_to_choose": [0, 2]}
        chosen_indexes = tool_args.get("clubs_to_choose", [])
        filtered = [founded_clubs[i] for i in chosen_indexes if i < len(founded_clubs)]

        # Return filtered clubs and maybe a string summary
        result_str = "\n".join([f"{club.get('サークル', 'N/A')}: {club.get('活動内容', '')}" for club in filtered])
        return filtered, result_str

class ClubListUpdater(QtCore.QObject):
    update_clubs_signal=QtCore.Signal(list)
    def __init__(self, chatbot, parent=None):
        super().__init__(parent)
        self.chatbot=chatbot
        self.update_clubs_signal.connect(self.on_update_clubs)
    
    @QtCore.Slot()
    def on_update_clubs(self, clubs):
        self.chatbot.widget.update_club_list(clubs)
    
class ClubRecommendationBot(ChatAudioClient):
    
    def __init__(self,api_key, club_data, tools=[],system_instruction=""):
        super().__init__(api_key,tools=tools,system_instruction=system_instruction)
        self.club_data=club_data
        self.matching_clubs=None
        
        self.list_updater=ClubListUpdater(self)

    def call_tool(self,tool_name,tool_args):
        if tool_name=="search_clubs_tool":
            self.matching_clubs, result_str=ClubRecommendationTools.search_clubs(self.club_data,tool_args)
            return result_str
        elif tool_name=="filter_clubs_tool":
            if self.matching_clubs:
                filtered_clubs,result_str=ClubRecommendationTools.filter_clubs(self.matching_clubs,tool_args)
                self.list_updater.update_clubs_signal.emit(filtered_clubs)
                return result_str
        
    
    def run(self):
        super().run()
        self.app = QtWidgets.QApplication([])
        self.widget = ChatUI(self)
        self.widget.resize(800, 600)
        self.widget.show()

        sys.exit(self.app.exec())