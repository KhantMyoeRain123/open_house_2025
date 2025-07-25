from PySide6 import QtWidgets, QtCore, QtGui

class CustomItem(QtWidgets.QWidget):
    def __init__(self, title, description):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        title_label = QtWidgets.QLabel(title)
        description_label = QtWidgets.QLabel(description)

        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        description_label.setStyleSheet("color: #bbbbbb; font-size: 13px;")

        layout.addWidget(title_label)
        layout.addWidget(description_label)

        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border-radius: 8px;
            }
        """)


class ChatUI(QtWidgets.QWidget):
    def __init__(self, chatbot):
        super().__init__()

        self.chatbot = chatbot
        self.setWindowTitle("ワセクラ チャット")
        self.setMinimumSize(400, 600)
        self.setStyleSheet("background-color: black;")

        # Widgets
        self.text = QtWidgets.QLabel("ワセクラ - 早稲田大学サークル推薦AI")
        self.text.setAlignment(QtCore.Qt.AlignCenter)
        

        self.club_list = QtWidgets.QListWidget()
        
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QVBoxLayout(button_container)
        button_layout.setAlignment(QtCore.Qt.AlignCenter)
        button_layout.setContentsMargins(0, 50, 0, 50) 

        self.button = QtWidgets.QPushButton("話す!")
        self.button.setFixedSize(90, 90)  # ボタンサイズを大きく
        self.button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 45px;
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

        # Layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        self.button_instruction = QtWidgets.QLabel("クリックして音声で話しかけてください", alignment=QtCore.Qt.AlignCenter)
        self.button_instruction.setStyleSheet("font-size: 16px; color: #7f8c8d; margin: 10px;")
        
        self.reset_button = QtWidgets.QPushButton("リセット")
        self.reset_button.setFixedSize(100, 40)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
            QPushButton:pressed {
                background-color: #707b7c;
            }
        """)
        #self.reset_button.clicked.connect(self.reset_club_list)

        reset_wrapper = QtWidgets.QHBoxLayout()
        reset_wrapper.setContentsMargins(0, 10, 0, 0)
        reset_wrapper.addStretch()
        reset_wrapper.addWidget(self.reset_button)
        reset_wrapper.addStretch()

        
        # ボタンを中央に配置するためのレイアウト調整
        button_wrapper = QtWidgets.QHBoxLayout()
        button_wrapper.addStretch()
        button_wrapper.addWidget(self.button)
        button_wrapper.addStretch()
        
        button_layout.addLayout(button_wrapper)
        button_layout.addWidget(self.button_instruction)
        button_layout.addLayout(reset_wrapper)
        

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.club_list)
        self.layout.addWidget(button_container)
        #self.layout.addWidget(self.button)

        # Connections
        self.button.clicked.connect(self.record_voice)
        self.reset_button.clicked.connect(self.reset_app)

    @QtCore.Slot()
    def reset_app(self):
        self.button.setText("話す!")
        self.button.setStyleSheet("""
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 45px;
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
        self.button_instruction.setText("クリックして音声で話しかけてください")
        self.club_list.clear()
        self.chatbot.reset=True
    @QtCore.Slot()
    def record_voice(self):
        if not self.chatbot.is_replying:
            if not self.chatbot.is_recording:
                self.chatbot.start_recording()
                self.button.setText("止める！")
                self.button.setStyleSheet("""
                QPushButton {
                    background-color: #d1342c;
                    color: white;
                    border: none;
                    border-radius: 45px;
                    font-size: 24px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #851711;
                }
                QPushButton:pressed {
                    background-color: #851711;
                }
                """)
                self.button_instruction.setText("録音中")
            else:
                self.chatbot.stop_recording()
                self.button.setText("話す!")
                self.button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 45px;
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
                self.button_instruction.setText("クリックして音声で話しかけてください")
            
    def update_club_list(self, clubs):
        self.club_list.clear()
        for i, club in enumerate(clubs):
            item = QtWidgets.QListWidgetItem()
            # Prepare display text for each club (customize as needed)
            title=f"{club.get('サークル', 'N/A')}"
            description=f"{club.get('活動内容', 'N/A')}"
            custom_widget = CustomItem(title,description)
            item.setSizeHint(custom_widget.sizeHint())
            self.club_list.addItem(item)
            self.club_list.setItemWidget(item, custom_widget)