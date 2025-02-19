import os
from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtCore import QTimer, QUrl, Qt

render_timeout = 10

class OffscreenScreenshot(QWebEngineView):
    """
    A QWebEngineView that is moved offscreen to allow rendering while remaining invisible.
    After loading a URL, it waits briefly, takes a screenshot, and saves it.
    """
    def __init__(self, url, ip, title, done_callback, parent=None):
        super(OffscreenScreenshot, self).__init__(parent)
        self.ip = ip
        forbiddenChars = ['\\','/',':','*','?','"','<','>','|']  # 9 forbidden chars in WinOS file system
        replacmntChars = ['＼','／','：','＊','？','＂','＜','＞','｜']
        for i in range(8):
            title = title.replace(forbiddenChars[i],replacmntChars[i])
        self._title = title
        self.done_callback = done_callback
        
        # Instead of WA_DontShowOnScreen, move the widget offscreen.
        # This makes the widget visible to the rendering system while not actually showing it.
        self.setGeometry(-2000, -2000, 1920, 1080)
        self.resize(1920, 1080)
        self.show()  # Ensure the widget is realized and rendering occurs.
        
        # Connect the loadFinished signal.
        self.loadFinished.connect(self.on_load_finished)
        self.load(QUrl(url))
    
    def on_load_finished(self, ok):
        if ok:
            # Wait a bit to ensure full rendering before capturing.
            QTimer.singleShot(render_timeout*1000, self.take_screenshot)
        else:
            print(f"Page failed to load for {self.ip}")
            self.done_callback()
    
    def take_screenshot(self):
        # Grab a pixmap of the rendered page.
        pixmap = self.grab()
        image = pixmap.toImage()
        # Check if the image is all white by sampling every 10th pixel
        all_white = True
        for y in range(0, image.height(), 10):
            for x in range(0, image.width(), 10):
                if image.pixelColor(x, y) != Qt.white:
                    all_white = False
                    break
            if not all_white:
                break

        if not all_white:
            os.makedirs("./resources", exist_ok=True)
            filename = f"./resources/{self._title}_{self.ip}.png"
            pixmap.save(filename)
        self.done_callback()
