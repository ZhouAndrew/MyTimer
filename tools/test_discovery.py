import asyncio
import subprocess
import time

async def main():
    server_proc = subprocess.Popen(['python', '-m', 'tools.mock_server'])
    time.sleep(0.5)  # give the server time to start
    from tools.server_discovery import discover_server
    servers = await discover_server()
    server_proc.terminate()
    print('Servers found:', servers)

if __name__ == '__main__':
    asyncio.run(main())
