import sys
from PySide2.QtWidgets import QApplication

from utils.render_utils import *
from utils.request_utils import *



def main():
    # Step 1: Check websites concurrently (using multithreading).
    iter_count = 5000    # Total random IPs to try.
    thread_count = 5000  # Number of parallel threads.
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
