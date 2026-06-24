# Traffic Capture and Flow Generator Service

## Plataforma Distribuída de Monitoramento e Segurança de Redes

Projeto desenvolvido para a disciplina de Laboratório de Redes.

O objetivo deste módulo é capturar tráfego de rede proveniente das VLANs monitoradas da infraestrutura virtual, realizar o processamento dos pacotes observados e gerar fluxos de comunicação contendo estatísticas relevantes para análise posterior.

A solução implementada corresponde ao **Aluno 4 (VM4 - Captura de Tráfego)** da arquitetura distribuída proposta para o trabalho.


## Visão Geral --- Flow Generator

O Flow Generator é o componente desenvolvido na VM4 responsável pela captura, processamento e geração de fluxos de rede do ambiente virtual da disciplina.

A aplicação monitora o tráfego da VLAN40, identifica protocolos de rede, agrupa pacotes em fluxos, calcula estatísticas e envia automaticamente os dados para a API central executada na VM1.

Além da integração com a VM1, os fluxos também podem ser exportados localmente em formato JSON para fins de análise e validação.

---
## Objetivos

Este módulo foi desenvolvido para:

- Capturar tráfego proveniente da VLAN40;
- Realizar parsing de pacotes IP;
- Gerar fluxos de comunicação;
- Produzir estatísticas de rede;
- Integrar-se ao servidor central (VM1);
- Disponibilizar a aplicação em container Docker.

## Tecnologias Utilizadas

| Tecnologia | Finalidade |
|------------|------------|
| Python 3.12 | Linguagem principal |
| Scapy | Captura e parsing de pacotes |
| Requests | Comunicação com API REST |
| Docker | Containerização |
| Open vSwitch | Espelhamento de tráfego |
| JSON | Exportação de fluxos |

# Arquitetura Geral

A figura abaixo apresenta a arquitetura completa da plataforma.

![Topologia da Plataforma](images/topologia.png)

A infraestrutura foi dividida em múltiplas máquinas virtuais especializadas, cada uma responsável por uma função específica dentro do sistema de monitoramento.

A comunicação entre os módulos ocorre através de VLANs dedicadas e APIs REST disponibilizadas pelo servidor central.

---

## Responsabilidades do Aluno 4

O componente desenvolvido possui as seguintes responsabilidades:

* Captura de pacotes de rede
* Parsing dos protocolos IP, TCP, UDP e ICMP
* Geração de fluxos de comunicação
* Cálculo de estatísticas por fluxo
* Exportação dos dados para JSON
* Envio automático para a API REST da VM1
* Containerização da aplicação utilizando Docker


O fluxo de funcionamento da VM4 pode ser resumido da seguinte forma:
![Fluxo de Dados](images/vm4_fluxo_dados.png)
---
## Observações de Desenvolvimento

Durante a fase de implementação foi utilizada temporariamente a interface ens8 para acesso à Internet, instalação de dependências e testes de conectividade.

A operação final do sistema ocorre através das interfaces ens3 e ens7, associadas à VLAN40.

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

A VM4 não participa ativamente da comunicação entre os hosts.

Seu papel é exclusivamente observar o tráfego replicado pelos switches virtuais através da técnica de port mirroring (SPAN), permitindo monitoramento passivo da rede sem alterar os pacotes originais.
---


## Fluxo de Funcionamento

O processamento ocorre seguindo as etapas abaixo:

```text
Captura de Pacotes
        ↓
      Scapy
        ↓
 Parsing dos Protocolos
        ↓
 Geração de Fluxos
        ↓
 Cálculo de Estatísticas
        ↓
 Exportação JSON
        ↓
 Envio para VM1
```

### Informações coletadas

Para cada fluxo são armazenados:

* Interface de captura
* IP de origem
* IP de destino
* Porta de origem
* Porta de destino
* Protocolo
* Quantidade de pacotes
* Quantidade de bytes
* Duração do fluxo
* Taxa de transferência

---

## Integração com a VM1
A VM1 atua como servidor central da plataforma.

Os fluxos gerados pela VM4 são enviados periodicamente para a API REST, onde ficam disponíveis para armazenamento, agregação e análise por outros componentes do sistema.

### Endpoint

```text
POST /api/v1/flows/
```

### Exemplo de fluxo gerado

```json
{
  "src_ip": "10.0.40.10",
  "dst_ip": "10.0.40.20",
  "src_port": 52314,
  "dst_port": 80,
  "protocol": "TCP",
  "bytes": 1820,
  "packets": 14,
  "duration_s": 1.25
}
```

---

## Estrutura do Projeto

```text
.
├── flow_generator.py
├── requirements.txt
├── Dockerfile
├── flows.json
├── README.md
├── VM4_CONFIGURATION.md
└── VM10_DEPLOY.md
```

### Arquivos principais

| Arquivo              | Descrição                   |
| -------------------- | --------------------------- |
| flow_generator.py    | Aplicação principal         |
| requirements.txt     | Dependências Python         |
| Dockerfile           | Construção da imagem Docker |
| flows.json           | Exportação dos fluxos       |
| VM4_CONFIGURATION.md | Configuração da VM4         |
| VM10_DEPLOY.md       | Guia de implantação         |

---

## Dependências

Instalação manual:

```bash
pip install -r requirements.txt
```

Dependências utilizadas:

```text
scapy
requests
```

---

## Execução Local

```bash
python3 flow_generator.py
```

---

## Docker

### Construção da imagem

```bash
docker build -t flow-generator .
```

### Execução

```bash
docker run \
  --net=host \
  --privileged \
  flow-generator
```

---


## Documentação Complementar

A documentação detalhada do projeto encontra-se distribuída nos seguintes arquivos:

* VM4_CONFIGURATION.md
* VM10_DEPLOY.md
* comandos.txt


Esses documentos descrevem o processo completo de configuração da VM4, comandos utilizados e os procedimentos necessários para reprodução do ambiente em outras máquinas.

---
