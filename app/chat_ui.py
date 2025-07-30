from PySide6 import QtCore, QtWidgets, QtSvgWidgets, QtGui
from PySide6.QtGui import QPainter, QLinearGradient, QColor, QPixmap
from PySide6.QtCore import QPoint, Qt
import os
import random

# --- 音声レベル表示用の定数設定 ---
NUM_BARS = 20         # 表示する棒グラフの数


class ChatUI(QtWidgets.QWidget):
    # Signal for club data display
    club_data_received = QtCore.Signal(list)

    def __init__(self, chatbot):
        super().__init__()

        self.chatbot = chatbot
        self.setup_ui()

        # Connect the signal to the display method
        self.club_data_received.connect(self.display_club_info_modal)

        # 音声レベル表示の初期化（チャットボットから音声レベルを受け取る）
        self.setup_audio_waveform()

        # チャットボットの状態変化を監視するタイマー
        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(100)  # 100ms間隔で更新
        
        # 質問進捗管理
        self.total_questions = 5  # 実際の質問数（挨拶は除く）
        self.current_question = 0
        
        # ランダム画像表示の初期化
        self.setup_random_images()
        
        # 前回の状態を記録（画像表示タイミング判定用）
        self.previous_status = None

    def setup_random_images(self):
        """ランダム画像表示の初期化"""
        # 画像フォルダのパス
        self.club_images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "picture", "club")
        
        # 利用可能な画像ファイルを取得
        self.available_images = []
        if os.path.exists(self.club_images_path):
            for filename in os.listdir(self.club_images_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.available_images.append(filename)
        
        # 表示位置の定義（右上、右下、左下）
        self.display_positions = ['top-right', 'bottom-right', 'bottom-left']
        self.used_positions = []  # 使用済み位置を記録
        self.used_images = []  # 使用済み画像を記録
        
        # 現在表示中の画像ウィジェットリスト
        self.displayed_image_widgets = []

    def setup_audio_waveform(self):
        """音声レベル表示の初期化（チャットボットから音声レベルを受け取る）"""
        # 音声レベルデータの初期化
        self.audio_level = 0.0
        
        # UI更新用のタイマー（常に作成するが、録音時のみ動作）
        self.waveform_timer = QtCore.QTimer()
        self.waveform_timer.setInterval(50)  # 50msごとに画面を更新
        self.waveform_timer.timeout.connect(self.update_audio_bars)

    def start_audio_stream(self):
        """音声レベル表示を開始（タイマーのみ）"""
        self.waveform_timer.start()

    def stop_audio_stream(self):
        """音声レベル表示を停止"""
        if self.waveform_timer.isActive():
            self.waveform_timer.stop()
        
        # すべてのバーをリセット
        if hasattr(self, 'audio_bars'):
            for bar in self.audio_bars:
                bar.setValue(0)
                bar.setStyleSheet("""
                    QProgressBar {
                        background-color: #2c3e50;
                        border: 1px solid #34495e;
                        border-radius: 3px;
                    }
                    QProgressBar::chunk {
                        background-color: #2c3e50;
                        border-radius: 2px;
                    }
                """)
        self.audio_level = 0.0

    def show_random_club_image(self):
        """ランダムなサークル画像を表示"""
        if not self.available_images:
            return
        
        # 使用可能な位置をチェック
        if len(self.used_positions) >= len(self.display_positions):
            # すべての位置が使用済みの場合は表示しない
            return
        
        # 未使用の画像をフィルタリング
        available_images = [img for img in self.available_images if img not in self.used_images]
        
        # 未使用の画像がない場合は使用済みリストをリセット
        if not available_images:
            self.used_images.clear()
            available_images = self.available_images.copy()
        
        # ランダムに画像を選択
        random_image = random.choice(available_images)
        self.used_images.append(random_image)
        image_path = os.path.join(self.club_images_path, random_image)
        
        # 未使用の位置からランダムに選択
        available_positions = [pos for pos in self.display_positions if pos not in self.used_positions]
        position = random.choice(available_positions)
        self.used_positions.append(position)
        
        # 画像ウィジェットを作成
        image_widget = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap(image_path)
        
        # 画像サイズを調整（180x180ピクセル）
        scaled_pixmap = pixmap.scaled(180, 180, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        
        # ランダムな角度で回転（-30度から30度）
        rotation_angle = random.uniform(-15, 15)
        transform = QtGui.QTransform()
        transform.rotate(rotation_angle)
        rotated_pixmap = scaled_pixmap.transformed(transform, QtCore.Qt.SmoothTransformation)
        
        image_widget.setPixmap(rotated_pixmap)
        # 回転後のサイズに合わせて調整
        image_widget.setFixedSize(rotated_pixmap.size())
        image_widget.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
            }
        """)
        
        # 位置を設定
        self.position_image_widget(image_widget, position)
        
        # ウィジェットを表示
        image_widget.show()
        
        # 表示中のウィジェットリストに追加
        self.displayed_image_widgets.append(image_widget)
        
        print(f"[DEBUG] Displayed club image: {random_image} at position: {position} with rotation: {rotation_angle:.1f}°")

    def position_image_widget(self, widget, position):
        """画像ウィジェットを指定位置に配置"""
        margin = 80  # 画面端からの余白を大きくして中央寄りに
        
        if position == 'top-right':
            x = self.width() - widget.width() - margin
            y = margin + 120  # ヘッダーを避けて配置（少し下に移動）
        elif position == 'bottom-right':
            x = self.width() - widget.width() - margin +20
            y = self.height() - widget.height() - margin  # ボタンエリアを避けつつさらに下寄りに配置
        elif position == 'bottom-left':
            x = margin - 40  # 左下の画像をより左に移動
            y = self.height() - widget.height() - margin  # ボタンエリアを避けつつさらに下寄りに配置
        
        widget.move(x, y)

    def clear_club_images(self):
        """表示中のサークル画像をすべて削除"""
        for widget in self.displayed_image_widgets:
            widget.setParent(None)
            widget.deleteLater()
        
        self.displayed_image_widgets.clear()
        self.used_positions.clear()
        self.used_images.clear()  # 使用済み画像もクリア
        print("[DEBUG] Cleared all club images")

    def update_audio_level(self, level):
        """チャットボットから音声レベルを受け取る"""
        self.audio_level = level

    def update_question_progress(self, current, total, percentage):
        """質問進捗の更新（バーは削除済みなので空処理）"""
        pass

    def update_audio_bars(self):
        """音声レベルバーを更新する関数"""
        if hasattr(self, 'audio_bars'):
            # 各バーの高さを音声レベルに応じて設定
            for i, bar in enumerate(self.audio_bars):
                # 各バーが異なるしきい値で反応するように設定
                threshold = (i + 1) / NUM_BARS
                if self.audio_level > threshold:
                    # 音声レベルが高いほど緑色に、低いほど青色に
                    if self.audio_level > 0.7:
                        color = "#e74c3c"  # 赤
                    elif self.audio_level > 0.4:
                        color = "#f39c12"  # オレンジ
                    else:
                        color = "#3498db"  # 青
                    bar.setStyleSheet(f"""
                        QProgressBar {{
                            background-color: #2c3e50;
                            border: 1px solid #34495e;
                            border-radius: 3px;
                        }}
                        QProgressBar::chunk {{
                            background-color: {color};
                            border-radius: 2px;
                        }}
                    """)
                    bar.setValue(100)
                else:
                    bar.setStyleSheet("""
                        QProgressBar {
                            background-color: #2c3e50;
                            border: 1px solid #34495e;
                            border-radius: 3px;
                        }
                        QProgressBar::chunk {
                            background-color: #2c3e50;
                            border-radius: 2px;
                        }
                    """)
                    bar.setValue(0)

    def update_waveform(self):
        """波形プロットを更新する関数（互換性のため残す）"""
        pass

    def setup_ui(self):
        self.setWindowTitle("ワセクラ - 早稲田大学サークル推薦AI")

        # メインウィンドウのスタイル（背景色はpaintEventで描画）
        self.setStyleSheet("""
            QWidget {
                color: #ffffff;
            }
        """)

        # メインレイアウト
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(20)  # 要素間のスペースを増やす

        # ヘッダー部分（タイトルとロゴ）
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        
        # タイトル
        title = QtWidgets.QLabel("ワセクラ - 早稲田大学サークル推薦AI", alignment=QtCore.Qt.AlignCenter)
        title.setStyleSheet(
            "font-family: 'Kosugi Maru', 'Kosugi Maru', 'Meiryo', sans-serif; font-size: 34px; font-weight: bold; margin-top: 40px; margin-left: 15px; margin-right: 15px; margin-bottom: 15px; color: #000000; background-color: transparent; padding: 15px;"
        )
        
        # ロゴエリア（早稲田ロゴ + メインロゴ）
        logo_container = QtWidgets.QWidget()
        logo_layout = QtWidgets.QVBoxLayout(logo_container)
        logo_layout.setSpacing(0)  # ロゴ間のスペース（負の値で重なりを作る）
        logo_layout.setContentsMargins(30, 20, 20, 20)
        
        # 早稲田ロゴ（上部）
        waseda_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "picture", "waseda_logo.png")
        if os.path.exists(waseda_logo_path):
            self.waseda_logo_widget = QtWidgets.QLabel()
            pixmap = QtGui.QPixmap(waseda_logo_path)
            scaled_pixmap = pixmap.scaled(160, 80, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.waseda_logo_widget.setPixmap(scaled_pixmap)
            self.waseda_logo_widget.setAlignment(QtCore.Qt.AlignCenter)
            self.waseda_logo_widget.setStyleSheet("background-color: transparent;")
            logo_layout.addWidget(self.waseda_logo_widget)
        
        # メインロゴ（下部）
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "picture", "rsl_logo_black.svg")
        if os.path.exists(logo_path):
            self.logo_widget = QtSvgWidgets.QSvgWidget(logo_path)
            self.logo_widget.setFixedSize(160, 160)  # ロゴのサイズを設定
            self.logo_widget.setStyleSheet("background-color: transparent;")
        else:
            # SVGファイルが見つからない場合は代替テキストを表示
            self.logo_widget = QtWidgets.QLabel("LOGO")
            self.logo_widget.setFixedSize(160, 160)
            self.logo_widget.setAlignment(QtCore.Qt.AlignCenter)
            self.logo_widget.setStyleSheet(
                "border: 2px solid #3498db; border-radius: 60px; font-size: 16px; font-weight: bold; color: #3498db; background-color: #000000;"
            )
        logo_layout.addWidget(self.logo_widget)
        
        # ヘッダーレイアウトに追加
        header_layout.addWidget(title)
        header_layout.addStretch()  # タイトルとロゴの間にスペースを作る
        header_layout.addWidget(logo_container)
        
        self.layout.addWidget(header_widget)

        # 状態表示エリア
        self.status_widget = QtWidgets.QWidget()
        status_layout = QtWidgets.QHBoxLayout(self.status_widget)

        self.status_icon = QtWidgets.QLabel("[待機]")
        self.status_icon.setStyleSheet("font-family: 'Yu Gothic UI', 'Meiryo', 'Hiragino Sans', 'Arial', sans-serif; font-size: 20px; font-weight: bold; color: #3498db; padding: 10px; background-color: transparent;")
        self.status_text = QtWidgets.QLabel("待機中...")
        self.status_text.setStyleSheet("font-family: 'Yu Gothic UI', 'Meiryo', 'Hiragino Sans', 'Arial', sans-serif; font-size: 20px; color: #cccccc; padding: 10px; background-color: transparent;")

        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        self.layout.addWidget(self.status_widget)

        # 音声レベル表示エリア
        audio_container = QtWidgets.QWidget()
        audio_layout = QtWidgets.QVBoxLayout(audio_container)
        audio_layout.setContentsMargins(20, 10, 20, 10)
        
        # タイトルラベル
        audio_title = QtWidgets.QLabel("音声レベル", alignment=QtCore.Qt.AlignCenter)
        audio_title.setStyleSheet("font-size: 16px; color: #cccccc; margin-bottom: 10px; background-color: transparent;")
        audio_layout.addWidget(audio_title)
        
        # 音声レベルバーのコンテナ
        bars_container = QtWidgets.QWidget()
        bars_layout = QtWidgets.QHBoxLayout(bars_container)
        bars_layout.setSpacing(3)
        bars_layout.setContentsMargins(0, 0, 0, 0)
        
        # 複数の縦棒グラフを作成
        self.audio_bars = []
        for i in range(NUM_BARS):
            bar = QtWidgets.QProgressBar()
            bar.setOrientation(QtCore.Qt.Vertical)
            bar.setFixedSize(15, 80)
            bar.setMinimum(0)
            bar.setMaximum(100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setStyleSheet("""
                QProgressBar {
                    background-color: #2c3e50;
                    border: 1px solid #34495e;
                    border-radius: 3px;
                }
                QProgressBar::chunk {
                    background-color: #2c3e50;
                    border-radius: 2px;
                }
            """)
            self.audio_bars.append(bar)
            bars_layout.addWidget(bar)
        
        audio_layout.addWidget(bars_container)
        self.layout.addWidget(audio_container)


        # テスト用: サークル情報エリアが正しく表示されるかテスト
        # self.test_display()  # デバッグ時に有効化

        # 下部の大きな録音ボタンエリア
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QVBoxLayout(button_container)
        button_layout.setAlignment(QtCore.Qt.AlignCenter)
        button_layout.setContentsMargins(0, 30, 0, 30)  # 上下の余白を調整

        # ボタンの説明テキスト
        self.button_instruction = QtWidgets.QLabel(
            "ボタンを押して「こんにちは」と話しかけてね", alignment=QtCore.Qt.AlignCenter
        )
        self.button_instruction.setStyleSheet("font-family: 'Yu Gothic UI', 'Meiryo', 'Hiragino Sans', 'Arial', sans-serif; font-size: 18px; color: #000000; margin: 10px; background-color: transparent;")
        button_layout.addWidget(self.button_instruction)

        # 大きな円形の録音ボタン
        self.button = QtWidgets.QPushButton("話す!")
        self.button.setFixedSize(180, 180)  # ボタンサイズを大きく
        self.button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4a90e2, stop: 1 #1e3a8a);
                color: white;
                border: none;
                border-radius: 90px;
                font-size: 28px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #5ba0f2, stop: 1 #2e4a9a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2e4a9a, stop: 1 #1a2d6a);
            }
        """)
        self.button.clicked.connect(self.handle_button_click)

        # ボタンを中央に配置するためのレイアウト調整
        button_wrapper = QtWidgets.QHBoxLayout()
        button_wrapper.addStretch()
        button_wrapper.addWidget(self.button)
        button_wrapper.addStretch()

        button_layout.addLayout(button_wrapper)
        self.layout.addWidget(button_container)

        # サークル情報が表示されているかのフラグ
        self.clubs_displayed = False
        
        # 初回状態かどうかを示すフラグ
        self.is_first_interaction = True
        
        # 録音停止直後の処理待ち状態フラグ
        self.is_processing_after_recording = False
        
        # マイクアイコンを読み込み
        self.setup_mic_icon()
        
        # 背景画像を読み込み
        self.setup_background_image()

    def setup_background_image(self):
        """背景画像を読み込み"""
        background_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "picture", "background3.png")
        if os.path.exists(background_path):
            self.background = QPixmap(background_path)
        else:
            # 画像が見つからない場合は空のPixmapを設定
            self.background = QPixmap()
            print(f"背景画像が見つかりません: {background_path}")

    def paintEvent(self, event):
        """背景画像またはグラデーションを描画"""
        painter = QPainter(self)
        
        if not self.background.isNull():
            # 背景画像がある場合は画像を描画
            # ウィンドウサイズに合わせて拡大縮小
            scaled = self.background.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, scaled)
        else:
            # 背景画像がない場合はグラデーションを描画
            gradient = QLinearGradient(QPoint(0, 0), QPoint(0, self.height()))
            gradient.setColorAt(0, QColor("#750000"))   # 上部の色
            gradient.setColorAt(1, QColor("#3e0000"))   # 下部の色
            painter.fillRect(self.rect(), gradient)

    def setup_mic_icon(self):
        """マイクアイコンとサウンドアイコンを読み込み"""
        # マイクアイコンを読み込み
        mic_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "picture", "mic.svg")
        if os.path.exists(mic_icon_path):
            self.mic_icon = QtGui.QIcon(mic_icon_path)
        else:
            # SVGファイルが見つからない場合は空のアイコンを設定
            self.mic_icon = QtGui.QIcon()
        
        # サウンドアイコンを読み込み
        sound_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "picture", "sound.svg")
        if os.path.exists(sound_icon_path):
            self.sound_icon = QtGui.QIcon(sound_icon_path)
        else:
            # SVGファイルが見つからない場合は空のアイコンを設定
            self.sound_icon = QtGui.QIcon()

    def _set_button_instruction_text(self, text):
        """ボタン説明文を設定し、色を黒に固定"""
        self.button_instruction.setText(text)
        self.button_instruction.setStyleSheet("font-family: 'Yu Gothic UI', 'Meiryo', 'Hiragino Sans', 'Arial', sans-serif; font-size: 18px; color: #000000; margin: 10px; background-color: transparent;")

    def _set_button_content(self, icon=None, text="", icon_size=(60, 60)):
        """ボタンのアイコンまたはテキストを設定する共通メソッド"""
        if icon and not icon.isNull():
            self.button.setIcon(icon)
            self.button.setIconSize(QtCore.QSize(*icon_size))
            self.button.setText("")  # アイコン使用時はテキストを非表示
        else:
            self.button.setIcon(QtGui.QIcon())  # アイコンをクリア
            self.button.setText(text)

    def update_status(self):
        """チャットボットの状態に応じてUIを更新"""
        if self.clubs_displayed:
            # サークル情報が表示されている時は終了ボタンとして表示
            self.status_icon.setText("[完了]")
            self.status_icon.setStyleSheet("font-size: 20px; font-weight: bold; color: #27ae60; padding: 10px; background-color: transparent;")
            self.status_text.setText("サークル情報を確認してください")
            self.status_text.setStyleSheet("font-size: 20px; color: #27ae60; padding: 10px; background-color: transparent;")
            self.button.setEnabled(True)
            self._set_button_content(text="リセット")
            self._set_button_instruction_text("アプリを終了するにはボタンをクリックしてください")
            self._update_exit_button_style()
        elif self.chatbot.is_recording:
            self.status_icon.setText("[録音中]")
            self.status_icon.setStyleSheet("font-size: 20px; font-weight: bold; color: #e74c3c; padding: 10px; background-color: transparent;")
            self.status_text.setText("録音中... 話してください")
            self.status_text.setStyleSheet("font-size: 20px; color: #e74c3c; font-weight: bold; padding: 10px; background-color: transparent;")
            self.button.setEnabled(True)  # 録音中は停止ボタンとして有効
            self._set_button_content(text="STOP")
            self._set_button_instruction_text("録音を停止するにはボタンをクリックしてください")
            self._update_recording_button_style()
            # 録音中は音声レベル表示を開始
            self.start_audio_stream()
        elif hasattr(self.chatbot, "is_speaking") and self.chatbot.is_speaking:
            self.status_icon.setText("[ワセクラ発話中]")
            self.status_icon.setStyleSheet("font-size: 20px; font-weight: bold; color: #27ae60; padding: 10px; background-color: transparent;")
            self.status_text.setText("ワセクラが話しています...")
            self.status_text.setStyleSheet("font-size: 20px; color: #27ae60; padding: 10px; background-color: transparent;")
            self.button.setEnabled(False)  # 発話中はボタン無効
            self._set_button_content(icon=self.sound_icon, text="待っててね!")
            self._set_button_instruction_text("ワセクラの発話が終わるまでお待ちください")
            self._update_button_disabled_style()
            # 発話中は音声レベル表示を停止
            self.stop_audio_stream()
        elif hasattr(self.chatbot, "is_processing") and self.chatbot.is_processing:
            self.status_icon.setText("[処理中]")
            self.status_icon.setStyleSheet("font-size: 20px; font-weight: bold; color: #9b59b6; padding: 10px; background-color: transparent;")
            self.status_text.setText("ワセクラが考え中...")
            self.status_text.setStyleSheet("font-size: 20px; color: #9b59b6; padding: 10px; background-color: transparent;")
            self.button.setEnabled(False)  # 処理中はボタン無効
            self._set_button_content(text="...")
            self._set_button_instruction_text("ワセクラが処理中です... しばらくお待ちください")
            self._update_button_disabled_style()
            # 処理中は音声レベル表示を停止
            self.stop_audio_stream()
            # 実際の処理状態になったら録音停止後フラグをリセット
            self.is_processing_after_recording = False
        elif self.is_processing_after_recording:
            # 録音停止直後の処理待ち状態
            self.status_icon.setText("[処理中]")
            self.status_icon.setStyleSheet("font-size: 20px; font-weight: bold; color: #9b59b6; padding: 10px; background-color: transparent;")
            self.status_text.setText("ワセクラが考え中...")
            self.status_text.setStyleSheet("font-size: 20px; color: #9b59b6; padding: 10px; background-color: transparent;")
            self.button.setEnabled(False)  # 処理中はボタン無効
            self._set_button_content(text="...")
            self._set_button_instruction_text("ワセクラが処理中です... しばらくお待ちください")
            self._update_button_disabled_style()
            # 処理中は音声レベル表示を停止
            self.stop_audio_stream()
        elif self.chatbot.is_listening and not self.chatbot.is_recording:
            self.status_icon.setText("[待機]")
            self.status_icon.setStyleSheet("font-size: 20px; font-weight: bold; color: #f39c12; padding: 10px; background-color: transparent;")
            self.status_text.setText("音声待機中...")
            self.status_text.setStyleSheet("font-size: 20px; color: #f39c12; padding: 10px; background-color: transparent;")
            self.button.setEnabled(True)  # 待機中はボタン有効
            self._set_button_content(icon=self.mic_icon, text="マイク")
            if self.is_first_interaction:
                self._set_button_instruction_text("ボタンを押して「こんにちは」と話してみよう！")
            else:
                self._set_button_instruction_text("クリックして話しかけてください")
            self._restore_normal_button_style()
            # 待機中は音声レベル表示を停止
            self.stop_audio_stream()
        else:
            self.status_icon.setText("[待機]")
            self.status_icon.setStyleSheet("font-size: 20px; font-weight: bold; color: #f39c12; padding: 10px; background-color: transparent;")
            self.status_text.setText("音声待機中...")
            self.status_text.setStyleSheet("font-size: 20px; color: #f39c12; padding: 10px; background-color: transparent;")
            self.button.setEnabled(True)  # 通常時はボタン有効
            self._set_button_content(icon=self.mic_icon, text="話す!")
            if self.is_first_interaction:
                self._set_button_instruction_text("ボタンを押して「こんにちは」と話しかけてね")
            else:
                self._set_button_instruction_text("ボタンを押して話しかけてください")
            self._restore_normal_button_style()
            # 通常待機中は音声レベル表示を停止
            self.stop_audio_stream()
        
        # 状態変化をチェックして画像表示を制御
        current_status = self._get_current_status()
        if (self.previous_status != "waiting" and current_status == "waiting" 
            and hasattr(self.chatbot, 'current_question_count') 
            and self.chatbot.current_question_count > 1):  # 挨拶後の質問から
            # AI発話後の録音待機状態になったときに画像を表示
            self.show_random_club_image()
        
        self.previous_status = current_status

    def _get_current_status(self):
        """現在の状態を文字列で返す"""
        if self.clubs_displayed:
            return "completed"
        elif self.chatbot.is_recording:
            return "recording"
        elif hasattr(self.chatbot, "is_speaking") and self.chatbot.is_speaking:
            return "speaking"
        elif hasattr(self.chatbot, "is_processing") and self.chatbot.is_processing:
            return "processing"
        elif self.is_processing_after_recording:
            return "processing"
        elif self.chatbot.is_listening and not self.chatbot.is_recording:
            return "waiting"
        else:
            return "waiting"

    def _update_button_disabled_style(self):
        """ボタンが無効な時のスタイルを設定"""
        self.button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #bdc3c7, stop: 1 #95a5a6);
                color: #7f8c8d;
                border: none;
                border-radius: 90px;
                font-size: 28px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #bdc3c7, stop: 1 #95a5a6);
                color: #7f8c8d;
            }
        """)

    def update_realtime_text(self, text):
        """リアルタイム音声認識結果を更新（削除済みのため何もしない）"""
        pass

    def _reset_app(self):
        """アプリをリセットして初期状態に戻す"""
        self._restore_normal_button_style()

        self.clubs_displayed=False
        self.chatbot.running=False
        self.is_first_interaction=True
        self.is_processing_after_recording = False

    def handle_button_click(self):
        """ボタンクリックを処理（録音開始/停止 or アプリ終了）"""
        if self.clubs_displayed:
            # サークル情報が表示されている場合はアプリを終了
            #QtWidgets.QApplication.quit()
            self._reset_app()
        else:
            # 通常の録音機能
            self.record_voice()

    @QtCore.Slot()
    def record_voice(self):
        # ボタンが無効な時は何もしない
        if not self.button.isEnabled():
            return

        if not self.chatbot.is_recording:
            # 初回の場合はフラグを更新
            if self.is_first_interaction:
                self.is_first_interaction = False
            
            # 録音開始時に即座にボタンと説明文を同時に変更（ラグを防ぐため）
            self._set_button_content(text="STOP")
            self._update_recording_button_style()
            self._set_button_instruction_text("録音を停止するにはボタンをクリックしてください")
            
            self.chatbot.start_recording()
        else:
            # 録音停止時も即座にボタンと説明文を変更
            self._set_button_content(text="...")
            self._update_button_disabled_style()
            self._set_button_instruction_text("ワセクラが処理中です... しばらくお待ちください")
            
            # 録音停止（update_statusメソッドが自動的に適切な状態に更新）
            self.chatbot.stop_recording()
            # 録音停止直後は処理待ち状態として表示
            self.is_processing_after_recording = True

    def _update_recording_button_style(self):
        """録音中のボタンスタイルを設定"""
        self.button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #c0392b, stop: 1 #922b20);
                color: white;
                border: none;
                border-radius: 90px;
                font-size: 28px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #d35400, stop: 1 #a93226);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #a93226, stop: 1 #7f1d1d);
            }
        """)

    def _restore_normal_button_style(self):
        """通常時のボタンスタイルを復元"""
        self.button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4a90e2, stop: 1 #1e3a8a);
                color: white;
                border: none;
                border-radius: 90px;
                font-size: 28px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #5ba0f2, stop: 1 #2e4a9a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2e4a9a, stop: 1 #1a2d6a);
            }
        """)

    def _update_exit_button_style(self):
        """終了ボタンのスタイルを設定"""
        self.button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #27ae60, stop: 1 #1e8e4f);
                color: white;
                border: none;
                border-radius: 90px;
                font-size: 28px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2ecc71, stop: 1 #27ae60);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1e8e4f, stop: 1 #16703c);
            }
        """)

    def display_club_info_modal(self, clubs):
        """サークル情報を表示"""
        print(f"[UI DEBUG] display_club_info called with {len(clubs)} clubs")
        print(f"[UI DEBUG] Club info container exists: {hasattr(self, 'club_info_container')}")
        print(f"[UI DEBUG] Club content layout exists: {hasattr(self, 'club_content_layout')}")


        """サークル情報をモーダルで表示"""
        modal = QtWidgets.QDialog(self)
        modal.setWindowTitle("おすすめのサークル")
        modal.setModal(True)
        modal.resize(1500, 1000)  # モーダルのサイズを設定
        
        # モーダルのダークテーマ設定
        modal.setStyleSheet("""
            QDialog {
                background-color: #000000;
                color: #ffffff;
            }
            QLabel {
                background-color: transparent;
                color: #ffffff;
            }
        """)

        # モーダルのレイアウト
        modal_layout = QtWidgets.QVBoxLayout(modal)

        # タイトル
        self.club_info_title = QtWidgets.QLabel("あなたにおすすめのサークル", alignment=QtCore.Qt.AlignCenter)
        self.club_info_title.setStyleSheet(
            "font-family: 'Yu Gothic UI', 'Meiryo', 'Hiragino Sans', 'Arial', sans-serif; font-size: 28px; font-weight: bold; color: #ffffff; margin: 10px; padding: 10px; background-color: transparent;"
        )
        
        modal_layout.addWidget(self.club_info_title)

        # スクロール可能なサークル情報エリアを追加
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1a1a1a;
                border-radius: 10px;
                min-height: 600px;
                max-height: 800px;
                border: 1px solid #333333;
            }
        """)

        self.content_widget = QtWidgets.QWidget()
        self.club_content_layout = QtWidgets.QVBoxLayout(self.content_widget)

        # サークル情報を表示

        # 既存の内容をクリア
        for i in reversed(range(self.club_content_layout.count())):
            child = self.club_content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)


        if not clubs:
            # サークルが見つからない場合
            no_clubs_label = QtWidgets.QLabel(
                "申し訳ございませんが、条件に合うサークルが見つかりませんでした。", alignment=QtCore.Qt.AlignCenter
            )
            no_clubs_label.setStyleSheet("font-size: 18px; color: #e74c3c; padding: 20px; background-color: transparent;")
            self.club_content_layout.addWidget(no_clubs_label)
            print("[UI DEBUG] No clubs message added")
        else:
            # 各サークルの情報を表示
            for i, club in enumerate(clubs):
                print(f"[UI DEBUG] Adding club {i}: {club.get('サークル', 'N/A')}")
                club_frame = QtWidgets.QFrame()
                club_frame.setStyleSheet("""
                    QFrame {
                        background-color: #2a2a2a;
                        border: 1px solid #444444;
                        border-radius: 8px;
                        margin: 5px;
                        padding: 10px;
                    }
                    QFrame:hover {
                        border-color: #3498db;
                        box-shadow: 0 2px 5px rgba(52, 152, 219, 0.3);
                    }
                """)

                club_layout = QtWidgets.QVBoxLayout(club_frame)

                # サークル名
                club_name = QtWidgets.QLabel(f"📍 {club.get('サークル', 'N/A')}")
                club_name.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff; margin-bottom: 5px; background-color: transparent;")
                club_layout.addWidget(club_name)

                # 活動内容
                activity_content = club.get("活動内容", "N/A")
                if activity_content != "N/A":
                    activity_label = QtWidgets.QLabel(f"🎯 活動内容: {activity_content}")
                    activity_label.setStyleSheet("font-size: 16px; color: #cccccc; margin: 3px 0; padding-left: 10px; background-color: transparent;")
                    activity_label.setWordWrap(True)
                    club_layout.addWidget(activity_label)

                # 活動日時・場所
                schedule = club.get("活動日時・場所", "N/A")
                if schedule != "N/A":
                    schedule_label = QtWidgets.QLabel(f"🕒 活動日時・場所: {schedule}")
                    schedule_label.setStyleSheet("font-size: 16px; color: #cccccc; margin: 3px 0; padding-left: 10px; background-color: transparent;")
                    schedule_label.setWordWrap(True)
                    club_layout.addWidget(schedule_label)

                # ラベル情報
                label1 = club.get("ラベル1", "N/A")
                label2 = club.get("ラベル２", "N/A")
                if label1 != "N/A" or label2 != "N/A":
                    labels_text = f"🏷️ カテゴリ: {label2}" + (f" / {label1}" if label1 != "N/A" else "")
                    labels_label = QtWidgets.QLabel(labels_text)
                    labels_label.setStyleSheet(
                        "font-size: 15px; color: #aaaaaa; margin: 5px 0; padding-left: 10px; font-style: italic; background-color: transparent;"
                    )
                    club_layout.addWidget(labels_label)

                self.club_content_layout.addWidget(club_frame)

                print(f"[UI DEBUG] Club {i} added to layout")



        self.club_content_layout.addStretch()
        scroll_area.setWidget(self.content_widget)
        modal_layout.addWidget(scroll_area)

        # 閉じるボタン
        close_button = QtWidgets.QPushButton("閉じる")
        close_button.setStyleSheet("font-size: 18px; padding: 10px; background-color: #e74c3c; color: white; border-radius: 5px; border: none;")
        close_button.clicked.connect(modal.close)
        modal_layout.addWidget(close_button, alignment=QtCore.Qt.AlignCenter)

        # モーダルを表示
        modal.exec()


        # サークル情報コンテナを表示
        print(f"[UI DEBUG] Container visibility before show: {self.content_widget.isVisible()}")
        print(f"[UI DEBUG] Container visibility after show: {self.content_widget.isVisible()}")
        print("[UI DEBUG] Club info container shown")

        # サークル情報が表示されていることを示すフラグを設定
        self.clubs_displayed = True
        print("[UI DEBUG] clubs_displayed flag set to True")

        # 強制的にウィジェットを更新
        self.content_widget.update()
        self.update()
        print("[UI DEBUG] UI update forced")

    def test_display(self):
        """テスト用：サークル情報表示のテスト"""
        test_clubs = [
            {
                "サークル": "テストサークル1",
                "活動内容": "テスト活動内容1",
                "活動日時・場所": "テスト日時・場所1",
                "ラベル1": "テストラベル1",
                "ラベル２": "テストラベル2",
            }
        ]
        print("Testing display with test clubs")
        self.display_club_info_modal(test_clubs)


    def receive_club_data(self, clubs):
        """外部からサークルデータを受信し、Signalを発行"""
        print(f"[UI DEBUG] receive_club_data called with {len(clubs)} clubs")
        self.club_data_received.emit(clubs)

    def resizeEvent(self, event):
        """ウィンドウサイズ変更時に画像位置を調整"""
        super().resizeEvent(event)
        
        # 表示中の画像の位置を再調整
        for i, widget in enumerate(self.displayed_image_widgets):
            if i < len(self.used_positions):
                self.position_image_widget(widget, self.used_positions[i])

    def closeEvent(self, event):
        """ウィンドウが閉じられたときに音声レベル表示を停止"""
        self.stop_audio_stream()
        super().closeEvent(event)
