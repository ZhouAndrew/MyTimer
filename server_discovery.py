import asyncio
import socket

BROADCAST_PORT = 9999
BROADCAST_ADDR = '255.255.255.255'
DISCOVERY_MESSAGE = b'DISCOVER_SERVER'
RESPONSE_MESSAGE = b'SERVER_HERE'
TIMEOUT = 3

async def discover_server(timeout=TIMEOUT):
    loop = asyncio.get_running_loop()
    found = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        try:
            sock.sendto(DISCOVERY_MESSAGE, (BROADCAST_ADDR, BROADCAST_PORT))
        except OSError:
            # Fallback to localhost broadcast when network is restricted
            sock.sendto(DISCOVERY_MESSAGE, ('127.0.0.1', BROADCAST_PORT))
        start = loop.time()
        while True:
            remain = timeout - (loop.time() - start)
            if remain <= 0:
                break
            try:
                data, addr = sock.recvfrom(1024)
            except socket.timeout:
                break
            if data.startswith(RESPONSE_MESSAGE):
                found.append(addr[0])
    return found

async def main():
    servers = await discover_server()
    if servers:
        print('Found servers:')
        for ip in servers:
            print(f'  - {ip}')
    else:
        print('No server found')

if __name__ == '__main__':
    asyncio.run(main())
