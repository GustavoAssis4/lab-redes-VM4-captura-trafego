# Docker

Conteinerização da aplicação **Flow Generator** (VM4), utilizada para padronizar o ambiente de execução e facilitar a reprodução do sistema em outras máquinas da infraestrutura.

## Arquivos

| Arquivo | Descrição |
|---|---|
| `Dockerfile` | Define a imagem da aplicação, a partir da base `python:3.12-slim` |
| `docker-compose.yaml` | Sobe o container com as configurações de rede e privilégios necessárias para a captura de tráfego |

## Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "flow_generator.py"]
```

A imagem base `python:3.12-slim` foi escolhida por oferecer um ambiente Python funcional com tamanho reduzido, adequado ao perfil de hardware da VM4 (1 vCPU, 1 GB de RAM).

## docker-compose.yaml

```yaml
version: "3.9"
services:
  flow-generator:
    image: gustavosalmarino/flow-generator:latest
    container_name: flow-generator
    network_mode: host
    privileged: true
    restart: unless-stopped
    volumes:
      - ./flows:/app/flows/batch
    environment:
      - PYTHONUNBUFFERED=1
```

### Configurações importantes

| Opção | Finalidade |
|---|---|
| `network_mode: host` | Permite que o container enxergue diretamente as subinterfaces VLAN criadas no sistema operacional da VM4 (`ens3.X` e `ens7.X`), inacessíveis em modo de rede isolado (bridge) |
| `privileged: true` | Permite que a biblioteca Scapy abra sockets em modo promíscuo e capture o tráfego espelhado |
| `restart: unless-stopped` | Garante que o serviço volte a subir automaticamente após reinicializações da VM |
| `volumes` | Persiste os fluxos exportados localmente em `./flows`, fora do container |
| `PYTHONUNBUFFERED=1` | Garante que os logs da aplicação apareçam em tempo real no `docker logs`, sem buffer |

> Observação: o arquivo `docker-compose.yaml` precisa ter os campos indentados sob `services` e `flow-generator` (padrão YAML de 2 espaços) para ser interpretado corretamente pelo Docker Compose.

## Build e execução

### Usando Docker diretamente

```bash
docker build -t flow-generator .

docker run -d \
  --name flow-generator \
  --net=host \
  --privileged \
  --log-opt max-size=20m \
  --log-opt max-file=3 \
  flow-generator
```

### Usando Docker Compose

```bash
docker compose up -d
```

## Monitoramento

```bash
docker ps
docker logs -f flow-generator
docker system df
```

---
Módulo Docker da VM4, Aluno 4 (Gustavo Assis Ferreira).
