import random, re, requests
from concurrent.futures import ThreadPoolExecutor, as_completed

request_timeout = 5
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
                 r'æ²¡æ\x9c\x89æ\x89¾å\x88°ç«\x99ç\x82¹',
                 'IIS7',
                 'RouterOS',
                 'Apache2 Debian Default Page: It works']

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
    url = f"http://{ip}"
    try:
        head = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47'}
        response = requests.get(url, headers = head, timeout=request_timeout)
        if response.ok:
            match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
            title = match.group(1).strip() if match else "No Title Found"
            if title not in boring_titles:
                print(f'Found: {url}, {title}')
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