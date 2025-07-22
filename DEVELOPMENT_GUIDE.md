# Guia do Projeto VisuHall - Sistema de Picking Híbrido

Este documento serve como a fonte central de verdade para o projeto VisuHall. Ele detalha os objetivos, a arquitetura de hardware e software, as decisões tomadas e os próximos passos.

## 1. Visão Geral do Projeto

O VisuHall é um sistema de picking híbrido projetado para otimizar o processo de separação de itens em um armazém. Ele combina uma interface visual em um tablet/celular com um sistema de guia por luzes (LEDs) instalado em cada rack do estoque.

O objetivo é guiar o operador pelo caminho mais curto possível, mostrando em qual prateleira o item está e, ao mesmo tempo, acendendo um LED no rack correspondente para uma localização rápida e inequívoca.

O projeto está dividido em duas fases principais.

---

## 2. Fase 1: Protótipo Funcional com 2 ESPs via MQTT (Concluído)

**Objetivo:** Desenvolver e validar o software principal (backend, banco de dados, frontend) e a lógica de roteirização usando um ambiente de prototipagem com dois microcontroladores ESP32, simulando duas ruas do armazém.

**Status:** Concluído.

### 2.1. Arquitetura de Hardware (Fase 1)

- **Controladores:** 2x ESP32 NodeMCU.
- **Atuadores:** Fitas de LED endereçáveis (WS2812B) conectadas a cada ESP32.
- **Servidor:** Raspberry Pi 5, rodando o ambiente Docker.
- **Comunicação:** Os ESP32 se conectam à rede Wi-Fi e se comunicam com o backend via protocolo MQTT, publicando seu status e recebendo comandos.

### 2.2. Arquitetura de Software (Fase 1)

- **Containerização:** Docker e Docker Compose.
- **Serviços Docker:**
    1.  `webapp`: Backend em Python com o framework Flask. Serve a API, a lógica principal e atua como cliente MQTT.
    2.  `db`: Banco de dados PostgreSQL para persistir ordens de picking, produtos e localizações.
    3.  `mqtt`: Broker Mosquitto para mediar a comunicação entre o backend e os ESP32.
- **Frontend:** Uma aplicação web simples, acessível por um tablet ou celular, para guiar o operador.

### 2.3. Lógica de Roteirização ("Serpente Otimizada")

A lógica principal do sistema é ordenar a lista de picking para criar o caminho mais eficiente. A ordenação segue a seguinte hierarquia:

1.  **Ordenar por `Rua`:** Em ordem crescente (01, 02, 03...).
2.  **Ordenar por `Rack` (Fluxo Serpente):**
    - Para **Ruas ÍMPARES** (01, 03, 05...): Ordenar Racks em ordem **crescente** (R01, R02, R03...).
    - Para **Ruas PARES** (02, 04, 06...): Ordenar Racks em ordem **decrescente** (R03, R02, R01...).
3.  **Ordenar por `Linha`:** Ordem crescente.
4.  **Ordenar por `Coluna`:** Ordem crescente.

O sistema ignora automaticamente as ruas onde não há itens a serem coletados.

---

## 3. Próximos Passos e Escalabilidade

Com a validação bem-sucedida da arquitetura com 2 ESPs, o projeto está pronto para ser escalado. A lógica atual foi projetada para ser expandida com alterações mínimas.

### 3.1. Fase 2: Expansão para 12 ESPs

**Objetivo:** Aumentar a cobertura do sistema para 12 ruas/setores, validando a robustez da comunicação MQTT e do backend com um número maior de dispositivos concorrentes.

**Plano de Ação:**

1.  **Hardware:** Preparar e instalar os 10 novos módulos de ESP32 e fitas de LED nos locais designados.
2.  **Firmware:** Carregar o firmware existente nos novos ESP32, garantindo que o `DEVICE_ID` em cada um seja configurado corretamente para corresponder à sua rua/setor físico (ex: `3`, `4`, ..., `12`).
3.  **Backend (Lógica de Mapeamento):** A principal alteração será no mapeamento `id_rua -> topico_mqtt`. A lógica atual já é dinâmica. O sistema `on_connect` do MQTT permite que cada novo ESP anuncie sua presença. A aplicação precisa garantir que o dicionário `device_online_status` consiga gerenciar todos os 12 dispositivos. A lógica de envio de comandos `send_light_command` já itera sobre uma lista de comandos, tornando-a inerentemente escalável. Não são esperadas grandes modificações no código principal.
4.  **Testes:** Realizar testes de carga simulando múltiplos pedidos que demandem a ativação de várias luzes simultaneamente para garantir que o broker e o backend lidem com o tráfego.

### 3.2. Fase 3: Sistema de Produção Completo

**Objetivo:** Substituir o protótipo por uma solução de hardware escalável, robusta e pronta para ser instalada em todos os racks necessários do armazém.

**Plano de Ação:**

1.  **Mapeamento de Endereços:** O modelo de dados (`Rua-Rack-Linha-Coluna`) já está preparado. A expansão exigirá o cadastro de todas as localizações válidas no banco de dados.
2.  **Tópicos MQTT:** A estrutura de tópicos `visuhall/rua/{id_rua}/commands` é perfeitamente escalável. Para dezenas ou centenas de dispositivos, ela se mantém organizada e eficiente.
3.  **Infraestrutura:** A infraestrutura de rede Wi-Fi do armazém deve ser avaliada para garantir a cobertura e a capacidade de suportar dezenas de dispositivos IoT conectados simultaneamente.
4.  **Fonte de Alimentação:** Implementar a estratégia de alimentação decidida: **uma fonte de 5V 2A por rack**, alimentando tanto o ESP32 quanto a fita de LED, usando conectores P4 e splitters para uma instalação sem solda.

A lógica de software atual, baseada em eventos MQTT e um dicionário de status de dispositivos, está fundamentalmente pronta para a expansão. O trabalho principal será na instalação do hardware e na configuração dos IDs de cada novo dispositivo.

---

## 4. Fluxo de Entrada de Pedidos (Processamento de PDF)

A entrada de novas ordens de picking no sistema é automatizada através de um script de monitoramento que opera fora do ambiente Docker principal.

-   **Componente:** `visuhall_watcher.py` (script Python).
-   **Localização:** Executado diretamente na máquina Windows do gestor.
-   **Diretório Monitorado:** `C:\Users\AltF4\Documents\visuhall\PDFs`.
-   **Funcionamento:**
    1.  O script `visuhall_watcher.py` monitora o diretório especificado em tempo real.
    2.  Quando um novo arquivo PDF de picking é salvo neste diretório, o script o detecta imediatamente.
    3.  Ele utiliza uma biblioteca (como `PyMuPDF`) para extrair os dados relevantes do PDF (SKU, quantidade, localização).
    4.  Após a extração, o script envia esses dados, formatados como uma nova ordem de coleta, para a API do servidor VisuHall (rodando no Raspberry Pi) através de uma requisição HTTP.
    5.  A API do servidor então insere os dados no banco de dados PostgreSQL, e a ordem de picking fica disponível para ser iniciada por um operador.

Este mecanismo desacoplado permite que a criação de ordens seja feita de forma contínua, simplesmente arrastando e soltando arquivos em uma pasta, sem a necessidade de uma interface de upload manual. O script `seed_db.py` serve apenas para fins de teste e desenvolvimento, para popular o banco de dados sem depender do fluxo de PDFs.

---

## 5. Modelo de Dados e Endereçamento

- **Endereço Físico Completo:** O sistema usa um endereço de 4 partes para identificar a localização exata de um SKU: `Rua-Rack-Linha-Coluna` (ex: `R01-R03E-L06-C02`).
- **Gatilho do LED:** Para acionar o hardware, o sistema simplifica o endereço para `Rua-Rack` (ex: `R01-R03E`).
- **Lógica D/E:** As letras `D` (Direita) e `E` (Esquerda) são definidas a partir de um ponto de vista fixo (a mesa de separação), independentemente da direção do operador.
- **Escopo Inicial:** O desenvolvimento inicial focará nas Ruas 01 a 09, conforme o mapa fornecido.

## 6. Plano de Ação Imediato (Histórico)

As seguintes tarefas foram concluídas na Fase 1:

-   [x] **(Concluído)** Definir o esquema do banco de dados (tabelas para `picking_orders`, `products`, `locations`).
-   [x] **(Concluído)** Implementar a função de roteirização `sort_picking_list` em Python.
-   [x] **(Concluído)** Desenvolver os endpoints básicos da API Flask (ex: `/start_picking`, `/next_item`).
-   [x] **(Concluído)** Criar a interface inicial do tablet (frontend) para exibir a lista de picking e as instruções.
-   [x] **(Concluído)** Substituir a comunicação serial com Arduino por uma arquitetura MQTT com ESP32.
-   [x] **(Concluído)** Implementar reconexão automática e gerenciamento de estado para o cliente MQTT no backend.
-   [x] **(Concluído)** Validar o fluxo ponta-a-ponta com 2 ESPs. 