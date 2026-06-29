import requests
from scapy.all import sniff, IP, TCP, UDP, ICMP
from datetime import datetime
import threading
import time
import json

VM1_API = "http://10.10.1.2/api/v1/flows/"

flows = {}
sent_flows = set()

FLOW_TIMEOUT = 60  # segundos

total_packets = 0
total_bytes = 0


def send_flow(flow_data):
    try:
        response = requests.post(
            VM1_API,
            json=flow_data,
            timeout=5
        )

        if response.status_code in [200, 201]:
            print(
                f"[VM1 OK] "
                f"{flow_data['src_ip']}:{flow_data['src_port']} "
                f"-> "
                f"{flow_data['dst_ip']}:{flow_data['dst_port']}"
            )
        else:
            print(f"[ERRO API] {response.status_code}")

    except Exception as e:
        print(f"[ERRO ENVIO] {e}")


def get_service(protocol, port):
    if protocol == "ICMP":
        return "ICMP"

    services = {
        22: "SSH",
        53: "DNS",
        67: "DHCP",
        68: "DHCP",
        80: "HTTP",
        443: "HTTPS",
        8000: "HTTP-TESTE"
    }

    return services.get(port, "DESCONHECIDO")


def process(packet):
    global total_packets
    global total_bytes

    if IP not in packet:
        return

    total_packets += 1
    total_bytes += len(packet)

    src_ip = packet[IP].src
    dst_ip = packet[IP].dst

    protocol = "OTHER"
    src_port = 0
    dst_port = 0

    if TCP in packet:
        protocol = "TCP"
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport

    elif UDP in packet:
        protocol = "UDP"
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport

    elif ICMP in packet:
        protocol = "ICMP"

    interface = packet.sniffed_on

    flow_key = (
        interface,
        src_ip,
        dst_ip,
        src_port,
        dst_port,
        protocol
    )

    now = datetime.now()

    if flow_key not in flows:
        flows[flow_key] = {
            "packets": 0,
            "bytes": 0,
            "first_seen": now,
            "last_seen": now
        }

    flows[flow_key]["packets"] += 1
    flows[flow_key]["bytes"] += len(packet)
    flows[flow_key]["last_seen"] = now


def export_json():
    data = []

    for flow, stats in flows.items():
        interface, src_ip, dst_ip, src_port, dst_port, protocol = flow

        duration = (
            stats["last_seen"] -
            stats["first_seen"]
        ).total_seconds()

        rate = stats["bytes"] / duration if duration > 0 else 0

        service = get_service(protocol, dst_port)

        data.append({
            "interface": interface,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "protocol": protocol,
            "service": service,
            "packets": stats["packets"],
            "bytes": stats["bytes"],
            "duration": round(duration, 2),
            "bytes_per_second": round(rate, 2),
            "first_seen": stats["first_seen"].strftime("%Y-%m-%d %H:%M:%S"),
            "last_seen": stats["last_seen"].strftime("%Y-%m-%d %H:%M:%S")
        })

    with open("flows.json", "w") as f:
        json.dump(data, f, indent=4)


def remove_expired_flows():
    now = datetime.now()

    for flow in list(flows.keys()):
        idle_time = (
            now -
            flows[flow]["last_seen"]
        ).total_seconds()

        if idle_time > FLOW_TIMEOUT:
            print(f"[TIMEOUT] Removendo fluxo {flow}")

            flow_id = hash(flow)

            if flow_id in sent_flows:
                sent_flows.remove(flow_id)

            del flows[flow]


def print_flow_table():
    while True:
        time.sleep(10)

        remove_expired_flows()
        export_json()

        print("\n")
        print("=" * 90)
        print("FLOW TABLE")
        print("=" * 90)

        if len(flows) == 0:
            print("Nenhum fluxo capturado.")
            continue

        for flow, stats in list(flows.items()):
            (
                interface,
                src_ip,
                dst_ip,
                src_port,
                dst_port,
                protocol
            ) = flow

            duration = (
                stats["last_seen"] -
                stats["first_seen"]
            ).total_seconds()

            rate = stats["bytes"] / duration if duration > 0 else 0

            service = get_service(protocol, dst_port)

            flow_id = hash(flow)

            if flow_id not in sent_flows:

                flow_data = {
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "protocol": protocol,
                    "bytes": stats["bytes"],
                    "packets": stats["packets"],
                    "duration_s": round(duration, 2)
                }

                send_flow(flow_data)
                sent_flows.add(flow_id)

            print(f"INTERFACE : {interface}")
            print(f"PROTOCOLO : {protocol}")
            print(f"SERVICO   : {service}")
            print(f"FLOW ID   : {flow_id}")
            print(f"ORIGEM    : {src_ip}:{src_port}")
            print(f"DESTINO   : {dst_ip}:{dst_port}")
            print(f"PACOTES   : {stats['packets']}")
            print(f"BYTES     : {stats['bytes']}")
            print(f"DURACAO   : {duration:.2f}s")
            print(f"BYTES/S   : {rate:.2f}")

            print(
                f"INICIO    : "
                f"{stats['first_seen'].strftime('%H:%M:%S')}"
            )

            print(
                f"ULTIMO    : "
                f"{stats['last_seen'].strftime('%H:%M:%S')}"
            )

            print("-" * 90)

        print("\nRESUMO GERAL")
        print("-" * 90)
        print(f"PACOTES TOTAIS : {total_packets}")
        print(f"BYTES TOTAIS   : {total_bytes}")
        print("=" * 90)


threading.Thread(
    target=print_flow_table,
    daemon=True
).start()

print("Flow Generator iniciado...")
print("Monitorando interfaces ens3 e ens7 ...")

sniff(
    iface=["ens3", "ens7"],
    prn=process,
    store=False
)