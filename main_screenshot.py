import os
import sys
import random
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# -----------------------
# PART 1: Website Checking (Multithreading)
# -----------------------

timeout = 5
boring_titles = ['Node.js packaged by Bitnami',
                 'Sorry, the website has been stopped',
                 'Apache2 Ubuntu Default Page: It works',
                 'Welcome to nginx!', 
                 'IIS Windows Server',
                 'IIS Windows',
                 'Your Azure Function App is up and running.',
                 'Welcome to CentOS',
                 'Test Page for Apache Installation',
                 'Google',
                 'Amazon S3 - Cloud Object Storage  - AWS',
                 'AT&T WiFi Portal',
                 'RouterOS router configuration page',
                 'Hotwire Communications',
                 'CMS Web Viewer',
                 '',
                 "Web Server's Default Page",
                 r'æ²¡æ\x9c\x89æ\x89¾å\x88°ç«\x99ç\x82¹']

def generate_random_ip():
    """
    Generate a random IPv4 address, skipping reserved/private/multicast addresses.
    """
    while True:
        ip = "{}.{}.{}.{}".format(
            random.randint(1, 223),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(1, 254)
        )
        octets = list(map(int, ip.split('.')))
        # Skip loopback (127.x.x.x)
        if octets[0] == 127:
            continue
        # Skip private addresses: 10.x.x.x
        if octets[0] == 10:
            continue
        # Skip private addresses: 172.16.x.x to 172.31.x.x
        if octets[0] == 172 and 16 <= octets[1] <= 31:
            continue
        # Skip private addresses: 192.168.x.x
        if octets[0] == 192 and octets[1] == 168:
            continue
        return ip

def check_website():
    """
    Generate a random IP, try to load its homepage with a 10-second timeout,
    and if responsive, extract the <title> tag. Returns (ip, title) on success.
    """
    ip = generate_random_ip()
    # ip = '142.250.200.14'
    url = f"http://{ip}"
    try:
        head = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47'}
        print('|', end='')
        response = requests.get(url, headers = head, timeout=timeout)
        if response.ok:
            match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
            title = match.group(1).strip() if match else "No Title Found"
            if title not in boring_titles:
                print(f'\n> Found: {(ip, title)}')
                return (ip, title)
    except Exception:
        return None

def check_websites(iter_count, thread_count):
    """
    Run iter_count website checks using thread_count parallel threads.
    Returns a list of (ip, title) tuples for responsive websites.
    """
    results = []
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [executor.submit(check_website) for _ in range(iter_count)]
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    return results

# -----------------------
# PART 2: Headless Browsing & Concurrent Screenshots with PySide2
# -----------------------

from PySide2.QtWidgets import QApplication
from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtCore import QTimer, QUrl, Qt

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
            QTimer.singleShot(timeout*2, self.take_screenshot)
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

# -----------------------
# MAIN: Integration
# -----------------------

def main():
    # Step 1: Check websites concurrently (using multithreading).
    iter_count = 100000    # Total random IPs to try.
    thread_count = 4096  # Number of parallel threads.
    accessible_websites = check_websites(iter_count, thread_count)
    
    if not accessible_websites:
        print("No accessible websites found.")
        sys.exit(0)
    
    print("Accessible websites found:")
    for site in accessible_websites:
        print(site)
    
    # Step 2: For each accessible website, start a headless browser to load and capture a screenshot.
    app = QApplication(sys.argv)
    pending = len(accessible_websites)
    
    def on_page_done():
        nonlocal pending
        pending -= 1
        if pending == 0:
            app.quit()
    
    pages = []  # Keep references to OffscreenScreenshot instances.
    for ip, title in accessible_websites:
        url = f"http://{ip}"
        page = OffscreenScreenshot(url, ip, title, on_page_done)
        pages.append(page)
    
    app.exec_()

if __name__ == "__main__":
    main()
