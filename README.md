# VM4 — Captura de Tráfego e Geração de Fluxos

**Módulo de captura passiva de tráfego e geração de fluxos de rede da Plataforma Distribuída de Gerenciamento, Monitoramento, Observabilidade e Segurança de Redes, Laboratório de Redes, IFES Campus Guarapari.**

Implementado com **Python + Scapy + Docker**, com escuta em subinterfaces VLAN via port mirroring (SPAN) e envio periódico dos fluxos para a API REST da VM1.

## Estrutura do repositório

```
VM4-Flow-Generator/
├── VM4/                   # Aplicação Flow Generator e configuração da VM4
├── Docker/                # Dockerfile e docker-compose
├── images/                # Imagens utilizadas na documentação
└── README.md
```

| Item | Descrição |
|---|---|
| Captura | Interfaces `ens3.X` e `ens7.X` (VLANs 10, 20, 30, 50, 60) |
| Processamento | Agrupamento de pacotes em fluxos bidirecionais, com controle por threads |
| Exportação local | `flows.json` |
| Destino | API REST da VM1 (`POST /api/v1/flows/batch`) |

## Tecnologias

| Tecnologia | Finalidade |
|---|---|
| Python 3.12 | Linguagem principal |
| Scapy | Captura e parsing de pacotes |
| Requests | Comunicação com a API REST |
| Threading | Captura e gerenciamento executados de forma concorrente |
| Docker | Containerização da aplicação |
| Open vSwitch | Espelhamento de tráfego (SPAN/mirror) |


## Documentação

| Arquivo | Descrição |
|---|---|
| [VM4/VM4_SETUP.md](VM4/VM4_SETUP.md) | Configuração da VM4 |
| [Docker/README.md](Docker/README.md) | Build e execução do container |
| [Docs/relatorio.pdf](Docs/relatorio.pdf) | Relatório técnico individual |

---
Trabalho desenvolvido por Gustavo Assis Ferreira, Aluno 4.
