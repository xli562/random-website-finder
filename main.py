import requests
import random
import re
import multiprocessing

def generate_random_ip():
    """Generate a random IPv4 address, skipping reserved/private/multicast addresses."""
    while True:
        # Generate an IP: first and last octets in 1-254, the middle ones in 0-255.
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
        # Skip multicast/reserved addresses (224.x.x.x and above)
        if octets[0] >= 224:
            continue
        return ip

def check_website():
    """
    Generate a random IP, attempt an HTTP GET request with a 10-second timeout,
    and if successful, extract and return the website's title as a tuple (ip, title).
    """
    ip = generate_random_ip()
    # ip = '142.250.200.14'
    url = f"http://{ip}"
    try:
        head = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47'}
        print(f'trying {url} ...')
        response = requests.get(url, headers = head, timeout=10)
        if response.ok:
            # Extract the content inside the <title> tag
            match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
            title = match.group(1).strip() if match else "No Title Found"
            print(f'> Found: {(ip, title)}')
            return (ip, title)
    except Exception:
        return None

def run_check(_):
    """Wrapper for check_website to work with multiprocessing's map."""
    return check_website()

def main(iter_count, process_count):
    """
    Run iter_count iterations of website checks using process_count parallel processes.
    Returns a list of (ip, title) tuples for responsive websites.
    """
    with multiprocessing.Pool(processes=process_count) as pool:
        # Use pool.map with a dummy iterable since run_check doesn't require an input.
        results = pool.map(run_check, range(iter_count))
    # Filter out unsuccessful (None) results.
    return [result for result in results if result is not None]

if __name__ == "__main__":
    iter_count = 500    # Total iterations (i.e., number of random IPs to check)
    process_count = 50  # Number of parallel processes
    accessible_websites = main(iter_count, process_count)
    
    print("Accessible websites (ip, title):")
    for site in accessible_websites:
        print(site)
