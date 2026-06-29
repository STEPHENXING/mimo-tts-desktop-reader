from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import os
from collections import deque

class AudioPlayer(QObject):
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)
        
        self.playlist = deque()
        self.is_playing = False
        self.is_paused = False
        
        # When media finishes playing, play the next one in the queue
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)

    @Slot(str)
    def enqueue_audio(self, file_path):
        """Adds an audio file to the playlist and plays if not currently playing."""
        if not os.path.exists(file_path):
            print(f"Audio file not found: {file_path}")
            return
            
        abs_path = os.path.abspath(file_path)
        self.playlist.append(abs_path)
        
        # Start immediately if idle
        if not self.is_playing and not self.is_paused:
            self.play_next()

    def play_next(self):
        if self.playlist:
            file_path = self.playlist.popleft()
            self.is_playing = True
            self.is_paused = False
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()
        else:
            self.is_playing = False

    def on_media_status_changed(self, status):
        # Auto advance on media end
        if status == QMediaPlayer.EndOfMedia:
            self.play_next()

    def pause(self):
        self.is_paused = True
        if self.is_playing:
            self.player.pause()

    def resume(self):
        if not self.is_paused:
            return

        self.is_paused = False
        if self.is_playing:
            self.player.play()
        else:
            self.play_next()

    def toggle_pause(self):
        if self.is_paused:
            self.resume()
        else:
            self.pause()
        return self.is_paused

    def stop(self):
        self.player.stop()
        self.playlist.clear()
        self.is_playing = False
        self.is_paused = False
        
    def clear_queue(self):
        self.stop()
