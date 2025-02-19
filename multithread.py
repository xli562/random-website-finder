import requests
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_random_ip():
    """Generate a random IPv4 address, skipping reserved/private/multicast addresses."""
    while True:
        # Generate an IP with first and last octets in 1-254 and others 0-255.
        ip = "{}.{}.{}.{}".format(
            random.randint(1, 254),
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
        # Skip multicast and reserved addresses (224.x.x.x and above)
        if octets[0] >= 224:
            continue
        return ip

def check_website():
    """
    Generate a random IP, try to access it, and if responsive, return a tuple (ip, title).
    """
    ip = generate_random_ip()
    # ip = '142.250.200.14'
    url = f"http://{ip}"
    try:
        head = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47'}
        print('|', end='')
        response = requests.get(url, headers = head, timeout=5)
        # Only consider HTTP 200 responses
        if response.ok:
            # Use a regex to search for the <title> tag content
            m = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
            title = m.group(1).strip() if m else "No Title Found"
            print(f'\n> Found: {(ip, title)}')
            return (ip, title)
    except Exception:
        # Any exception (including timeouts) results in no output.
        return None

def main(iter_count, thread_count):
    """
    Run iter_count iterations of website checks using thread_count parallel threads.
    Returns a list of (ip, title) tuples for responsive websites.
    """
    results = []
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        # Submit iter_count tasks to the thread pool
        futures = [executor.submit(check_website) for _ in range(iter_count)]
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    return results

if __name__ == "__main__":
    iter_count = 10000    # Total iterations (i.e. random IPs to check)
    thread_count = 1000   # Number of parallel threads
    accessible_websites = main(iter_count, thread_count)
    print("Accessible websites (ip, title):")
    for site in accessible_websites:
        print(site)
