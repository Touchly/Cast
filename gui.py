from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication,QMainWindow, QWidget, QLabel, QVBoxLayout,QHBoxLayout, QPushButton, QFileDialog, QSplitter, QScrollArea
from PySide6.QtGui import QPixmap, QIcon, QAction
from PySide6.QtCore import Qt, QTimer, QSettings
import sys
import os
import userpaths
from server import Server

if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

settings = QSettings("Touchly", "Cast")
folders = settings.value("folders", {})

def update_mounts(server, time=100):
        # Get name, path
        server_state = server.get_state()

        # Running -> Stop
        if server_state[0]=="R":
            print("stop")
            server.stop()
            update_mounts(server)
        # Stopping -> Call again
        elif server_state == "Stopping server...":
            print("wait")
            timer = QTimer()
            timer.timeout.connect(update_mounts)
            timer.start(time)
        # Stopped -> Update mounts and Start
        elif server_state in ["Server stopped", "Preparing...", "Error starting server"]:
            print("start")
            server.clear_mounts()
            for key in folders:
                print(key, folders[key]["name"])
                server.add_mount(key, folders[key]["name"])
            server.start(port = 8080)

class FolderElement(QWidget):

    def deleteSelf(self):
        folders.pop(self.path)
        update_mounts(server)
        self.hide()
        # Code to take it out of folders dictionary

    def __init__(self, name: str = "Unknown", path:str = "/"):
        super().__init__()


        layout = QHBoxLayout()
        #self.setStyleSheet(f"background-color: red;")
        
        icon = QPixmap(os.path.join(application_path, "folder.png"))
        icon = icon.scaled(40, 40, Qt.KeepAspectRatio) 

        label = QLabel()
        
        label.setPixmap(icon)

        layout.addWidget(label)

        infoLayout = QVBoxLayout()
        infoLayout.setSpacing(0)        
        nameLabel = QLabel(name)
        pathLabel = QLabel(path)
        self.path = path
        
        pathLabel.setObjectName("pathLabel")
        pathLabel.setAlignment(Qt.AlignLeft)

        nameLabel.setObjectName("nameLabel")
        nameLabel.setAlignment(Qt.AlignLeft)

        # Make them closer
        self.setMaximumHeight(50)

        infoLayout.addWidget(nameLabel)
        infoLayout.addWidget(pathLabel)

        layout.addLayout(infoLayout)
        

        deleteButton = QPushButton("X")
        deleteButton.setObjectName("deleteButton")
        
        deleteButton.clicked.connect(self.deleteSelf)

        layout.addWidget(deleteButton)
        
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def updateFolders(self):
        for key in folders:
            name = folders[key]["name"]
            path = folders[key]["path"]
            folderElement = FolderElement(name= name, path= path)
            self.scrollable_layout.addWidget(folderElement)

    def showFolderDialog(self):
        getSaveFileUrl = QFileDialog.getExistingDirectory(self.main, "Select the folder you want to add")
        self.addFolder(getSaveFileUrl)

    def addFolder(self, path):
        # Check if folder is already in folders
        if folders.get(path) == None:
            print(path)
            # Get folder name using
            folderData = {}
            name = os.path.basename(path)
            folderData["name"] = name
            folderData["path"] = path
            folderData["video_count"] = len(os.listdir(path))

            print(folderData)

            folders[path] = folderData

            # Add to GUI
            folderElement = FolderElement(name= name, path= path)
            self.scrollable_layout.addWidget(folderElement)

            # Add to server
            update_mounts(server)
    
    def update_server_state(self, server, time=100):
        server_state = server.get_state()
        self.status.setText(server_state)

        if server_state[0]!="R":
            timer = QTimer()
            timer.timeout.connect(self.update_server_state)
            timer.start(time)

    def __init__(self):
        super().__init__()

        # Main window
        self.main = QWidget()
        self.main.setObjectName("MainWindow")

        self.main.setWindowTitle("Touchly renderer")
        self.main.show()

        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(20)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        first = QHBoxLayout()
        first.setAlignment(Qt.AlignVCenter)

        self.status = QLabel("Starting server...")
        self.status.setObjectName("status")
        self.status.setAlignment(Qt.AlignVCenter)

        first.addWidget(self.status)
        
        rightbar = QHBoxLayout()
        rightbar.alignment = Qt.AlignRight
        rightbar.setSpacing(10)
        addfolder = QPushButton("Add folder")
        addfolder.setObjectName("addfolder")

        addfolder.clicked.connect(self.showFolderDialog)
        
        rightbar.addWidget(addfolder)        
        first.addLayout(rightbar)

        # Folder grid
        self.folderList = QVBoxLayout()
        self.folderList.setAlignment(Qt.AlignVCenter)

        scrollable_widget = QWidget()
        scrollable_widget.setObjectName("scrollable_widget")
        self.scrollable_layout = QVBoxLayout()
        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scrollable_widget)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scrollable_widget.setLayout(self.scrollable_layout)
        scroll_area.setWidget(scrollable_widget)

        path = userpaths.get_my_videos().replace("\\", "/")

        if len(folders) == 0:
            item1 = FolderElement(name = "My Videos", path = path)
            folderData = {}
            name = os.path.basename(path)
            folderData["name"] = name
            folderData["path"] = path
            folderData["video_count"] = len(os.listdir(path))
            folders[path] = folderData
            self.scrollable_layout.addWidget(item1)

        self.updateFolders()

        mainLayout.addLayout(first, 1)
        mainLayout.addWidget(scroll_area, 10)

        self.main.setLayout(mainLayout)
        self.setCentralWidget(self.main)
        self.show()

        global server
        server = Server(path = application_path)
        update_mounts(server)

        self.update_server_state(server, time=100)

def closeEvent():
    print("Closing")
    settings.setValue("folders", folders)
    server.stop()
    app.quit()

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.aboutToQuit.connect(closeEvent) 

    menu = QMenu()

    tray_icon = QSystemTrayIcon(QIcon(os.path.join(application_path, "icon.ico")))
    tray_icon.show()

    quit = QAction("Quit")
    quit.triggered.connect(closeEvent)
    menu.addAction(quit)
    
    tray_icon.setContextMenu(menu)

    w = MainWindow()
    w.resize(600, 400)
    w.show()
    
    with open(os.path.join(application_path, "style.qss"), "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    app.exec()