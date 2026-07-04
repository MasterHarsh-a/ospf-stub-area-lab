"""
interface_status_via_jump.py

Connects to routers in the OSPF stub-area lab through an SSH jump host
(the GNS3 VM), and retrieves interface status.

Credentials are read from environment variables (or a local .env file,
untracked by git) instead of being hardcoded - see .env.example.

Requires: pip install paramiko netmiko python-dotenv
"""

import os
import sys
import paramiko
from netmiko import ConnectHandler
from dotenv import load_dotenv

load_dotenv()  # loads variables from a local .env file if present

JUMP_HOST = os.environ["JUMP_HOST"]
JUMP_USER = os.environ["JUMP_USER"]
JUMP_PASS = os.environ["JUMP_PASS"]

ROUTER_USER = os.environ["ROUTER_USER"]
ROUTER_PASS = os.environ["ROUTER_PASS"]
ROUTER_SECRET = os.environ["ROUTER_SECRET"]

# Topology addressing only - no secrets here, safe to commit
ROUTERS = {
    "R5": {"host": "192.168.10.150"},
    "R6": {"host": "10.0.12.2"},
    "R7": {"host": "10.0.23.2"},
    "R8": {"host": "10.0.34.2"},
}


def check_interface_status(router_name):
    if router_name not in ROUTERS:
        print(f"Unknown router: {router_name}")
        print(f"Available: {', '.join(ROUTERS.keys())}")
        return

    target = ROUTERS[router_name]

    jump_client = paramiko.SSHClient()
    jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jump_client.connect(JUMP_HOST, username=JUMP_USER, password=JUMP_PASS)

    jump_transport = jump_client.get_transport()
    dest_addr = (target["host"], 22)
    local_addr = (JUMP_HOST, 22)
    channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr)

    device = {
        "device_type": "cisco_ios",
        "host": target["host"],
        "username": ROUTER_USER,
        "password": ROUTER_PASS,
        "secret": ROUTER_SECRET,
        "sock": channel,
        "disabled_algorithms": {"kex": [], "pubkeys": []},
    }

    conn = ConnectHandler(**device)
    print(f"SSH connection to {router_name} (via {JUMP_HOST}) successful\n")

    output = conn.send_command("show ip interface brief")
    print(output)

    conn.disconnect()
    jump_client.close()


if __name__ == "__main__":
    router_name = sys.argv[1] if len(sys.argv) > 1 else input(
        f"Which router? ({', '.join(ROUTERS.keys())}): "
    )
    check_interface_status(router_name)
