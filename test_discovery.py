import asyncio
import subprocess
import time

async def main():
    server_proc = subprocess.Popen(['python', 'mock_server.py'])
    time.sleep(0.5)  # give the server time to start
    from server_discovery import discover_server
    servers = await discover_server()
    server_proc.terminate()
    print('Servers found:', servers)

if __name__ == '__main__':
    asyncio.run(main())
