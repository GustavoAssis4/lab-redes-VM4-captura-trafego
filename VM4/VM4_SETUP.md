# VM4 - Captura e Análise de Tráfego

## Objetivo

A VM4 é responsável pela captura passiva do tráfego espelhado da infraestrutura OpenStack, realizando a geração de fluxos de comunicação (Flow Generator) e enviando essas informações para a API REST hospedada na VM1.

## Topologia

A VM4 está conectada à VLAN de monitoramento (VLAN 40) e recebe o tráfego espelhado pelos switches virtuais.

**Interfaces físicas:**
- `ens3` → Switch Virtual 1
- `ens7` → Switch Virtual 2

**Subinterfaces monitoradas pelo Flow Generator:**

```
ens3.10
ens3.20
ens3.30
ens3.50
ens3.60

ens7.10
ens7.20
ens7.30
ens7.50
ens7.60
```

> A VLAN 40 (rede de monitoramento/gerência da própria infraestrutura) não é monitorada — o script `configurar-captura-vlans.sh` (Aluno 5) não cria subinterfaces para ela.

## Endereçamento e Acesso Utilizado

**VM4 conectada ao Switch Virtual 1**
- IP: `10.0.40.10/16`
- Gateway: `10.0.0.1`
- MAC Address: `fa:16:3e:77:99:5e`

**VM4 conectada ao Switch Virtual 2**
- IP: `10.0.40.20/16`
- Gateway: `10.0.0.2`
- MAC Address: `fa:16:3e:69:d6:31`

**Acesso remoto à VM:**

*Entrar via VM11*
```bash
ssh root@10.10.1.22
# Senha padrão: XXXXXX
```

*Dentro da VM11:*
```bash
ssh root@10.10.40.10
# Senha padrão: XXXXXX
```

**Acessar/Criar o diretório aluno4 :**

*Dentro da VM4:*
```bash
cd aluno4
```
*Listar arquivos:*
```bash
ls
```
## Configuração Inicial e Inspeção do Sistema

Verificar interfaces e endereços IP:
```bash
ip addr
```

Verificar tabela de rotas:
```bash
ip route
```

Testar conectividade com a infraestrutura (ex: VM1):
```bash
ping 10.10.1.2
```

Verificar a utilização do disco rígido:
```bash
df -h
```

## Configuração do Ambiente e Atualização do Sistema

**1. Atualização do Sistema Operacional**
```bash
apt update && apt upgrade -y
```

**2. Resolução de DNS (caso a VM não consiga acessar a internet)**

Editar o arquivo de configuração:
```bash
nano /etc/resolv.conf
```

Adicionar os servidores:
```
nameserver 8.8.8.8
nameserver 1.1.1.1
```

**3. Instalação do Python e Dependências Básicas**
```bash
apt install python3 python3-pip -y
```

## Acesso e Execução Local (Sem Docker)

**Acesso ao projeto**

Entrar no diretório da aplicação e verificar os arquivos existentes:
```bash
cd /root/aluno4
ls
```

**Instalação das bibliotecas Python**
```bash
pip install scapy requests
```
ou via arquivo de dependências:
```bash
pip install -r requirements.txt
```

**Execução da aplicação em modo local**
```bash
python3 flow_generator.py
```

A aplicação inicia monitorando automaticamente todas as subinterfaces configuradas.

## Docker: Construção e Gerenciamento

**1. Instalação e Verificação do Docker**
```bash
apt install docker.io -y
docker --version
```

**2. Estrutura de Arquivos para Containerização**

`requirements.txt`:
```
scapy
requests
```

`Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "flow_generator.py"]
```

**3. Construção da Imagem**
```bash
docker build -t flow-generator .
```

> **Observação:** sempre que houver alteração no arquivo `flow_generator.py`, a imagem Docker deverá ser reconstruída utilizando o comando acima.

**4. Gerenciamento e Inspeção dos Containers**

Executar o container em segundo plano (com privilégios de rede e limites de log):
```bash
docker run -d \
  --name flow-generator \
  --net=host \
  --privileged \
  --log-opt max-size=20m \
  --log-opt max-file=3 \
  flow-generator
```

Listar containers ativos:
```bash
docker ps
```

Listar todos os containers (incluindo os parados):
```bash
docker ps -a
```

Listar imagens Docker locais:
```bash
docker images
```

Entrar no terminal interativo do container em execução:
```bash
docker exec -it flow-generator bash
```

Verificar o espaço em disco utilizado pelo ecossistema Docker:
```bash
docker system df
```

**5. Monitoramento de Logs do Container**

Visualizar logs gerados:
```bash
docker logs flow-generator
```

Acompanhar logs em tempo real (stdout da aplicação):
```bash
docker logs -f flow-generator
```

Exibir as últimas 50 linhas e continuar acompanhando em tempo real:
```bash
docker logs --tail 50 -f flow-generator
```

## Funcionamento do Flow Generator

A aplicação realiza continuamente o monitoramento e o processamento de dados na infraestrutura de forma automatizada através das seguintes funcionalidades implementadas:

- **Captura Multi-protocolo:** escuta passiva de pacotes TCP, UDP e ICMP utilizando a biblioteca Scapy.
- **Identificação Automática de VLAN:** mapeamento realizado diretamente através do nome da subinterface lógica onde o pacote foi capturado.
- **Métricas Computadas:**
  - Contagem total de pacotes por fluxo.
  - Contagem acumulada de bytes.
  - Registro de timestamp do primeiro pacote (`first_seen`) e do último pacote (`last_seen`).
  - Cálculo em tempo real da duração exata do fluxo.
  - Cálculo da taxa de transmissão média (bytes por segundo).
- **Abstração L7:** identificação automática do serviço correspondente com base na porta destino.
- **Console & Persistência:** impressão de um resumo de status a cada ciclo (fluxos ativos, novos fluxos enviados, pacotes e bytes totais) e exportação sincronizada para o arquivo local `flows.json`. Atualização automática a cada 10 segundos.

## Integração com a API REST

O envio dos lotes de fluxos consolidados é feito para a API hospedada na VM1. Durante a rotina de comunicação, o sistema realiza o estabelecimento da conexão HTTP, realiza o envio do lote sob a semântica JSON e valida o recebimento do código de sucesso HTTP 200/201.

- **Endpoint de Produção:** `http://10.0.20.10/api/v1/flows/batch`
- **Método HTTP:** `POST`

**Exemplo de Formato JSON Enviado**
```json
[
    {
        "src_ip": "10.0.10.2",
        "dst_ip": "10.0.20.2",
        "src_port": 50502,
        "dst_port": 80,
        "protocol": "TCP",
        "bytes": 1024,
        "packets": 8,
        "duration_s": 0.53
    }
]
```

**Comando de Teste e Inspeção da API**

Para verificar manualmente o resumo das comunicações registradas no servidor central da VM1:
```bash
curl http://10.10.1.2/api/v1/flows/summary
```

## Estrutura do Projeto

```
VM4/
│
├── Dockerfile
├── requirements.txt
├── flow_generator.py
├── flows.json
└── README.md
```

## Observações Importantes

- **Modo Passivo:** a VM4 trabalha exclusivamente de forma passiva, apenas observando e computando métricas do tráfego espelhado.
- **Dependência de Infraestrutura:** o espelhamento de portas (Port Mirroring/SPAN) deve estar previamente ativo nos switches virtuais corporativos configurados pelo módulo de infraestrutura.
- **Mecanismo Antipoluição:** apenas fluxos com atualizações ou totalmente inéditos são enviados para a API REST da VM1, evitando duplicidade e consumo desnecessário de banda.
- **Gerenciamento de Memória (Timeout):** fluxos identificados como ociosos ou inativos por mais de 60 segundos são removidos automaticamente da memória RAM do programa para evitar crescimento indefinido das estruturas de dados.
- **Proteção de Disco:** os logs do contêiner Docker possuem limites estritos de tamanho máximo e rotação (`max-size` e `max-file`) para mitigar riscos de esgotamento de armazenamento físico da VM.


