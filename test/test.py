import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QLineEdit, QFileDialog, QProgressBar, QInputDialog, QRadioButton, QGroupBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from pytube import YouTube, Playlist

class DownloadWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)

    def __init__(self, url, download_path, download_format):
        super().__init__()
        self.url = url
        self.download_path = download_path
        self.download_format = download_format

    def run(self):
        def on_progress_callback(stream, chunk, bytes_remaining):
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            percentage = int((bytes_downloaded / total_size) * 100)
            self.progress_signal.emit(percentage)

        try:
            if "playlist" in self.url.lower():
                playlist = Playlist(self.url)
                self.log_signal.emit(f"Total videos in playlist: {len(playlist.video_urls)}")
                for i, video_url in enumerate(playlist.video_urls, start=1):
                    self.download_video(video_url, on_progress_callback, i, len(playlist.video_urls))
            else:
                self.download_video(self.url, on_progress_callback, 1, 1)
        except Exception as e:
            self.log_signal.emit(f"Error downloading {self.url}: {str(e)}")

    def download_video(self, video_url, on_progress_callback, current_video, total_videos):
        yt = YouTube(video_url, on_progress_callback=on_progress_callback)

        if self.download_format == 'mp3':
            audio_stream = yt.streams.filter(only_audio=True).first()
            audio_stream.download(self.download_path)
            self.log_signal.emit(f"Downloaded audio ({current_video}/{total_videos}): {yt.title}")
        else:
            video = yt.streams.get_highest_resolution()
            video.download(self.download_path)
            self.log_signal.emit(f"Downloaded video ({current_video}/{total_videos}): {yt.title}")

class YouTubeDownloaderApp(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Gdownloader')
        self.setGeometry(100, 100, 600, 400)
        self.setWindowIcon(QIcon('./Gicon.png'))

        self.url_label = QLabel('Enter youtube URL or playlist URL :')
        self.url_textedit = QTextEdit()

        self.path_label = QLabel('Download Path:')
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText('Select or enter download path...')
        self.browse_button = QPushButton('Browse', self)
        self.browse_button.clicked.connect(self.browse_path)

        self.download_button = QPushButton('Download', self)
        self.download_button.clicked.connect(self.download_videos)

        self.refresh_button = QPushButton('Refresh', self)
        self.refresh_button.clicked.connect(self.refresh_ui)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.log_label = QLabel('Log:')
        self.log_textedit = QTextEdit()
        self.log_textedit.setReadOnly(True)

        self.format_label = QLabel('Select Download Format:')
        self.mp3_radio = QRadioButton('MP3', self)
        self.mp4_radio = QRadioButton('MP4', self)
        self.mp4_radio.setChecked(True)  # Default to MP4

        format_layout = QVBoxLayout()
        format_layout.addWidget(self.format_label)
        format_layout.addWidget(self.mp3_radio)
        format_layout.addWidget(self.mp4_radio)

        self.format_group = QGroupBox()
        self.format_group.setLayout(format_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_textedit)
        layout.addWidget(self.path_label)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.format_group) 
        layout.addWidget(self.download_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_label)
        layout.addWidget(self.log_textedit)
         # Add the format group to the main layout

        self.copyright_label = QLabel('Copyright © 2023 Gemii. All rights reserved.')
        self.copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.copyright_label)

        self.setLayout(layout)

        self.download_worker = None

    def browse_path(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Download Folder")

        if folder_path:
            self.path_edit.setText(folder_path)

    def download_videos(self):
        video_url = self.url_textedit.toPlainText().strip()
        download_path = self.path_edit.text()

        if not video_url:
            self.show_input_url_dialog()
            return

        self.progress_bar.setValue(0)

        format_selected = 'mp3' if self.mp3_radio.isChecked() else 'mp4'

        self.download_worker = DownloadWorker(video_url, download_path, format_selected)
        self.download_worker.progress_signal.connect(self.update_progress)
        self.download_worker.log_signal.connect(self.log)
        self.download_worker.start()

    def show_input_url_dialog(self):
        text, ok = QInputDialog.getText(self, 'Input your URL', 'Enter youTube URL or playlist URL:')
        if ok and text:
            self.url_textedit.setPlainText(text)

    def refresh_ui(self):
        self.url_textedit.clear()
        self.path_edit.clear()
        self.log_textedit.clear()
        self.progress_bar.setValue(0)

        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.terminate()

    def update_progress(self, percentage):
        self.progress_bar.setValue(percentage)

    def log(self, message):
        current_log = self.log_textedit.toPlainText()
        self.log_textedit.setPlainText(current_log + '\n' + message)
        self.log_textedit.verticalScrollBar().setValue(self.log_textedit.verticalScrollBar().maximum())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YouTubeDownloaderApp()
    window.show()
    sys.exit(app.exec())
