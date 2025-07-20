# Guia do Projeto VisuHall - Sistema de Picking Híbrido

Este documento serve como a fonte central de verdade para o projeto VisuHall. Ele detalha os objetivos, a arquitetura de hardware e software, as decisões tomadas e os próximos passos.

## 1. Visão Geral do Projeto

O VisuHall é um sistema de picking híbrido projetado para otimizar o processo de separação de itens em um armazém. Ele combina uma interface visual em um tablet/celular com um sistema de guia por luzes (LEDs) instalado em cada rack do estoque.

O objetivo é guiar o operador pelo caminho mais curto possível, mostrando em qual prateleira o item está e, ao mesmo tempo, acendendo um LED no rack correspondente para uma localização rápida e inequívoca.

O projeto está dividido em duas fases principais.

---

## 2. Fase 1: Protótipo com Arduino Uno (Momento Atual)

**Objetivo:** Desenvolver e validar o software principal (backend, banco de dados, frontend) e a lógica de roteirização usando um hardware simples e já disponível.

### 2.1. Arquitetura de Hardware (Fase 1)

- **Controlador:** Arduino Uno.
- **Atuadores:** 10 LEDs discretos (5 verdes, 5 amarelos) com resistores, montados em uma protoboard para simular 5 setores.
- **Servidor:** Raspberry Pi 5, rodando o ambiente Docker.
- **Conexão:** Arduino conectado via USB ao Raspberry Pi 5 para comunicação serial.

### 2.2. Arquitetura de Software (Fase 1)

- **Containerização:** Docker e Docker Compose.
- **Serviços Docker:**
    1.  `webapp`: Backend em Python com o framework Flask. Serve a API e a lógica principal.
    2.  `db`: Banco de dados PostgreSQL para persistir ordens de picking, produtos e localizações.
    3.  `mqtt`: Broker Mosquitto (preparação para a Fase 2).
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

## 3. Fase 2: Sistema de Produção com ESP32 (Momento Futuro)

**Objetivo:** Substituir o protótipo por uma solução de hardware escalável, robusta e pronta para ser instalada nos 40 racks do armazém.

### 3.1. Arquitetura de Hardware por Rack (Fase 2)

Cada um dos 40 racks terá um módulo de controle idêntico, composto por:

- **Controlador:** ESP32 NodeMCU.
- **Atuador:** Pedaço de 15 cm de uma fita de LED endereçável WS2812B (totalizando 9 LEDs).
- **Conexão:** Wi-Fi, comunicando-se com o backend via protocolo MQTT.

### 3.2. Estratégia de Alimentação (Decisão Final)

Para evitar complexidade e garantir a estabilidade, foi decidido usar **uma única fonte de alimentação por rack**.

- **Fonte:** 1x Fonte Chaveada 5V 2A por rack.
- **Fiação:** A fonte alimentará em paralelo tanto o **ESP32** (pelo pino `Vin`) quanto a **fita de LED**. A porta USB do ESP32 será usada apenas para programação.
- **Conectores (Sem Solda):** A conexão será feita usando um **Cabo Splitter DC (1 para 2)** e **Conectores Jack P4 com Borne**, eliminando a necessidade de solda.

### 3.3. Lógica de Sinais

- **Sinal de Dados:** O sinal de dados do ESP32 (3.3V) será "traduzido" para os 5V da fita de LED usando um **Conversor de Nível Lógico**, garantindo a confiabilidade da comunicação.

---

## 4. Modelo de Dados e Endereçamento

- **Endereço Físico Completo:** O sistema usa um endereço de 4 partes para identificar a localização exata de um SKU: `Rua-Rack-Linha-Coluna` (ex: `R01-R03E-L06-C02`).
- **Gatilho do LED:** Para acionar o hardware, o sistema simplifica o endereço para `Rua-Rack` (ex: `R01-R03E`).
- **Lógica D/E:** As letras `D` (Direita) e `E` (Esquerda) são definidas a partir de um ponto de vista fixo (a mesa de separação), independentemente da direção do operador.
- **Escopo Inicial:** O desenvolvimento inicial focará nas Ruas 01 a 09, conforme o mapa fornecido.

## 5. Plano de Ação Imediato

As seguintes tarefas estão em andamento para a Fase 1:

-   [ ] **(Em Progresso)** Definir o esquema do banco de dados (tabelas para `picking_orders`, `products`, `locations`).
-   [ ] Implementar a função de roteirização `sort_picking_list` em Python.
-   [ ] Desenvolver os endpoints básicos da API Flask (ex: `/start_picking`, `/next_item`).
-   [ ] Criar a interface inicial do tablet (frontend) para exibir a lista de picking e as instruções.
-   [ ] Manter a integração com o Arduino Uno via porta serial para os testes físicos do protótipo. 