import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import csv
from collections import defaultdict

from utils.chataudioclient import ChatAudioClient

# システム指示の定数定義
SYSTEM_INSTRUCTION = """
    あなたは高校生（まだ大学生ではない）に早稲田大学のサークル活動を推薦することを仕事とする、ワセクラと言う、親切なAIアシスタントです。あなたの目標は、生徒が楽しめて、かつ有意義なサークルを見つけられるように導くことです。そのために、次のように対応してください：

        1.生徒の興味や目標を理解するために、考え抜かれたオープンエンドの質問を5つ行ってください。

        2.質問は、以下のテーマを含めてください：

            趣味や好きなこと

            学問的な関心や得意科目

            将来の進路や夢

            サークルに参加できる曜日や時間帯（例：平日放課後、土日、短時間だけなど）

        3. 高校の雰囲気に合った、親しみやすくフレンドリーな口調で会話してください。

        4. 最後の質問への回答を受け取ったら、「あなたに最適なサークルを探してもよいですか？」と尋ねてください。

        5. 生徒がOKしてくれたら、search_clubs_tool を呼び出してください。その直後に、学生のスケジュールや活動内容も考慮して、さらにのサークルを絞り込むために filter_clubs_tool をすぐに呼び出してください。サークルが見つかったら、「あなたにぴったりのサークルが見つかりました！画面に表示されたサークル情報をご確認ください。」と伝えてください。

        最初は自己紹介をしてから、生徒のことを知るための1つ目の質問をしてください。
"""


def read_json_club_data(path):
    """CSVファイルからサークルデータを読み込む"""
    # Resolve the absolute path to the data directory
    dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)

    # Find the first CSV file in the directory
    for filename in os.listdir(dir_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(dir_path, filename)
            try:
                with open(file_path, newline="", encoding="utf-8-sig") as csvfile:
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
    """サークル名のクリーニング"""
    cleaned = []
    for name in club_names:
        try:
            if str(name) == "":
                continue
            encoded = name.encode("utf-8")
            decoded = encoded.decode("utf-8")
            cleaned.append(decoded)
        except UnicodeDecodeError:
            print(f"Skipping invalid UTF-8 club name: {name}")
    return cleaned


class ClubRecommendationTools:
    """サークル推薦用のツール群"""

    @staticmethod
    def make_search_clubs_tool(available_clubs):
        """サークル検索ツールの定義を作成"""
        search_clubs_tool = {
            "name": "search_clubs_tool",
            "description": "学生の希望に基づいて、最も適したサークルを検索します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "clubs_to_search": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": available_clubs,
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
        """サークルフィルタツールの定義を作成"""
        filter_clubs_tool = {
            "name": "filter_clubs_tool",
            "description": "学生のスケジュールとサークルの活動内容に基づいて、最も適したサークルを絞り込みます。",
            "parameters": {
                "type": "object",
                "properties": {
                    "clubs_to_choose": {
                        "type": "array",
                        "items": {
                            "type": "integer",
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
        """ツール一覧を作成"""
        tools = []
        tools.append(ClubRecommendationTools.make_search_clubs_tool(available_clubs))
        tools.append(ClubRecommendationTools.make_filter_clubs_tool())
        return tools

    @staticmethod
    def search_clubs(club_data, tool_args):
        """サークル検索を実行"""
        print("Arguments:")
        print(tool_args)

        clubs_to_search = tool_args.get("clubs_to_search", [])
        matching_clubs = []

        for club in clubs_to_search:
            if club in club_data:
                matching_clubs.extend(club_data[club])
            else:
                print(f"Club {club} not found in club data.")

        result_lines = []
        for i, club in enumerate(matching_clubs):
            club_info = []
            club_info.append(f"サークル {i}")
            club_info.append(f"サークル: {club.get('サークル', 'N/A')}")
            club_info.append(f"活動内容: {club.get('活動内容', 'N/A')}")
            club_info.append(f"活動日時・場所: {club.get('活動日時・場所', 'N/A')}")
            club_info.append(f"ラベル1: {club.get('ラベル1', 'N/A')}")
            club_info.append(f"ラベル２: {club.get('ラベル２', 'N/A')}")
            result_lines.append("\n".join(club_info))
            result_lines.append("-" * 40)

        result_str = "\n".join(result_lines).strip() + "\n"
        print(result_str)
        return matching_clubs, result_str

    @staticmethod
    def filter_clubs(founded_clubs, tool_args):
        """サークルフィルタリングを実行"""
        print(tool_args)
        print("Filtering clubs...")

        clubs_to_choose = tool_args.get("clubs_to_choose", [])
        filtered_clubs = []

        for club_index in clubs_to_choose:
            if 0 <= club_index < len(founded_clubs):
                filtered_clubs.append(founded_clubs[club_index])
            else:
                print(f"Invalid club index: {club_index}")

        return filtered_clubs


class ClubRecommendationBot(ChatAudioClient):
    """サークル推薦Bot"""

    def __init__(self, api_key, club_data, tools=[], system_instruction=""):
        super().__init__(api_key, tools=tools, system_instruction=system_instruction)
        self.club_data = club_data
        self.matching_clubs = None
        self.ui_widget = None
        
        # 質問進捗管理
        self.total_questions = 5  # 実際の質問回数（挨拶は除く）
        self.current_question_count = 0  # 現在の応答回数（挨拶含む）

    def set_ui_widget(self, ui_widget):
        """UIウィジェットを設定し、コールバックを登録"""
        print(f"[DEBUG] Setting UI widget: {ui_widget is not None}")
        self.ui_widget = ui_widget
        self.set_ui_callback(self.handle_ui_event)
        print(f"[DEBUG] UI widget set successfully: {self.ui_widget is not None}")

    def handle_ui_event(self, event, data=None):
        """UIイベントハンドラー"""
        if not self.ui_widget:
            return

        # 音声レベル更新イベントを処理
        if event == "audio_level_update" and data is not None:
            self.ui_widget.update_audio_level(data)

    def increment_question_count(self):
        """質問回数をインクリメント"""
        self.current_question_count += 1
                
    def reset_question_count(self):
        """質問回数をリセット"""
        self.current_question_count = 0

    # def reset_session(self):
    #     """セッション状態をリセット"""
    #     # 質問回数をリセット
    #     self.reset_question_count()
        
    #     # マッチしたサークル情報をクリア
    #     self.matching_clubs = None
        
    #     # 実行状態をリセット
    #     self.running = True

    def call_tool(self, tool_name, tool_args):
        """ツール実行"""
        print(f"[DEBUG] Tool called: {tool_name}")
        print(f"[DEBUG] Tool args: {tool_args}")
        print(f"[DEBUG] UI widget exists: {self.ui_widget is not None}")

        if tool_name == "search_clubs_tool":
            self.matching_clubs, result_str = ClubRecommendationTools.search_clubs(self.club_data, tool_args)
            print(f"[DEBUG] Search result: Found {len(self.matching_clubs)} clubs")
            return result_str
        elif tool_name == "filter_clubs_tool":
            if self.matching_clubs:
                filtered_clubs = ClubRecommendationTools.filter_clubs(self.matching_clubs, tool_args)
                print(f"[DEBUG] Filter result: {len(filtered_clubs)} clubs after filtering")

                # UIにサークル情報を表示（Signalを使用）
                if self.ui_widget:
                    print(f"[DEBUG] About to display {len(filtered_clubs)} clubs on UI using Signal")
                    try:
                        # Signalを使ってメインスレッドで確実に実行
                        self.ui_widget.receive_club_data(filtered_clubs)
                        print("[DEBUG] UI update via Signal sent successfully")
                    except Exception as e:
                        print(f"[DEBUG] Error sending UI update via Signal: {e}")
                else:
                    print("[DEBUG] UI widget is None - cannot display results")

                # 結果の文字列を作成
                result_lines = []
                for i, club in enumerate(filtered_clubs):
                    result_lines.append(f"選択されたサークル {i + 1}: {club.get('サークル', 'N/A')}")

                result_str = f"選択されたサークル数: {len(filtered_clubs)}\n" + "\n".join(result_lines)
                print(f"[DEBUG] Returning result: {result_str}")
                return result_str
            else:
                print("[DEBUG] No matching clubs found")
                return "サークルが見つかりませんでした。"

        print(f"[DEBUG] Unknown tool: {tool_name}")
        return ""

    @staticmethod
    def create_bot_instance(api_key, data_path="./data"):
        """Botインスタンスを作成するファクトリーメソッド"""
        club_data = read_json_club_data(data_path)
        cleaned_club_names = clean_club_names(club_data.keys())
        tools = ClubRecommendationTools.make_tools(cleaned_club_names)

        return ClubRecommendationBot(api_key, club_data=club_data, tools=tools, system_instruction=SYSTEM_INSTRUCTION)
