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
    image: salmarino/flow-generator:latest
    container_name: flow-generator
    network_mode: host
    privileged: true
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
    logging:
      driver: json-file
      options:
        max-size: "20m"
        max-file: "3"
```

### Configurações importantes

| Opção | Finalidade |
|---|---|
| `image` | Aponta para a imagem publicada no Docker Hub (`salmarino/flow-generator`), permitindo que outras máquinas subam o container sem precisar clonar o código-fonte nem buildar localmente |
| `network_mode: host` | Permite que o container enxergue diretamente as subinterfaces VLAN criadas no sistema operacional da VM4 (`ens3.X` e `ens7.X`), inacessíveis em modo de rede isolado (bridge) |
| `privileged: true` | Permite que a biblioteca Scapy abra sockets em modo promíscuo e capture o tráfego espelhado |
| `restart: unless-stopped` | Garante que o serviço volte a subir automaticamente após reinicializações da VM |
| `logging` (`max-size`/`max-file`) | Limita o log do container a no máximo 60 MB (3 arquivos de 20 MB), evitando esgotamento de disco em execuções prolongadas |
| `PYTHONUNBUFFERED=1` | Garante que os logs da aplicação apareçam em tempo real no `docker logs`, sem buffer |

> Observação: o arquivo `docker-compose.yaml` precisa ter os campos indentados sob `services` e `flow-generator` (padrão YAML de 2 espaços) para ser interpretado corretamente pelo Docker Compose.

> Observação: o `flows.json` gerado pela aplicação é interno ao container e não é persistido no host — o dado que realmente importa (os fluxos consolidados) já é enviado para a VM1 via API a cada ciclo.

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

Como o `docker-compose.yaml` não possui uma seção `build:`, ele não builda a imagem localmente — ele apenas baixa (`pull`) a imagem já publicada no Docker Hub. Por isso, antes que qualquer outra máquina (como a do Aluno 10) consiga subir o serviço com `docker compose up -d`, a imagem precisa ter sido publicada previamente, conforme a seção a seguir.

## Publicação da imagem no Docker Hub

Necessária sempre que o serviço for executado em uma máquina diferente daquela onde a imagem foi construída — por exemplo, para permitir que o Aluno 10 rode a VM4 em seu próprio ambiente.

```bash
docker login
docker build -t salmarino/flow-generator:latest .
docker push salmarino/flow-generator:latest
```

O repositório precisa estar configurado como **público** no Docker Hub (Settings → Visibility), caso contrário a máquina de destino precisará das credenciais de login para realizar o `pull` da imagem.

> Importante: a imagem publicada contém apenas a aplicação. As subinterfaces VLAN (`ens3.10`, `ens3.20`, `ens3.30`, `ens3.50`, `ens3.60` e as equivalentes em `ens7`) precisam já existir no sistema operacional da máquina de destino — criadas pelo script `configurar-captura-vlans.sh` (Aluno 5) — antes de subir o container, já que ele depende de `network_mode: host` para acessá-las.

## Monitoramento

```bash
docker ps
docker logs -f flow-generator
docker system df
```

---
Módulo Docker da VM4, Aluno 4 (Gustavo Assis Ferreira).
