# VisuHall - Sistema de Picking Híbrido de Mapa Interativo com Guia de Corredor por Luz

## 1. Sumário Executivo

O **VisuHall** é um sistema de otimização de logística para separação de pedidos (picking) em estoques. Ele ataca diretamente as maiores fontes de ineficiência do processo manual: o tempo gasto na navegação entre os locais dos produtos e a alta taxa de erros na coleta.

A solução é um sistema **híbrido** inovador que combina uma **interface de mapa interativo** em um dispositivo móvel (tablet/smartphone) com um **sistema de guia visual por luzes** instalado nos **setores de picking** (cada lado de uma estante). Essa abordagem une a precisão de um sistema de software com a eficiência cognitiva de um guia visual físico, resultando em uma solução de baixo custo, alta eficiência e rápida implementação.

---

## 2. O Problema

Em um estoque com centenas ou milhares de posições de produtos, o processo de picking manual enfrenta desafios significativos:

*   **Tempo de Navegação Elevado:** O separador gasta a maior parte do seu tempo caminhando e procurando o próximo item da lista.
*   **Alta Taxa de Erros:** A coleta de um item errado ou da quantidade errada gera custos com devoluções e retrabalho.
*   **Longa Curva de Aprendizagem:** Novos funcionários levam semanas para memorizar o layout do estoque e se tornarem eficientes.
*   **Falta de Otimização:** As listas de picking em papel raramente são ordenadas de forma a criar a rota mais curta, resultando em caminhadas desnecessárias.
*   **Baixa Rastreabilidade:** É difícil medir a produtividade e identificar gargalos no processo manual.

---

## 3. A Solução Proposta: Arquitetura Híbrida

O VisuHall opera com duas camadas de orientação para guiar o separador de forma rápida e precisa. A área de picking (PCK) será dividida em setores, onde cada lado de uma estante é considerado um setor individual (ex: 20 estantes PCK = 40 setores). As estantes de armazenagem (ARM) não serão instrumentadas nesta fase.

#### Camada 1: Orientação MACRO (Guia de Setor por Luz)

*   **Conceito:** Um sinaleiro luminoso industrial é instalado na extremidade de cada **setor de picking**.
*   **Função:** Quando um pedido é iniciado, as luzes de **todos os setores** que contêm itens para aquele pedido se acendem em uma cor de "espera" (ex: **amarelo**). A luz do **primeiro setor** na rota otimizada se acende em uma cor "ativa" (ex: **verde**). O separador navega com a cabeça erguida, sabendo exatamente para qual corredor e **para qual lado do corredor** deve se dirigir. Quando todos os itens de um setor são coletados, sua luz se apaga e a luz do próximo setor na rota se torna verde.

#### Camada 2: Orientação MICRO (Mapa Interativo e Visão da Prateleira)

*   **Conceito:** O separador utiliza um aplicativo em um tablet ou smartphone.
*   **Função:** Dentro do setor "ativo", o aplicativo assume o controle. Ele mostra:
    1.  **Mapa do Setor:** Exibe a localização exata do item naquela face da estante.
    2.  **Visão da Prateleira:** Ao chegar no local, o app mostra uma representação gráfica da estante, destacando a posição exata do produto.
    3.  **Confirmação por Scan (Método Padrão):** O app exibe a foto e o nome do produto e ativa a câmera do dispositivo. A coleta só é confirmada após o escaneamento bem-sucedido do código de barras do produto, garantindo 100% de precisão e eliminando erros de coleta.

---

## 4. Componentes do Sistema

O sistema é composto por três elementos principais que se comunicam via Wi-Fi.

#### 4.1. Servidor Central (Hub)

*   **Hardware:** Raspberry Pi 5.
*   **Software:**
    *   **Backend:** Aplicação em Python (usando Flask ou FastAPI) para gerenciar a lógica.
    *   **Banco de Dados:** SQLite ou um arquivo JSON para o mapeamento `SKU -> Localização (Setor, Nível, Posição) -> Coordenadas (x,y)`.
    *   **Algoritmo de Rota:** Biblioteca de otimização (ex: Google OR-Tools) para calcular a rota mais curta.
    *   **Broker de Comunicação:** Protocolo MQTT para comunicação em tempo real com os dispositivos IoT (ESP32).

#### 4.2. Controladores de Setor (Spokes)

*   **Hardware:**
    *   Uma placa microcontroladora **ESP32** por setor de picking.
    *   Um sinaleiro de LED industrial ou lâmpada inteligente por setor.
    *   Fonte de alimentação local para a luz.
*   **Firmware:** Um código simples em C++/Arduino que conecta o ESP32 ao Wi-Fi, se inscreve no tópico MQTT do seu setor específico (ex: `visuhall/pck/setor_1A/luz`) e aguarda comandos do servidor central.

#### 4.3. Terminal do Separador

*   **Hardware:**
    *   **Dispositivo Principal:** Tablet ou smartphone robusto (Android/iOS).
    *   **Scanner (Recomendado):** Coletor de código de barras portátil com conexão Bluetooth. Modelos tipo "anel" (que se prendem ao dedo) ou tipo "pistola" são ideais, pois liberam as mãos do operador.
*   **Software (App VisuHall):**
    *   **Framework:** Desenvolvido em um framework multiplataforma como Flutter ou React Native.
    *   **Funcionalidades:**
        *   **Login de Usuário:** Para rastrear a produtividade.
        *   **Input de Pedido:** Tela para digitar o nº do pedido ou, idealmente, para escanear um QR Code/código de barras da ordem de serviço.
        *   **Tela de Mapa:** Renderiza a planta do estoque e a rota otimizada.
        *   **Tela de Prateleira:** Mostra a representação gráfica do local do item.
        *   **Lógica de Input:** O app deve ser capaz de receber dados tanto da câmera (scanner integrado) quanto de um dispositivo de entrada Bluetooth (o coletor externo, que geralmente se comporta como um teclado).

---

## 5. Fluxo de Trabalho Detalhado

1.  **Login e Input:** O separador faz login no app e escaneia o código do pedido a ser separado.
2.  **Processamento e Guia Visual:** O app envia o ID do pedido para o Servidor Pi. O servidor calcula a rota e instantaneamente acende as luzes dos setores relevantes.
    *   Setores com itens ficam em **Amarelo** (Em espera).
    *   O primeiro setor da rota fica em **Verde** (Ativo).
3.  **Navegação Macro:** O separador caminha em direção à luz **Verde**, sabendo exatamente o corredor e o lado correto para iniciar o trabalho.
4.  **Navegação Micro:** Ao chegar no setor, ele consulta o tablet, que o guia para o local exato do item.
5.  **Coleta e Confirmação por Scan:** O app exibe a "Visão da Prateleira". O separador localiza e coleta o item. Para confirmar a coleta, ele pode utilizar uma das duas opções de escaneamento:
    *   **Scanner Bluetooth (Método Recomendado):** Utiliza o coletor dedicado para uma leitura rápida e ergonômica.
    *   **Câmera do Dispositivo (Método Alternativo):** Utiliza a câmera integrada do tablet ou smartphone.
    O sistema então valida o código de barras lido. Se o código corresponder, a coleta é registrada. Caso contrário, o app emite um alerta sonoro e visual, prevenindo o erro.
6.  **Atualização Dinâmica:** Após a confirmação bem-sucedida, o Servidor Pi é notificado.
    *   Se houver outro item no mesmo setor, o app guia para o próximo ponto.
    *   Se for o último item do setor, a luz **Verde** se apaga. A luz **Amarela** do próximo setor na rota se torna **Verde**.
7.  **Ciclo:** O separador repete o processo, seguindo a próxima luz verde, até que todos os itens sejam coletados.
8.  **Finalização:** Todas as luzes se apagam. O app exibe "Pedido Concluído" e retorna à tela inicial, pronto para o próximo.

---

## 6. Gerenciamento de Múltiplos Separadores e Pedidos Concorrentes

A verdadeira força de um sistema de picking digital reside na sua capacidade de orquestrar múltiplos operadores simultaneamente sem gerar caos. O VisuHall é projetado com essa concorrência em mente, utilizando uma lógica de sessões e codificação por cores.

#### 6.1. Sessões de Picking e Codificação por Cor

*   **Sessão Individual:** Cada vez que um separador faz login e inicia um pedido, o Servidor Central cria uma **"sessão de picking"** única. Essa sessão vincula o ID do separador, o ID do pedido e uma **cor exclusiva** (ex: Verde, Azul, Roxo, Laranja) que será o identificador visual daquele separador durante todo o processo.
*   **Persistência da Cor:** A cor atribuída é usada em todas as interfaces para aquele separador: a luz "ativa" do setor será na sua cor, o traçado da rota no mapa será na sua cor e os destaques na "Visão de Prateleira" também. Isso cria um reforço visual constante e inequívoco.

#### 6.2. Fluxo de Trabalho Concorrente

Imagine dois separadores, Ana (Verde) e Bruno (Azul), começando a trabalhar.

1.  **Início:** Ana escaneia o Pedido 101. O sistema atribui a ela a cor **Verde**. As luzes dos setores A e C ficam amarelas (espera) e a do setor A fica verde (ativa). Bruno escaneia o Pedido 102. O sistema lhe dá a cor **Azul**. As luzes dos setores C e D ficam amarelas e a do setor D fica azul (ativa).
2.  **Navegação:** Ana se dirige à luz verde, e Bruno à luz azul. Eles trabalham em paralelo em corredores diferentes.

#### 6.3. Resolução de Conflitos de Setor

O desafio ocorre quando ambos precisam de itens no mesmo setor.

*   **Cenário:** Ana (Verde) está finalizando no setor A. Sua próxima tarefa é no setor C. Bruno (Azul) também precisa ir para o setor C.
*   **Lógica de Fila Visual:** A luz do setor C, que já estava amarela para ambos, agora precisa indicar que há trabalho para os dois. O sistema pode adotar duas abordagens:
    1.  **Sinalização Piscante:** A luz do setor C começa a piscar, alternando entre **Verde** e **Azul**. Isso sinaliza a ambos que aquele é um ponto de encontro.
    2.  **Prioridade de Chegada:** A luz muda para a cor do primeiro separador cuja rota o direciona para lá (digamos, Ana). A luz fica **Verde**. Quando Ana finaliza seu trabalho no setor, a luz automaticamente muda para **Azul**, sinalizando que agora é a vez de Bruno.
*   **O Tablet é a Fonte da Verdade:** Independentemente do estado da luz, o aplicativo no tablet de cada operador é a fonte final de verdade. O app de Ana dirá "Vá para o Setor C", e o de Bruno também. A luz serve como um guia de alta visibilidade, mas a instrução específica está no app, evitando qualquer ambiguidade.

#### 6.4. Dashboard do Gestor

Esta arquitetura permite a criação de um "Painel de Controle do Gestor" em tempo real no Servidor Central. Em uma tela na sala de controle, o gestor poderia ver:
*   A planta do estoque com pontos coloridos se movendo, representando cada separador.
*   O status de cada pedido em andamento (% de conclusão).
*   A produtividade individual e da equipe (itens/hora).
*   Identificação de gargalos (ex: múltiplos separadores esperando pelo mesmo setor).

---

## 7. Funcionalidades Avançadas (Fase 2)

Após a implementação bem-sucedida do sistema principal, funcionalidades avançadas podem ser adicionadas para aumentar ainda mais a inteligência e o controle sobre a operação.

#### 7.1. Rastreamento de Separadores em Tempo Real

A funcionalidade de exibir um mapa com pontos representando cada separador se movendo em tempo real requer a implementação de um **Sistema de Posicionamento Interno (Indoor Positioning System - IPS)**, já que o GPS não funciona em ambientes fechados.

*   **Método Recomendado (Custo-Benefício): Beacons Bluetooth (BLE)**
    *   **Como Funciona:** Pequenos dispositivos "beacons" são instalados pelo estoque. O tablet do operador mede a força do sinal recebido de múltiplos beacons para triangular sua posição aproximada no mapa.
    *   **Precisão:** Geralmente entre 1 a 5 metros, ideal para saber em qual corredor um operador está, mas não a prateleira exata.
    *   **Vantagem:** Oferece um excelente equilíbrio entre custo, facilidade de instalação e o benefício de ter um mapa de supervisão em tempo real.

*   **Método Alternativo (Alta Precisão): Ultra-Wideband (UWB)**
    *   **Como Funciona:** Um sistema de "âncoras" fixas e "tags" móveis que calculam a posição baseada no tempo de voo do sinal de rádio.
    *   **Precisão:** Extremamente alta, na casa dos centímetros.
    *   **Consideração:** É a solução profissional para rastreamento de ativos, mas possui um custo de hardware e implementação significativamente maior.

*   **Abordagem Inicial (Sem Custo): Rastreamento Implícito**
    *   O sistema pode ser lançado sem um IPS ativo. A posição do separador no mapa do gestor é inferida e "salta" para a localização do próximo item da rota cada vez que um scan de coleta é bem-sucedido.

#### 7.2. Painel Informativo de Setor

Para fornecer ainda mais contexto ao separador, o sinaleiro luminoso de cada setor pode ser substituído por um **Painel de Matriz de LEDs**.

*   **Conceito:** Em vez de apenas uma luz colorida, cada setor teria um pequeno painel capaz de exibir texto e números.
*   **Funcionalidade:** Ao se aproximar de um setor ativo, além de ver a cor correspondente à sua sessão, o separador veria informações cruciais diretamente no painel, como:
    *   **SKUs:** O número de itens únicos a serem coletados naquele setor.
    *   **QTD:** A quantidade total de peças a serem coletadas.
    *   **Exemplo de Display:** `SKU: 3 / QTD: 7`
*   **Vantagem:** Permite que o operador avalie o volume da tarefa à distância, melhorando o planejamento (ex: posicionamento do carrinho) e adicionando uma camada de verificação mental antes mesmo de consultar o tablet.

---

## 8. Vantagens Competitivas

*   **Eficiência Máxima:** Combina a velocidade da navegação por luz com a precisão da confirmação por scan.
*   **Segurança e Ergonomia:** Permite que o separador ande com a "cabeça erguida", aumentando a segurança e reduzindo a fadiga mental. O uso de um scanner Bluetooth dedicado melhora ainda mais a ergonomia e velocidade da coleta.
*   **Baixo Custo e Alta Flexibilidade:** Evita o custo proibitivo e a rigidez de um sistema Pick-to-Light completo. Alterações no layout do estoque são feitas via software.
*   **Inteligência de Dados:** Coleta dados valiosos sobre o tempo de picking, produtividade e rotas, permitindo otimizações contínuas.
*   **Rápida Implementação e Treinamento:** O sistema é intuitivo e um novo funcionário pode ser treinado para usá-lo em menos de uma hora.

---

## 9. Especificações de Hardware (Implementação Final)

#### 9.1. Quantidade de Setores

*   **Estantes de Picking (PCK):** 20
*   **Total de Setores a serem Instrumentados:** **40** (os dois lados de cada uma das 20 estantes PCK).

#### 9.2. Lista de Materiais por Setor

| Componente | Quantidade por Setor | Detalhe |
| :--- | :--- | :--- |
| **Controlador** | 1 | Placa de Desenvolvimento **ESP32** |
| **Sinaleiro Visual** | 1 | **Sinaleiro Industrial LED** (ou lâmpada inteligente customizada) |
| **Fonte de Alimentação**| 1 | Fonte de 5V ou 12V DC (dependerá do sinaleiro) |
| **Caixa de Proteção** | 1 | Caixa de montagem para proteger a eletrônica |
| **Fiação** | - | Fios e conectores diversos | 