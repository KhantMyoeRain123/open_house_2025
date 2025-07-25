from dotenv import load_dotenv
import sys
import os
from PySide6 import QtCore, QtWidgets, QtGui

# ローカルモジュールのインポート
from ui import ChatUI
from bot import ClubRecommendationBot


class WaseKuraApp:
    """ワセクラアプリケーションのメインクラス"""
    
    def __init__(self):
        self.app = None
        self.widget = None
        self.bot = None
        
    def setup_font(self):
        """フォント設定"""
        # WSL環境での日本語フォント設定を強化
        self.app.setStyle('Fusion')
        
        # 日本語フォントを段階的に設定
        font = QtGui.QFont()
        
        # 利用可能なフォントを順番に試す
        font_candidates = [
            "Noto Sans CJK JP",
            "DejaVu Sans", 
            "Ubuntu",
            "Liberation Sans",
            "Arial Unicode MS",
            "MS Gothic",
            "Sans Serif"
        ]
        
        for font_name in font_candidates:
            font.setFamily(font_name)
            if QtGui.QFontInfo(font).exactMatch():
                print(f"Using font: {font_name}")
                break
        else:
            print("Using default system font")
            
        font.setPointSize(12)
        font.setStyleHint(QtGui.QFont.StyleHint.SansSerif)
        self.app.setFont(font)
    
    def setup_environment(self):
        """環境変数設定"""
        # 環境変数でエンコーディングを確実に設定
        os.environ['LC_ALL'] = 'ja_JP.UTF-8'
        os.environ['LANG'] = 'ja_JP.UTF-8'
    
    def create_bot(self, api_key):
        """Botインスタンスの作成"""
        return ClubRecommendationBot.create_bot_instance(api_key, "./data")
    
    def run(self, api_key):
        """アプリケーションの実行"""
        # GUIアプリケーションを最初に作成
        self.app = QtWidgets.QApplication([])
        
        # フォント設定
        self.setup_font()
        
        # 環境変数設定
        self.setup_environment()
        
        # Botインスタンスの作成
        self.bot = self.create_bot(api_key)
        
        # UIを作成して表示
        self.widget = ChatUI(self.bot)
        self.bot.set_ui_widget(self.widget)
        self.widget.resize(900, 700)
        self.widget.show()
        
        # バックグラウンドでチャットボットを開始
        self.bot.run()
        
        # GUIアプリケーションを実行
        sys.exit(self.app.exec())


def main():
    """メイン関数"""
    # 環境変数の読み込み
    load_dotenv()
    
    # Gemini API キーの取得
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in environment variables")
        sys.exit(1)
    
    # アプリケーションの実行
    app = WaseKuraApp()
    app.run(GEMINI_API_KEY)


if __name__ == "__main__":
    main()
