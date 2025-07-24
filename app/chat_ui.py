from PySide6 import QtWidgets, QtCore, QtGui

class CustomItem(QtWidgets.QWidget):
    def __init__(self, text):
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)

        self.label = QtWidgets.QLabel(text)

        self.button = QtWidgets.QPushButton("Click")

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.button)

        self.setLayout(layout)

class ChatUI(QtWidgets.QWidget):
    def __init__(self, chatbot):
        super().__init__()

        self.chatbot = chatbot
        self.setWindowTitle("ワセクラ チャット")
        self.setMinimumSize(400, 600)

        # Widgets
        self.text = QtWidgets.QLabel("こんにちは！")
        self.text.setAlignment(QtCore.Qt.AlignCenter)

        self.club_list = QtWidgets.QListWidget()

        self.button = QtWidgets.QPushButton("話す！")
        self.button.setFixedHeight(40)

        # Layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.club_list)
        self.layout.addWidget(self.button)

        # Connections
        self.button.clicked.connect(self.record_voice)
        self.chatbot

    @QtCore.Slot()
    def record_voice(self):
        if not self.chatbot.is_recording:
            self.chatbot.start_recording()
            self.button.setText("止める！")
        else:
            self.chatbot.stop_recording()
            self.button.setText("話す!")
            
    def update_club_list(self, clubs):
        self.club_list.clear()
        for i, club in enumerate(clubs):
            item = QtWidgets.QListWidgetItem()
            # Prepare display text for each club (customize as needed)
            text = f"{club.get('サークル', 'N/A')} - {club.get('活動内容', '')}"
            custom_widget = CustomItem(text)
            item.setSizeHint(custom_widget.sizeHint())
            self.club_list.addItem(item)
            self.club_list.setItemWidget(item, custom_widget)