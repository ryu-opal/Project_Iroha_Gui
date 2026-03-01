import sys
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QSystemTrayIcon, QMenu, QFileDialog
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QPoint, QSettings

class VtuberWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAcceptDrops(True) 

        self.settings = QSettings("Kodi-IrohaProject", "DesktopSticker")
        self.is_movable = self.settings.value("is_movable", True, type=bool) 
        self.is_resizing = False

        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        if not self.is_movable:
            flags |= Qt.WindowTransparentForInput 

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAcceptDrops(True) 

        self.scale_factor = float(self.settings.value("scale_factor", 1.0))
        self.image_path = self.settings.value("last_image_path", "")
        self.original_pixmap = QPixmap(self.image_path) if self.image_path else QPixmap()
        
        self.update_display() 
        

        saved_pos = self.settings.value("window_pos", QPoint(100, 100))
        #last time position 
        self.move(saved_pos)
        self.old_pos = None

        self.tray_icon = QSystemTrayIcon(self)

        if not self.original_pixmap.isNull():
            self.tray_icon.setIcon(self.original_pixmap)
        else:
            
            fallback = QPixmap(32, 32)
            fallback.fill(Qt.white)
            self.tray_icon.setIcon(fallback)
        
        self.tray_menu = QMenu()
        
        clear_pic_action = self.tray_menu.addAction("Reset")
        clear_pic_action.triggered.connect(self.clear_picture)
        
        self.tray_menu.addSeparator()
        
        if self.is_movable:
            self.toggle_action = self.tray_menu.addAction("Moveable: YES")
        else:
            self.toggle_action = self.tray_menu.addAction("Moveable: NO")
            
        self.toggle_action.triggered.connect(self.toggle_click_through)
        
        self.tray_menu.addSeparator()
        
        self.resize_action = self.tray_menu.addAction("Resize: Unlock")
        self.resize_action.triggered.connect(self.toggle_resize_mode)
        
        self.tray_menu.addSeparator() 
        
        quit_action = self.tray_menu.addAction("Leave")
        quit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def update_display(self):
        if not self.original_pixmap.isNull():
            new_w = int(self.original_pixmap.width() * self.scale_factor)
            new_h = int(self.original_pixmap.height() * self.scale_factor)
            scaled_pixmap = self.original_pixmap.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled_pixmap)
        else:
            new_w = int(600 * self.scale_factor)
            new_h = int(600 * self.scale_factor)
            self.label.clear() 
            
        if self.is_resizing:
            style = "border: 4px solid lightpink; background-color: rgba(255, 182, 193, 100);"
        else:
            if not self.original_pixmap.isNull():
                style = "border: none; background-color: transparent;"
            else:
                style = """
                    border: 4px solid rgba(255, 000, 000, 150); 
                    background-color: rgba(255, 000, 000, 80);
                    border-radius: 10px;
                """
        
        self.label.setStyleSheet(style)
        self.label.resize(new_w, new_h)
        self.resize(new_w, new_h)

    def toggle_resize_mode(self):
        self.is_resizing = not self.is_resizing
        if self.is_resizing:
            self.resize_action.setText("Resize: Lock")
        else:
            self.resize_action.setText("Resize: Unlock")
        self.update_display()

    def toggle_click_through(self):
        self.is_movable = not self.is_movable
        
        self.settings.setValue("is_movable", self.is_movable) 
        
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        if not self.is_movable:
            flags |= Qt.WindowTransparentForInput
            self.toggle_action.setText("Moveable: NO")
        else:
            self.toggle_action.setText("Moveable: YES")
        
        self.setWindowFlags(flags)
        self.show()

    def clear_picture(self):
        self.settings.remove("last_image_path")
        self.image_path = ""
        self.original_pixmap = QPixmap()
        fallback = QPixmap(32, 32)
        fallback.fill(Qt.white)
        self.tray_icon.setIcon(fallback)
        self.is_movable = True
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        self.setWindowFlags(flags) 
        self.toggle_action.setText("Moveable: YES") 
        self.show() 
        self.update_display()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_movable:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None and self.is_movable:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        self.settings.setValue("window_pos", self.pos()) 
        #position

    def wheelEvent(self, event):
        if self.is_resizing:
            angle = event.angleDelta().y()
            if angle > 0: self.scale_factor += 0.05
            else:
                if self.scale_factor > 0.1: self.scale_factor -= 0.05
            self.settings.setValue("scale_factor", self.scale_factor) 
            #size
            self.update_display()

    def dragEnterEvent(self, event):

        if self.is_movable and event.mimeData().hasUrls():
            event.accept() 
        else:
            event.ignore() 

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                self.image_path = file_path
                self.original_pixmap = QPixmap(self.image_path)
                self.settings.setValue("last_image_path", self.image_path)
                self.tray_icon.setIcon(self.original_pixmap)
                self.update_display()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VtuberWindow()
    window.show()
    sys.exit(app.exec())
