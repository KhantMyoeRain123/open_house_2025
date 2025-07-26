from PySide6 import QtCore, QtWidgets


class ChatUI(QtWidgets.QWidget):
    # Signal for club data display
    club_data_received = QtCore.Signal(list)

    def __init__(self, chatbot):
        super().__init__()

        self.chatbot = chatbot
        self.setup_ui()

        # Connect the signal to the display method
        self.club_data_received.connect(self.display_club_info)

        # チャットボットの状態変化を監視するタイマー
        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(100)  # 100ms間隔で更新

    def setup_ui(self):
        self.setWindowTitle("ワセクラ - 早稲田大学サークル推薦AI")

        # メインレイアウト
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(20)  # 要素間のスペースを増やす

        # タイトル
        title = QtWidgets.QLabel("ワセクラ - 早稲田大学サークル推薦AI", alignment=QtCore.Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold; margin: 15px; color: #2c3e50; background-color: #ecf0f1; padding: 15px; border-radius: 10px;"
        )
        self.layout.addWidget(title)

        # 状態表示エリア
        self.status_widget = QtWidgets.QWidget()
        status_layout = QtWidgets.QHBoxLayout(self.status_widget)

        self.status_icon = QtWidgets.QLabel("[待機]")
        self.status_icon.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; padding: 10px;")
        self.status_text = QtWidgets.QLabel("待機中...")
        self.status_text.setStyleSheet("font-size: 18px; color: #7f8c8d; padding: 10px;")

        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        self.layout.addWidget(self.status_widget)

        # サークル情報表示エリア（中央）
        self.club_info_container = QtWidgets.QWidget()
        self.club_info_layout = QtWidgets.QVBoxLayout(self.club_info_container)

        # サークル情報タイトル
        self.club_info_title = QtWidgets.QLabel("あなたにおすすめのサークル", alignment=QtCore.Qt.AlignCenter)
        self.club_info_title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2c3e50; margin: 10px; padding: 10px;"
        )
        self.club_info_layout.addWidget(self.club_info_title)

        # スクロール可能なサークル情報エリア
        self.club_scroll_area = QtWidgets.QScrollArea()
        self.club_scroll_area.setWidgetResizable(True)
        self.club_scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                min-height: 300px;
                max-height: 400px;
            }
        """)

        self.club_content_widget = QtWidgets.QWidget()
        self.club_content_layout = QtWidgets.QVBoxLayout(self.club_content_widget)
        self.club_scroll_area.setWidget(self.club_content_widget)
        self.club_info_layout.addWidget(self.club_scroll_area)

        # 初期状態では非表示
        self.club_info_container.hide()
        self.layout.addWidget(self.club_info_container)

        # テスト用: サークル情報エリアが正しく表示されるかテスト
        # self.test_display()  # デバッグ時に有効化

        # 下部の大きな録音ボタンエリア
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QVBoxLayout(button_container)
        button_layout.setAlignment(QtCore.Qt.AlignCenter)
        button_layout.setContentsMargins(0, 30, 0, 30)  # 上下の余白を調整

        # ボタンの説明テキスト
        self.button_instruction = QtWidgets.QLabel(
            "クリックして音声で話しかけてください", alignment=QtCore.Qt.AlignCenter
        )
        self.button_instruction.setStyleSheet("font-size: 16px; color: #7f8c8d; margin: 10px;")
        button_layout.addWidget(self.button_instruction)

        # 大きな円形の録音ボタン
        self.button = QtWidgets.QPushButton("話す!")
        self.button.setFixedSize(180, 180)  # ボタンサイズを大きく
        self.button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 90px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
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

    def update_status(self):
        """チャットボットの状態に応じてUIを更新"""
        if self.clubs_displayed:
            # サークル情報が表示されている時は終了ボタンとして表示
            self.status_icon.setText("[完了]")
            self.status_icon.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60; padding: 10px;")
            self.status_text.setText("サークル情報を確認してください")
            self.status_text.setStyleSheet("font-size: 18px; color: #27ae60; padding: 10px;")
            self.button.setEnabled(True)
            self.button.setText("終了")
            self.button_instruction.setText("アプリを終了するにはボタンをクリックしてください")
            self._update_exit_button_style()
        elif self.chatbot.is_recording:
            self.status_icon.setText("[録音中]")
            self.status_icon.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c; padding: 10px;")
            self.status_text.setText("録音中... 話してください")
            self.status_text.setStyleSheet("font-size: 18px; color: #e74c3c; font-weight: bold; padding: 10px;")
            self.button.setEnabled(True)  # 録音中は停止ボタンとして有効
            self.button.setText("停止")
            self.button_instruction.setText("録音を停止するにはボタンをクリックしてください")
        elif hasattr(self.chatbot, "is_speaking") and self.chatbot.is_speaking:
            self.status_icon.setText("[ワセクラ発話中]")
            self.status_icon.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60; padding: 10px;")
            self.status_text.setText("ワセクラが話しています...")
            self.status_text.setStyleSheet("font-size: 18px; color: #27ae60; padding: 10px;")
            self.button.setEnabled(False)  # 発話中はボタン無効
            self.button.setText("話す!")
            self.button_instruction.setText("ワセクラの発話が終わるまでお待ちください")
            self._update_button_disabled_style()
        elif hasattr(self.chatbot, "is_processing") and self.chatbot.is_processing:
            self.status_icon.setText("[処理中]")
            self.status_icon.setStyleSheet("font-size: 18px; font-weight: bold; color: #9b59b6; padding: 10px;")
            self.status_text.setText("ワセクラが考え中...")
            self.status_text.setStyleSheet("font-size: 18px; color: #9b59b6; padding: 10px;")
            self.button.setEnabled(False)  # 処理中はボタン無効
            self.button.setText("処理中...")
            self.button_instruction.setText("ワセクラが処理中です... しばらくお待ちください")
            self._update_button_disabled_style()
        elif self.chatbot.is_listening and not self.chatbot.is_recording:
            self.status_icon.setText("[待機]")
            self.status_icon.setStyleSheet("font-size: 18px; font-weight: bold; color: #f39c12; padding: 10px;")
            self.status_text.setText("音声待機中... ボタンを押して話してください")
            self.status_text.setStyleSheet("font-size: 18px; color: #f39c12; padding: 10px;")
            self.button.setEnabled(True)  # 待機中はボタン有効
            self.button.setText("話す!")
            self.button_instruction.setText("クリックして音声で話しかけてください")
            if self.button.text() != "停止":  # 録音中でない場合のみスタイルを復元
                self._restore_normal_button_style()
        else:
            self.status_icon.setText("[待機]")
            self.status_icon.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; padding: 10px;")
            self.status_text.setText("待機中...")
            self.status_text.setStyleSheet("font-size: 18px; color: #7f8c8d; padding: 10px;")
            self.button.setEnabled(True)  # 通常時はボタン有効
            if self.button.text() != "停止":  # 録音中でない場合のみ
                self.button.setText("話す!")
                self.button_instruction.setText("クリックして音声で話しかけてください")
                self._restore_normal_button_style()

    def _update_button_disabled_style(self):
        """ボタンが無効な時のスタイルを設定"""
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #bdc3c7;
                color: #7f8c8d;
                border: none;
                border-radius: 90px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)

    def update_realtime_text(self, text):
        """リアルタイム音声認識結果を更新（削除済みのため何もしない）"""
        pass

    def handle_button_click(self):
        """ボタンクリックを処理（録音開始/停止 or アプリ終了）"""
        if self.clubs_displayed:
            # サークル情報が表示されている場合はアプリを終了
            QtWidgets.QApplication.quit()
        else:
            # 通常の録音機能
            self.record_voice()

    @QtCore.Slot()
    def record_voice(self):
        # ボタンが無効な時は何もしない
        if not self.button.isEnabled():
            return

        if not self.chatbot.is_recording:
            self.chatbot.start_recording()
            self._update_recording_button_style()
        else:
            self.chatbot.stop_recording()
            self._restore_normal_button_style()

    def _update_recording_button_style(self):
        """録音中のボタンスタイルを設定"""
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 90px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)

    def _restore_normal_button_style(self):
        """通常時のボタンスタイルを復元"""
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 90px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)

    def _update_exit_button_style(self):
        """終了ボタンのスタイルを設定"""
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 90px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)

    def display_club_info(self, clubs):
        """サークル情報を表示"""
        print(f"[UI DEBUG] display_club_info called with {len(clubs)} clubs")
        print(f"[UI DEBUG] Club info container exists: {hasattr(self, 'club_info_container')}")
        print(f"[UI DEBUG] Club content layout exists: {hasattr(self, 'club_content_layout')}")

        # 既存の内容をクリア
        for i in reversed(range(self.club_content_layout.count())):
            child = self.club_content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        print("[UI DEBUG] Cleared existing content")

        if not clubs:
            # サークルが見つからない場合
            no_clubs_label = QtWidgets.QLabel(
                "申し訳ございませんが、条件に合うサークルが見つかりませんでした。", alignment=QtCore.Qt.AlignCenter
            )
            no_clubs_label.setStyleSheet("font-size: 16px; color: #e74c3c; padding: 20px;")
            self.club_content_layout.addWidget(no_clubs_label)
            print("[UI DEBUG] No clubs message added")
        else:
            # 各サークルの情報を表示
            for i, club in enumerate(clubs):
                print(f"[UI DEBUG] Adding club {i}: {club.get('サークル', 'N/A')}")
                club_frame = QtWidgets.QFrame()
                club_frame.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border: 1px solid #dee2e6;
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
                club_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 5px;")
                club_layout.addWidget(club_name)

                # 活動内容
                activity_content = club.get("活動内容", "N/A")
                if activity_content != "N/A":
                    activity_label = QtWidgets.QLabel(f"🎯 活動内容: {activity_content}")
                    activity_label.setStyleSheet("font-size: 14px; color: #34495e; margin: 3px 0; padding-left: 10px;")
                    activity_label.setWordWrap(True)
                    club_layout.addWidget(activity_label)

                # 活動日時・場所
                schedule = club.get("活動日時・場所", "N/A")
                if schedule != "N/A":
                    schedule_label = QtWidgets.QLabel(f"🕒 活動日時・場所: {schedule}")
                    schedule_label.setStyleSheet("font-size: 14px; color: #34495e; margin: 3px 0; padding-left: 10px;")
                    schedule_label.setWordWrap(True)
                    club_layout.addWidget(schedule_label)

                # ラベル情報
                label1 = club.get("ラベル1", "N/A")
                label2 = club.get("ラベル２", "N/A")
                if label1 != "N/A" or label2 != "N/A":
                    labels_text = f"🏷️ カテゴリ: {label2}" + (f" / {label1}" if label1 != "N/A" else "")
                    labels_label = QtWidgets.QLabel(labels_text)
                    labels_label.setStyleSheet(
                        "font-size: 13px; color: #7f8c8d; margin: 5px 0; padding-left: 10px; font-style: italic;"
                    )
                    club_layout.addWidget(labels_label)

                self.club_content_layout.addWidget(club_frame)
                print(f"[UI DEBUG] Club {i} added to layout")

        # スペーサーを追加してレイアウトを整える
        self.club_content_layout.addStretch()

        # サークル情報コンテナを表示
        print(f"[UI DEBUG] Container visibility before show: {self.club_info_container.isVisible()}")
        self.club_info_container.show()
        print(f"[UI DEBUG] Container visibility after show: {self.club_info_container.isVisible()}")
        print("[UI DEBUG] Club info container shown")

        # サークル情報が表示されていることを示すフラグを設定
        self.clubs_displayed = True
        print("[UI DEBUG] clubs_displayed flag set to True")

        # 強制的にウィジェットを更新
        self.club_info_container.update()
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
        self.display_club_info(test_clubs)

    def receive_club_data(self, clubs):
        """外部からサークルデータを受信し、Signalを発行"""
        print(f"[UI DEBUG] receive_club_data called with {len(clubs)} clubs")
        self.club_data_received.emit(clubs)
