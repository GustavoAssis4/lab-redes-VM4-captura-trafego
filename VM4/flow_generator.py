import requests
from scapy.all import sniff, IP, TCP, UDP, ICMP
from datetime import datetime
import threading
import time
import json
import os

# ==========================================
# CONFIGURAÇÕES GLOBAIS
# ==========================================
VM1_IP = "10.0.20.10"
VM1_API = f"http://{VM1_IP}/api/v1/flows/batch"
FLOW_TIMEOUT = 60  # Tempo em segundos para expirar um fluxo inativo

# Variáveis de Estado
flows = {}
sent_flows = set()
flows_changed = False
total_packets = 0
total_bytes = 0


def send_flow(batch):
    """Envia os dados dos fluxos em lote (batch) para a API."""
    try:
        response = requests.post(
            VM1_API,
            json=batch,
            timeout=5
        )
        if response.status_code in [200, 201]:
            print(f"[VM1 OK] {len(batch)} fluxos enviados.")
        else:
            print(f"[ERRO API] Status: {response.status_code}")
    except Exception as e:
        print(f"[ERRO ENVIO] {e}")


def get_service(protocol, port):
    """Retorna o nome do serviço baseado na porta."""
    if protocol == "ICMP":
        return "ICMP"
    services = {
        22: "SSH", 53: "DNS", 67: "DHCP", 68: "DHCP",
        80: "HTTP", 443: "HTTPS", 8000: "HTTP-TESTE"
    }
    return services.get(port, "DESCONHECIDO")


def process(packet):
    """Processa cada pacote capturado pelo Scapy."""
    global flows_changed, total_packets, total_bytes

    if IP not in packet:
        return

    src_ip = packet[IP].src
    dst_ip = packet[IP].dst

    # Ignora tráfego da/para a própria VM da API para evitar loop infinito
    if src_ip == VM1_IP or dst_ip == VM1_IP:
        return

    flows_changed = True
    total_packets += 1
    total_bytes += len(packet)

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

    flow_key = (interface, src_ip, dst_ip, src_port, dst_port, protocol)
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
    """Exporta os fluxos atuais para um arquivo JSON local (sobrescreve a cada ciclo)."""
    data = []
    for flow, stats in list(flows.items()):
        interface, src_ip, dst_ip, src_port, dst_port, protocol = flow
        vlan = interface.split(".")[1] if "." in interface else "N/A"
        duration = (stats["last_seen"] - stats["first_seen"]).total_seconds()
        rate = stats["bytes"] / duration if duration > 0 else 0
        service = get_service(protocol, dst_port)

        data.append({
            "interface": interface,
            "vlan": vlan,
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
    """Remove fluxos que estão ociosos além do tempo limite (TIMEOUT)."""
    now = datetime.now()
    for flow in list(flows.keys()):
        idle_time = (now - flows[flow]["last_seen"]).total_seconds()
        if idle_time > FLOW_TIMEOUT:
            flow_id = hash(flow)
            if flow_id in sent_flows:
                sent_flows.remove(flow_id)
            del flows[flow]


def print_flow_table():
    """
    Thread em background que processa, exporta e envia fluxos periodicamente.

    IMPORTANTE: aqui NÃO imprimimos mais a tabela inteira a cada ciclo.
    Isso evitava que o log do container (capturado pelo Docker em
    /var/lib/docker/containers/.../*-json.log, sem limite por padrão)
    crescesse indefinidamente e enchesse o disco.
    Agora imprimimos apenas um resumo de uma linha por ciclo.
    """
    global flows_changed

    while True:
        time.sleep(10)

        if not flows_changed:
            continue
        flows_changed = False

        remove_expired_flows()
        export_json()

        batch = []
        for flow, stats in list(flows.items()):
            src_ip, dst_ip = flow[1], flow[2]
            src_port, dst_port = flow[3], flow[4]
            protocol = flow[5]
            duration = (stats["last_seen"] - stats["first_seen"]).total_seconds()

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
                batch.append(flow_data)
                sent_flows.add(flow_id)

        if batch:
            send_flow(batch)

        # Log resumido: uma linha por ciclo, em vez da tabela inteira
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(
            f"[{timestamp}] fluxos ativos: {len(flows)} | "
            f"novos enviados: {len(batch)} | "
            f"pacotes totais: {total_packets} | "
            f"bytes totais: {total_bytes}"
        )


# ==========================================
# EXECUÇÃO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    interfaces_to_monitor = [
        "ens3.10", "ens3.20", "ens3.30", "ens3.40", "ens3.50", "ens3.60",
        "ens7.10", "ens7.20", "ens7.30", "ens7.40", "ens7.50", "ens7.60",
    ]

    print("=" * 60)
    print("Flow Generator iniciado")
    print("=" * 60)
    print("Interfaces monitoradas:")
    for iface in interfaces_to_monitor:
        print(f" - {iface}")

    # Inicia a thread de monitoramento da tabela
    table_thread = threading.Thread(target=print_flow_table, daemon=True)
    table_thread.start()

    # Inicia o sniffer
    sniff(iface=interfaces_to_monitor, prn=process, store=False)
