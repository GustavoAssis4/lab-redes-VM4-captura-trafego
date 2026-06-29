
# VM4 - Captura e Análise de Tráfego

## Objetivo

Implementar o módulo responsável pela captura de tráfego espelhado da infraestrutura.

---

## Interfaces utilizadas

A VM4 foi conectada à VLAN 40 (MONITOR).

Interfaces monitoradas:

- ens3
- ens7

Interfaces provenientes dos switches virtuais:

- SW1 → VLAN40_CAP.TRAF1
- SW2 → VLAN40_CAP.TRAF2

MAC VM SW1:
fa:16:3e:77:99:5e

MAC VM SW2:
fa:16:3e:69:d6:31

---

## Configuração de rede

Verificação das interfaces:

```bash
ip addr

Verificação das rotas:

ip route

Verificação de conectividade:

ping 10.10.1.2
Instalação de dependências

Atualização do sistema:

apt update
apt upgrade -y

Instalação do Python:

apt install python3 python3-pip -y

Instalação das bibliotecas:

pip install scapy requests
Resolução de problemas DNS

Durante o projeto foi necessário corrigir problemas de resolução DNS.

Arquivo:

/etc/resolv.conf

DNS utilizados:

8.8.8.8

1.1.1.1

Docker

Instalação do Docker:

apt install docker.io -y

Verificação:

docker --version
Execução
python3 flow_generator.py

ou

docker run --net=host --privileged flow-generator