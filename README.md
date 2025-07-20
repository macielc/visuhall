# VisuHall - Sistema de Picking Guiado por Luz

VisuHall é um sistema de picking híbrido desenvolvido para otimizar e guiar operações de separação de pedidos em armazéns. Ele combina um backend robusto para processamento de listas de picking, um frontend para operadores e um sistema de controle de LEDs baseado em microcontroladores (Arduino/ESP32) para indicar visualmente os locais de coleta.

## ✨ Funcionalidades Principais

- **Processamento de PDF:** Extrai automaticamente listas de itens de arquivos PDF de picking, convertendo-os em ordens de serviço digitais.
- **Roteirização Otimizada:** Implementa um algoritmo de "serpente" para calcular a rota de coleta mais eficiente dentro do armazém, minimizando o deslocamento do operador.
- **Guia Visual por LED:** Controla LEDs (verdes para o local ativo, amarelos para os próximos locais) para guiar o operador de forma intuitiva e rápida.
- **Interface de Operador:** Um frontend simples e claro, acessível por tablet, que exibe as instruções de picking e permite a confirmação ou o pulo de itens.
- **Arquitetura Containerizada:** Utiliza Docker e Docker Compose para criar um ambiente de desenvolvimento e produção consistente e de fácil implantação.

## 🛠️ Tecnologias Utilizadas

- **Backend:** Flask (Python)
- **Banco de Dados:** PostgreSQL
- **Comunicação com Hardware:** PySerial
- **Microcontrolador (Protótipo):** Arduino Uno
- **Frontend:** HTML, CSS, JavaScript (Vanilla)
- **Containerização:** Docker, Docker Compose
- **Processamento de PDF:** PyMuPDF

## 🚀 Como Executar o Projeto

O projeto é totalmente containerizado, o que simplifica a configuração.

### Pré-requisitos
- Docker
- Docker Compose (geralmente incluído no Docker Desktop ou via plugin)

### Passos para a Instalação

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/macielc/visuhall.git
    cd visuhall
    ```

2.  **Configure as Variáveis de Ambiente:**
    - Renomeie o arquivo `db.env.example` para `db.env` (se houver um example, caso contrário, crie o `db.env`).
    - Preencha as variáveis de ambiente no arquivo `db.env` com as credenciais desejadas para o banco de dados.

3.  **Conecte o Arduino:**
    - Conecte o Arduino Uno à máquina host.
    - Garanta que o dispositivo serial (ex: `/dev/ttyUSB0` no Linux) esteja corretamente mapeado no arquivo `docker-compose.yml`.

4.  **Inicie os Contêineres:**
    Execute o seguinte comando na raiz do projeto para construir as imagens e iniciar os serviços em segundo plano:
    ```bash
    docker compose up --build -d
    ```

5.  **Acesse a Aplicação:**
    - A interface para seleção de ordens estará disponível em: `http://<seu-ip-local>:8000/`
    - A interface de picking estará em: `http://<seu-ip-local>:8000/picking?order_id=<ID_DA_ORDEM>`

## 📁 Estrutura do Projeto

```
.
├── frontend/         # Arquivos da interface do operador (HTML, JS)
├── poc_arduino/      # Código do protótipo para o Arduino
├── app.py            # Aplicação principal Flask (API)
├── models.py         # Modelos de dados do SQLAlchemy
├── routing.py        # Lógica de otimização de rota
├── seed_db.py        # Script para popular o banco de dados com dados de teste
├── Dockerfile        # Define a imagem do container da aplicação web
├── docker-compose.yml # Orquestra os serviços (webapp, db, mqtt)
├── requirements.txt  # Dependências Python
└── README.md         # Este arquivo
``` 