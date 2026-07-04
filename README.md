# OSPF Stub Area Lab with Python-Based Verification

A GNS3 lab demonstrating OSPF configuration with a stub area over point-to-point
links, plus Python automation (Netmiko/Paramiko) to verify router status
programmatically over SSH — including access through an SSH jump host to reach
routers not directly exposed on the management network.

## Topology

![Network Topology](https://github.com/MasterHarsh-a/ospf-stub-area-lab/blob/e1be7002ad12fb5537de6e2e39a4dc5be4f0e6a6/Screenshot%202026-07-04%20171848.png)

| Router | Role | Loopback |
|---|---|---|
| R5 | Area 0 (backbone) | 1.1.1.1 |
| R6 | ABR (area 0 <-> area 1) | 2.2.2.2 |
| R7 | Area 1 (stub) | 3.3.3.3 |
| R8 | Area 1 (stub) | 4.4.4.4 |

All inter-router links use OSPF point-to-point network type
(`ip ospf network point-to-point`) instead of the default broadcast type,
since GNS3 typically emulates Ethernet segments.

## What this demonstrates

- OSPF multi-area design with an ABR and a stub area
- Point-to-point network type configuration and verification (no DR/BDR
  election - confirmed via `FULL/ -` neighbor states)
- Stub-area behavior: intra/inter-area routes still propagate fully, while
  external (Type 5) LSAs are blocked and replaced with a single default route
  from the ABR
- Building real management access into an isolated GNS3 lab: bridging via a
  Cloud node, resolving subnet mismatches between host and GNS3 VM, and
  extending OSPF to carry the management subnet so replies can route back
- Working around legacy SSH crypto (`diffie-hellman-group1-sha1`, `ssh-rsa`)
  required by older IOS images, now rejected by default in modern SSH clients
- Reaching routers that aren't directly reachable from the automation host,
  using an SSH jump host (the GNS3 VM) via Paramiko channel forwarding into
  Netmiko, instead of modifying host-level routing tables

## Repo structure

```
router-configs/       Full startup configs for R5-R8
scripts/
  interface_status_via_jump.py   Retrieves interface status for any router
                                  via SSH jump host, credentials from .env
.env.example           Template for required environment variables
```

## Running the scripts

```bash
pip install netmiko paramiko python-dotenv
cp .env.example .env      # then fill in real credentials, not committed
python scripts/interface_status_via_jump.py R6
```

## Troubleshooting log (selected highlights)

- **GNS3 NAT node has no port-forwarding support** in current versions - it's
  outbound-only. Switched to a bridged Cloud node instead.
- **Host/VM subnet mismatch**: laptop on `192.168.1.0/24`, GNS3 VM on
  `192.168.10.0/24` - resolved by placing the management interface on the
  VM's subnet and confirming L2 reachability first.
- **SSH negotiation failures** from modern OpenSSH clients against legacy IOS
  crypto - resolved with explicit KEX/host-key algorithm overrides, both on
  the CLI and in the Netmiko connection parameters.
- **One-way reachability**: routers behind the ABR could not route replies
  back to the management subnet because it had never been advertised into
  OSPF - fixed by adding `network 192.168.10.0 0.0.0.255 area 0` on the
  ABR-adjacent router. Confirmed this didn't break stub-area behavior, since
  stub only blocks external (Type 5) routes, not inter-area (Type 3) ones.
- **Reaching routers with no direct route from the automation host**: solved
  with an SSH jump host pattern (Paramiko `direct-tcpip` channel handed to
  Netmiko's `sock` parameter) rather than adding persistent static routes on
  the Windows host.

## Notes

Credentials in `router-configs/*.txt` are lab-only placeholders
(`cisco123`) and are not sensitive - this is an isolated GNS3 lab with no
real-world exposure.
