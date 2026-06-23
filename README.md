# VM4-captura-trafego
Módulo de captura de tráfego e geração de fluxos (VM4) desenvolvido para o trabalho final da disciplina de Laboratório de Redes.
# Traffic Capture and Flow Generator Service

## Plataforma Distribuída de Monitoramento e Segurança de Redes

Projeto desenvolvido para a disciplina de Laboratório de Redes.

O objetivo deste módulo é capturar tráfego de rede proveniente das VLANs monitoradas da infraestrutura virtual, realizar o processamento dos pacotes observados e gerar fluxos de comunicação contendo estatísticas relevantes para análise posterior.

A solução implementada corresponde ao **Aluno 4 (VM4 - Captura de Tráfego)** da arquitetura distribuída proposta para o trabalho.

---

# Arquitetura Geral

A figura abaixo apresenta a arquitetura completa da plataforma.

![Topologia da Plataforma](images/topologia.png)

A infraestrutura foi dividida em múltiplas máquinas virtuais especializadas, cada uma responsável por uma função específica dentro do sistema de monitoramento.

A comunicação entre os módulos ocorre através de VLANs dedicadas e APIs REST disponibilizadas pelo servidor central.

---

# Papel da VM4 na Arquitetura

A VM4 é responsável pela captura e análise do tráfego de rede.

Seu principal objetivo é observar o tráfego que circula pela infraestrutura sem interferir na comunicação original dos dispositivos monitorados.

Para isso, os switches virtuais realizam o espelhamento (SPAN/Mirror) dos pacotes observados e enviam uma cópia para a VM4.

Após a captura, os pacotes são processados localmente, convertidos em fluxos de comunicação e enviados para a VM1.

O fluxo de funcionamento da VM4 pode ser resumido da seguinte forma:

```text
Switches Virtuais
        │
        ▼
SPAN / Mirror
        │
        ▼
     VM4
(Captura Scapy)
        │
        ▼
Parsing dos Pacotes
        │
        ▼
Geração de Fluxos
        │
        ▼
Exportação JSON
        │
        ▼
API REST
        │
        ▼
     VM1
Servidor Central
```

---

# VLAN 40 – Rede de Monitoramento

A VLAN 40 foi criada especificamente para os componentes relacionados às atividades de monitoramento e observabilidade da infraestrutura.

Rede:

```text
10.0.40.0/24
```

A VM4 encontra-se conectada nesta VLAN através dos endereços:

```text
10.0.40.10/16 --- Porta do SW1
```
```text
10.0.40.20/16 --- Porta do SW2
```
A utilização de uma VLAN exclusiva para monitoramento oferece diversas vantagens:

* Isolamento do tráfego de monitoramento;
* Maior segurança da infraestrutura;
* Separação lógica dos serviços;
* Facilidade de gerenciamento;
* Redução do impacto sobre as demais VLANs.

Todo o tráfego processado pela VM4 é encaminhado exclusivamente para a VM1.

---

# Integração com os Open vSwitch

A captura de tráfego depende diretamente da configuração dos switches virtuais da infraestrutura.

Os switches utilizados são:

| Equipamento | Função                    |
| ----------- | ------------------------- |
| VM-SW1      | Switch Virtual Principal  |
| VM-SW2      | Switch Virtual Secundário |

Informações das interfaces de monitoramento:

| Interface        | MAC Address       |
| ---------------- | ----------------- |
| VLAN40_CAP.TRAF1 | fa:16:3e:77:99:5e |
| VLAN40_CAP.TRAF2 | fa:16:3e:69:d6:31 |

Os switches realizam o espelhamento do tráfego através da funcionalidade SPAN/Mirror.

Esse mecanismo cria cópias dos pacotes observados e os encaminha para a VM4, permitindo inspeção passiva sem interferir na comunicação original da rede.

---

# Funcionalidades Implementadas

## Captura de Pacotes

A captura é realizada através da biblioteca Scapy.

O sistema monitora simultaneamente múltiplas interfaces da VM:

```text
ens3
ens7
```

Em que a interface ens3 se refere a porta do SW1 e a interface ens7 se refere a porta do SW2, com isso, cada pacote recebido é analisado em tempo real.

---

## Parsing de Pacotes

Durante a captura são extraídas informações relevantes dos cabeçalhos de rede.

Campos processados:

* Endereço IP de origem
* Endereço IP de destino
* Porta de origem
* Porta de destino
* Protocolo
* Interface de captura
* Quantidade de bytes

Exemplo:

```text
192.168.10.193:44706
        │
        ▼
10.10.1.2:80
```

---

## Identificação de Protocolos

Atualmente o sistema identifica automaticamente:

| Protocolo |
| --------- |
| TCP       |
| UDP       |
| ICMP      |
| HTTP      |
---

## Identificação de Serviços

Mapeamento automático de portas conhecidas:

| Porta | Serviço    |
| ----- | ---------- |
| 22    | SSH        |
| 53    | DNS        |
| 67    | DHCP       |
| 68    | DHCP       |
| 80    | HTTP       |
| 443   | HTTPS      |
| 8000  | HTTP-TESTE |

---


### Geração de Fluxos e *Threading*

Cada comunicação é convertida em um fluxo único definido pela tupla: `(interface, src_ip, dst_ip, src_port, dst_port, protocol)`.

Para otimizar o processamento, a aplicação utiliza paralelismo com a biblioteca `threading`. Enquanto o loop principal captura pacotes ininterruptamente, uma *Thread* secundária é executada a cada **10 segundos** para realizar as seguintes tarefas em segundo plano:
1. Imprimir a tabela de fluxos no terminal.
2. Enviar novos fluxos não registrados para a API da VM1.
3. Atualizar o arquivo local de backup.
Um fluxo é definido pela seguinte tupla:

```text
(interface,
src_ip,
dst_ip,
src_port,
dst_port,
protocol)
```

Para cada fluxo são armazenadas estatísticas de utilização.

Métricas calculadas:

* Número de pacotes;
* Quantidade de bytes;
* Tempo de duração;
* Taxa de transferência;
* Horário de início;
* Horário da última atualização.

---

### Controle de Expiração (Timeout)

Para evitar o crescimento infinito da tabela de fluxos e o consequente esgotamento da memória RAM da máquina virtual, foi implementada a função `remove_expired_flows()`. Ela roda periodicamente através de uma thread secundária e calcula o tempo de inatividade de cada fluxo ativo. Se um fluxo não receber pacotes por mais de **30 segundos** (limiar definido pela constante `FLOW_TIMEOUT`), ele é limpo e removido da memória do sistema de forma segura.

```python
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
```
## Exportação JSON

Os dados são periodicamente consolidados no arquivo local `flows.json` e exportados via POST para a API do Servidor Central (`http://10.10.1.2/api/v1/flows/`).

```text
flows.json
```

Exemplo:

```json
{
  "src_ip": "192.168.10.193",
  "dst_ip": "10.10.1.2",
  "protocol": "TCP",
  "bytes": 830
}
```

---

## Integração com a VM1

Após o processamento, os fluxos são enviados automaticamente para o servidor central.

Endpoint utilizado:

```text
POST /api/v1/flows/
```

Exemplo:

```json
{
  "src_ip": "192.168.10.193",
  "dst_ip": "10.10.1.2",
  "src_port": 44706,
  "dst_port": 80,
  "protocol": "TCP",
  "bytes": 830,
  "packets": 7,
  "duration_s": 0.01
}
```

---

# Estrutura do Projeto

```text
.
├── images
│   └── topologia.png
│
├── flow_generator.py
├── requirements.txt
├── Dockerfile
├── README.md
└── flows.json
```

---

# Containerização
## Containerização (Docker)

A aplicação foi totalmente preparada para execução em containers, isolando o ambiente de execução e garantindo que todas as dependências funcionem de maneira padronizada em qualquer infraestrutura.

### Arquivos de Configuração

**1. `requirements.txt`**
Define as bibliotecas externas necessárias para a captura e processamento de pacotes (`scapy`) e para o envio de requisições HTTP para a API (`requests`).
```text
scapy
requests
```
**2. `Dockerfile`**
O container é construído utilizando uma imagem enxuta e oficial do Python (python:3.12-slim), reduzindo drasticamente o espaço em disco e otimizando a inicialização do serviço.

### Construção e Execução 
Toda vez que o arquivo flow_generator.py sofrer alguma modificação, é obrigatório reconstruir a imagem do Docker para que as atualizações sejam aplicadas no container.
Para que a biblioteca Scapy consiga realizar o sniffing e capturar os pacotes em tempo real diretamente nas interfaces de rede reais da máquina virtual (ens3 e ens7), o container precisa ser executado obrigatoriamente com privilégios administrativos (--privileged) e mapeado diretamente na pilha de rede do host (--net host).

# 1. Construir a imagem Docker local
```bash
docker build -t flow-generator .
```
# 2. Execução
```bash
docker run --net host --privileged flow-generator
```
# 3. Verificação do ambiente
Para certificar-se de que a imagem foi gerada corretamente e analisar o consumo de armazenamento das camadas no Docker, o comando foi utilizado:
```bash
docker images
```

# Tecnologias Utilizadas

* Python 3.12
* Scapy
* Requests
* Docker
* Open vSwitch
* Linux Ubuntu

---

# Testes Realizados

## Teste ICMP

```bash
ping 10.10.1.2
```

Resultado:

* Captura dos pacotes ICMP;
* Geração dos fluxos;
* Envio para VM1.

## Teste HTTP

```bash
curl http://10.10.1.2
```

Resultado:

* Identificação de conexões TCP;
* Reconhecimento do serviço HTTP;
* Exportação para a API central.

## Teste DHCP

Monitoramento passivo dos broadcasts DHCP observados nas VLANs monitoradas.

---

# Requisitos Atendidos

| Requisito                   | Status |
| --------------------------- | ------ |
| Captura de pacotes          | ✔      |
| Parsing                     | ✔      |
| Identificação de protocolos | ✔      |
| Geração de fluxos           | ✔      |
| Estatísticas                | ✔      |
| Exportação JSON             | ✔      |
| Integração VM1              | ✔      |
| Dockerização                | ✔      |
| GitHub                      | ✔      |

---















