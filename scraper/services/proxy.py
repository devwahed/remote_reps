import random
file_path = 'scraper\services\proxies.txt'
with open(file_path, 'r') as file:
    proxies = file.readlines()

proxies = [proxy.strip() for proxy in proxies if proxy.strip()]

proxy_list = []
for proxy in proxies:
    proxy = proxy.split(':')
    proxy_list.append(f"http://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}")


def get_random_proxy():
    return random.choice(proxy_list)
