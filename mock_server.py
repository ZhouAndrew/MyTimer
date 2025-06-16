import socket

BROADCAST_PORT = 9999
DISCOVERY_MESSAGE = b'DISCOVER_SERVER'
RESPONSE_MESSAGE = b'SERVER_HERE'


def run_mock_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', BROADCAST_PORT))
        print('Mock server started. Waiting for discovery messages...')
        data, addr = sock.recvfrom(1024)
        if data == DISCOVERY_MESSAGE:
            sock.sendto(RESPONSE_MESSAGE, addr)
            print(f'Responded to discovery from {addr}')

if __name__ == '__main__':
    run_mock_server()
