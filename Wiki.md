# Plataforma de Orquestração de Agentes de IA
---

## Breve Descrição
---

Este projeto consiste em uma plataforma web para a criação, gerenciamento e orquestração de Agentes de Inteligência Artificial. O sistema permite que usuários configurem assistentes virtuais personalizados, alimentem-nos com conhecimento proprietário através de Bases de Conhecimento (RAG - Retrieval-Augmented Generation) e ampliem suas capacidades através de Toolsets (Conjuntos de Ferramentas), que podem incluir integrações via Webhooks, servidores MCP (Model Context Protocol) ou até mesmo a invocação de outros agentes.

Entre as funcionalidades oferecidas, destacam-se:
 - **Criação de Agentes Personalizados:** Configuração de modelos de LLM (GPT-4, Claude 3.5, etc.), definição de prompts de sistema, temperatura e limites de tokens;
 - **Bases de Conhecimento (RAG):** Upload e processamento de documentos (PDFs), que são vetorizados e armazenados para permitir que o agente consulte informações específicas durante uma conversa;
 - **Integração com Ferramentas (Toolsets):**
   - **MCP (Model Context Protocol):** Conexão com servidores de ferramentas padronizados;
   - **Webhooks:** Definição de chamadas de API personalizadas que o agente pode executar;
   - **Agente como Ferramenta:** Capacidade de um agente invocar outro agente para resolver sub-tarefas (Orquestração Multi-Agente);
 - **Interface de Chat:** Ambiente interativo para conversar com os agentes e validar seus comportamentos.

O sistema foi concebido como um Trabalho Final de Programação (PUC-Rio), visando demonstrar a aplicação prática de conceitos modernos de Engenharia de Software e Inteligência Artificial Generativa. Ele serve como uma prova de conceito robusta para desenvolvedores e estudantes interessados em arquiteturas de LLM, bancos de dados vetoriais e frameworks de frontend reativos.

**Ressalvas de uso:** O sistema requer chaves de API válidas (OpenAI, Anthropic, Google, etc.) para funcionar plenamente. Ele é um projeto acadêmico e, embora funcional, deve ser adaptado antes de qualquer utilização em ambientes críticos de produção.

---

## Visão de Projeto
---

### Cenário Positivo 1: Estudante de Engenharia de Prompt
Lucas, um estudante de Ciência da Computação, deseja entender na prática como a "temperatura" e o "prompt de sistema" influenciam as respostas de uma IA. Ele cria dois agentes idênticos na plataforma, chamados "Agente Frio" (Temperatura 0.1) e "Agente Criativo" (Temperatura 0.9). Ao fazer a mesma pergunta para ambos ("Escreva uma história curta sobre um robô"), ele compara as respostas lado a lado no chat e visualiza claramente as diferenças. Em seguida, ele altera o System Prompt do "Agente Criativo" para adotar uma persona sarcástica e testa novamente, aprendendo empiricamente sobre engenharia de prompt.

### Cenário Positivo 2: Aprendendo sobre Embeddings (RAG)
Mariana está estudando como funcionam bancos de dados vetoriais. Ela cria uma Base de Conhecimento e faz o upload de um texto técnico sobre "Redes Neurais". Após o processamento, ela interage com um agente vinculado a essa base. Curiosa para ver se o sistema realmente busca por similaridade semântica e não apenas por palavras-chave, ela faz perguntas usando sinônimos e termos relacionados que não estão explicitamente no texto. O agente recupera os trechos corretos, demonstrando a eficácia da busca vetorial do Qdrant, e Mariana valida seu aprendizado sobre RAG.

### Cenário Positivo 3: Aprendendo Tool Calling e APIs
Ricardo quer entender como LLMs interagem com APIs externas. Ele configura um Toolset do tipo "Custom" (Webhook) e define uma ferramenta simples chamada `get_weather` que aponta para uma API pública de clima. Ele define o JSON Schema dos parâmetros (latitude e longitude) e cria um agente com acesso a essa ferramenta. Ao pedir "Como está o tempo no Rio de Janeiro?", ele observa nos logs do sistema como o modelo decide chamar a ferramenta, preenche os parâmetros corretamente com as coordenadas do Rio e usa o JSON de resposta da API para formular a resposta final em linguagem natural.

### Cenário Positivo 4: Testando Servidor MCP Próprio
Júlia desenvolveu seu próprio servidor MCP em Python para controlar dispositivos IoT de sua casa. Antes de integrá-lo a sistemas comerciais complexos, ela usa a plataforma para testar. Ela sobe seu servidor localmente, cadastra a URL no menu "Toolsets" e vê suas ferramentas (`ligar_luz`, `ler_temperatura`) serem listadas automaticamente. Ela então cria um agente e conversa com ele para verificar se as chamadas às ferramentas estão acionando corretamente seu código Python local, validando sua implementação do protocolo MCP.

### Cenário Positivo 5: Comparativo de Orquestração entre Modelos
Dr. Silva é um pesquisador investigando a capacidade de raciocínio de diferentes LLMs. Ele deseja saber se o `Claude 4.5 Sonnet` é melhor que o `GPT-5` para decompor tarefas complexas. Ele cria um Toolset com ferramentas matemáticas e de busca. Em seguida, configura dois agentes com o mesmo prompt de sistema e as mesmas ferramentas, mas com modelos diferentes. Ele submete a mesma instrução complexa ("Planeje uma viagem para Paris com orçamento de 2000 euros considerando voos e hotéis atuais") para ambos e analisa os "traces" de execução para comparar qual modelo escolheu as ferramentas mais adequadas e em qual ordem, gerando dados para sua pesquisa.

### Cenário Negativo 1: Falha na Conexão MCP (Slack)
Um usuário tenta cadastrar um novo Toolset do tipo "MCP Server" para integrar o Slack ao seu agente. No entanto, ao preencher o campo de URL, ele digita incorretamente o endereço do servidor (ex: `http://localhost:9000` em vez de `8000`). Ao tentar salvar, o backend tenta estabelecer uma conexão com o servidor MCP para listar as ferramentas disponíveis, mas falha. O sistema exibe imediatamente uma mensagem de erro informando que "Não foi possível conectar ao servidor MCP na URL fornecida", impedindo o cadastro de um servidor inacessível.

### Cenário Negativo 2: Consulta a Base Vazia
Um usuário cria um Agente e vincula uma Base de Conhecimento recém-criada, mas esquece de fazer o upload dos arquivos. Ao perguntar "O que o documento diz sobre o prazo de entrega?", o agente responde: "Desculpe, não encontrei nenhum documento relevante na base de conhecimento para analisar e responder sua pergunta." O usuário percebe o erro, navega até a base de conhecimento, faz o upload dos arquivos PDF necessários e, após o processamento, volta ao chat e obtém a resposta correta.

---

# Documentação Técnica do Projeto
---

## Arquitetura do Sistema

O projeto adota uma arquitetura de **Single Page Application (SPA)** no frontend e **API REST** no backend, com suporte a processamento assíncrono para tarefas pesadas de IA.

 - **Frontend (SolidJS + Vite):** Responsável pela interface reativa. Gerencia o estado da aplicação, chamadas de API e renderização dos componentes de chat e formulários.
 - **Backend (FastAPI):** Núcleo da aplicação. Gerencia as rotas, validação de dados (Pydantic) e orquestração das chamadas para as LLMs (via PydanticAI e LangChain).
 - **Banco de Dados Relacional (PostgreSQL):** Armazena dados estruturados: configurações dos agentes, histórico de chat, definições de ferramentas e metadados dos arquivos.
 - **Banco de Dados Vetorial (Qdrant):** Armazena os *embeddings* (representações vetoriais) dos textos das Bases de Conhecimento, permitindo busca semântica.

## Estrutura de Dados

As principais entidades que regem o domínio da aplicação são:

- **Agent:** Representa a configuração de um assistente virtual. Armazena o nome, descrição, configurações do modelo de IA (provedor, temperatura, max tokens) e os prompts de sistema que definem sua personalidade e comportamento.
- **AgentKnowledgeBase:** Tabela associativa que vincula Agentes a Bases de Conhecimento, permitindo relacionamentos n-para-n (um agente pode acessar várias bases, e uma base pode ser usada por vários agentes).
- **AgentToolset:** Tabela associativa que vincula Agentes a Toolsets, definindo quais conjuntos de ferramentas estão disponíveis para cada agente, permitindo relacionamentos n-para-n.
- **KnowledgeBase:** Representa um agrupador lógico de arquivos. Serve como um contêiner para organizar documentos relacionados a um tema específico.
- **File:** Armazena os metadados dos arquivos enviados (nome original, tamanho, data de upload) e controla o status do processamento (processing, active, failed).
- **Chunk:** Representa os fragmentos de texto extraídos dos arquivos. Cada chunk contém o texto, a referência ao arquivo original e os metadados necessários para a busca vetorial (embora o vetor em si fique no Qdrant, esta tabela mantém a referência relacional).
- **Toolset:** Define um agrupamento de ferramentas. Pode ser de diferentes tipos (MCP Server, Custom), servindo como ponto de configuração para integrações externas.
- **Tool:** A definição concreta de uma função executável. Contém o nome, descrição e o esquema JSON dos parâmetros de entrada. Pode representar uma ferramenta remota (via MCP), um endpoint de API (Webhook) ou uma referência para invocar outro Agente.
- **Chat:** Representa uma sessão de conversa iniciada por um usuário com um agente.
- **Message:** Armazena o histórico individual das trocas de mensagens dentro de um Chat. Guarda o conteúdo textual e timestamps.

Esquema do Banco de Dados:
![Diagrama ER - Placeholder](https://via.placeholder.com/800x400?text=Diagrama+Entidade+Relacionamento)

## Estrutura de Módulos (Backend)

O backend do projeto segue uma arquitetura modular baseada em **Domain-Driven Design (DDD)** simplificado. Cada "módulo" dentro de `src/modules` encapsula toda a lógica, persistência e exposição de API relacionada a um domínio específico do negócio. Isso garante alta coesão e baixo acoplamento, facilitando a manutenção e a escalabilidade.

### Anatomia de um Módulo
A maioria dos módulos compartilha uma estrutura de arquivos padronizada:

- **`models.py`:** Define as entidades do banco de dados utilizando o ORM **SQLAlchemy**. É aqui que as tabelas e seus relacionamentos são declarados.
- **`schemas.py`:** Contém os modelos **Pydantic** para validação de dados internos e tipagem.
- **`routes.py`:** Define os *endpoints* da API (Controllers) utilizando **FastAPI**. É a porta de entrada das requisições HTTP.
- **`routes_schemas.py`:** Define os DTOs (Data Transfer Objects) específicos para entrada (Request Body) e saída (Response Model) da API, separando a camada de apresentação da camada de domínio.
- **`repositories/`:** Pasta contendo classes responsáveis pela abstração do acesso a dados (Repository Pattern). Isolam as consultas SQL (`select`, `insert`, `update`) da lógica de negócios.

### Detalhamento dos Módulos

#### 1. Módulo `agents`
Responsável pelo ciclo de vida da entidade central do sistema: o Agente.
- Gerencia o CRUD completo dos agentes.
- Controla as associações (N-para-N) com Bases de Conhecimento e Toolsets.
- Valida as configurações de LLM (garantindo que parâmetros como temperatura e limites de tokens estejam dentro do esperado).

#### 2. Módulo `chat`
Este é o "cérebro" da execução da IA. Não serve apenas para armazenar mensagens, mas para orquestrar a execução.
- **CRUD de Sessões:** Gerencia a criação, listagem e exclusão de históricos de conversa (`Chats`), permitindo que o usuário retome sessões anteriores.
- **`AgentExecutor`:** Componente crítico que instancia o cliente da LLM (via PydanticAI ou LangChain), injeta o `System Prompt` e gerencia o loop de execução.
- **Gerenciamento de Contexto:** Recupera o histórico da conversa e o injeta na janela de contexto da IA.
- **Execução de Ferramentas:** Detecta quando a LLM solicita o uso de uma ferramenta, executa a função correspondente (seja uma busca vetorial, uma chamada HTTP ou uma query MCP) e devolve o resultado para a IA.

#### 3. Módulo `knowledge_base`
Responsável por todo o pipeline de RAG (Retrieval-Augmented Generation), desde a ingestão até a busca.
- **CRUD de Bases:** Gerencia a criação, edição e remoção das Bases de Conhecimento e seus arquivos associados.
- **Ingestão (`ProcessFile.py`):** Gerencia o upload de arquivos e utiliza a biblioteca **Zerox** para realizar OCR e conversão de PDF para Markdown limpo.
- **Chunking:** Divide o texto processado em fragmentos menores e semanticamente coerentes.
- **Vetorização:** Comunica-se com a API de Embeddings (ex: OpenAI) para transformar texto em vetores numéricos.
- **Integração Qdrant:** Gerencia as coleções no banco vetorial, realizando inserções e buscas por similaridade semântica (Cosine Similarity).

#### 4. Módulo `toolsets`
Atua como um hub de integração para capacidades externas.
- **CRUD de Ferramentas:** Permite criar, configurar e remover integrações de toolsets (seja um endpoint Webhook manual ou uma conexão MCP).
- **Gerenciador MCP (`MCPManager.py`):** Implementa o cliente para o *Model Context Protocol*. Conecta-se a servidores MCP remotos, negocia capacidades e sincroniza a lista de ferramentas disponíveis para o banco de dados local.
- **Webhooks Customizados:** Processa definições de ferramentas manuais, armazenando seus JSON Schemas para que a LLM saiba como estruturar as chamadas de API.
- **Registry de Ferramentas:** Centraliza todas as ferramentas disponíveis (sejam nativas, MCP ou Webhooks) para que possam ser vinculadas aos agentes.

#### 5. Módulo `copilot`
Um módulo auxiliar focado em metadados e suporte à interface do usuário.
- Fornece endpoints para listar os modelos de LLM disponíveis (ex: conecta na API da OpenAI ou Anthropic para verificar quais modelos a chave de API configurada tem acesso).
- Serve como ponto de extensão para funcionalidades de "Copilot" da própria plataforma (ajuda ao usuário).

## Requisitos Funcionais

### RF01 – Criar Agentes
**Descrição:** O sistema deve permitir criar novos agentes e associa-los a bases de conhecimento e toolsets.
**Ator:** Usuário.
**Pré-condições:** O sistema deve estar operacional e o usuário deve ter acesso à interface. Bases de conhecimento e toolsets opcionais podem existir previamente.
**Pós-condições:** Um novo agente é persistido no banco de dados e fica disponível para interação no chat.
**Fluxo Principal:**
 1. O usuário navega até a página de "Agents" através do menu lateral.
 2. O usuário clica no botão "Create Agent".
 3. O sistema apresenta o formulário de criação de agente.
 4. O usuário preenche as informações básicas (nome, descrição, cor) e configurações do modelo (provedor, temperatura, limites de tokens).
 5. O usuário define o "System Prompt" e o "Contextualize System Prompt".
 6. (Opcional) O usuário seleciona Bases de Conhecimento e Toolsets na abas correspondentes para vincular ao agente.
 7. O usuário clica no botão "Save Agent".
 8. O sistema valida os dados, cria o agente e redireciona o usuário para a lista de agentes.

### RF02 – Gerenciar Agentes (Editar e Deletar)
**Descrição:** O sistema deve permitir editar as configurações de um agente existente ou excluí-lo.
**Ator:** Usuário.
**Pré-condições:** Deve existir pelo menos um agente cadastrado no sistema.
**Pós-condições:** O agente tem suas informações atualizadas ou é removido permanentemente do sistema.
**Fluxo Principal:**
 1. O usuário navega até a página de "Agents".
 2. O sistema lista os agentes cadastrados.
 3. O usuário identifica o agente desejado na lista.
 4. **Para Editar:**
    a. O usuário clica no botão "Edit" no cartão/linha do agente desejado.
    b. O sistema carrega o formulário com os dados atuais do agente.
    c. O usuário modifica os campos desejados e clica em "Save Agent".
    d. O sistema atualiza o registro.
 5. **Para Deletar:**
    a. O usuário clica no botão "Delete" correspondente ao agente.
    b. O usuário confirma a ação no diálogo de confirmação.
    c. O sistema remove o agente e atualiza a lista.

### RF03 – Criar Bases de Conhecimento
**Descrição:** O sistema deve permitir criar novas bases de conhecimento (agrupadores lógicos).
**Ator:** Usuário.
**Pré-condições:** O sistema de banco de dados vetorial (Qdrant) deve estar operacional.
**Pós-condições:** Uma nova base de conhecimento vazia é criada.
**Fluxo Principal:**
 1. O usuário navega até a página "Knowledge Bases".
 2. O usuário clica no botão "Create Knowledge Base".
 3. O sistema exibe um modal para inserção de dados.
 4. O usuário informa o nome e a descrição da nova base.
 5. O usuário confirma a criação clicando em "Save".
 6. O sistema cria o registro da base e a exibe na lista.

### RF04 – Gerenciar Bases de Conhecimento (Editar e Deletar)
**Descrição:** O sistema deve permitir editar os metadados de uma base ou excluí-la.
**Ator:** Usuário.
**Pré-condições:** Deve existir pelo menos uma base de conhecimento cadastrada.
**Pós-condições:** A base de conhecimento é atualizada ou excluída (juntamente com seus arquivos e vetores associados).
**Fluxo Principal:**
 1. O usuário acessa a página "Knowledge Bases".
 2. O usuário identifica a base desejada.
 3. **Para Editar:**
    a. O usuário clica no ícone de edição no cartão da base.
    b. O usuário altera o nome ou descrição no modal e salva.
 4. **Para Deletar:**
    a. O usuário clica no ícone de lixeira no cartão da base.
    b. O usuário confirma a exclusão.
    c. O sistema remove a base do banco relacional e a coleção correspondente no banco vetorial.

### RF05 – Fazer Upload de Arquivos
**Descrição:** O sistema deve permitir o upload de arquivos para uma base de conhecimento e processá-los.
**Ator:** Usuário. Sistema.
**Pré-condições:** Deve existir uma base de conhecimento criada.
**Pós-condições:** O arquivo é armazenado, seu texto é extraído, fragmentado (chunking), vetorizado e indexado no banco vetorial. O status do arquivo passa para "active".
**Fluxo Principal:**
 1. O usuário acessa os detalhes de uma base de conhecimento (clicando em "View Files" na lista de bases).
 2. O usuário arrasta arquivos (PDF) para a área de upload ou clica para selecionar do computador.
 3. O sistema inicia o upload e exibe o arquivo na lista com status "processing".
 4. O backend processa o arquivo assincronamente (OCR/Extração -> Chunking -> Embedding -> Indexação).
 5. O sistema atualiza o status do arquivo para "active" quando o processo é concluído com sucesso.

### RF06 – Gerenciar Arquivos (Deletar)
**Descrição:** O sistema deve permitir remover arquivos de uma base de conhecimento.
**Ator:** Usuário.
**Pré-condições:** Deve haver arquivos carregados em uma base de conhecimento.
**Pós-condições:** O arquivo é removido do sistema e seus vetores são apagados do banco vetorial.
**Fluxo Principal:**
 1. O usuário acessa a página de detalhes da base de conhecimento.
 2. O sistema exibe a lista de arquivos.
 3. O usuário identifica o arquivo e clica no botão "Delete".
 4. O usuário confirma a ação.
 5. O sistema remove o registro do arquivo e seus embeddings associados.

### RF07 – Criar toolset com MCP
**Descrição:** O sistema deve permitir integrar ferramentas externas via protocolo MCP.
**Ator:** Usuário. Sistema.
**Pré-condições:** Um servidor compatível com o protocolo MCP deve estar em execução e acessível via URL.
**Pós-condições:** Um toolset é criado e as ferramentas expostas pelo servidor MCP são automaticamente catalogadas no sistema.
**Fluxo Principal:**
 1. O usuário acessa a página "Toolsets".
 2. O usuário clica em "Create Toolset".
 3. O usuário seleciona o tipo "MCP Server" no seletor de tipo.
 4. O usuário preenche o nome, descrição e a URL do servidor MCP.
 5. (Opcional) O usuário configura headers de autenticação se o servidor exigir.
 6. O usuário clica em "Save Toolset".
 7. O sistema conecta-se ao servidor MCP, lista as ferramentas disponíveis e salva o toolset com essas referências.

### RF08 – Criar toolset para integração com API
**Descrição:** O sistema deve permitir criar ferramentas de Webhook que chama rotas de API's externas.
**Ator:** Usuário.
**Pré-condições:** O usuário deve possuir a documentação da API que deseja integrar (URL, método, parâmetros).
**Pós-condições:** Um toolset do tipo "Custom" é criado com definições manuais de ferramentas (Webhooks).
**Fluxo Principal:**
 1. O usuário inicia a criação de um Toolset e seleciona/mantém o tipo como "Custom".
 2. O usuário preenche nome e descrição do Toolset.
 3. O usuário navega para a aba "Tools".
 4. O usuário clica em "Add Tool".
 5. O usuário define o nome e descrição da ferramenta.
 6. O usuário seleciona o tipo "Webhook" (padrão) no card da ferramenta.
 7. O usuário configura o método HTTP (GET, POST, etc.) e a URL do endpoint.
 8. O usuário define os JSON Schemas para os parâmetros de Query, Path e Body, conforme exigido pela API.
 9. O usuário salva o Toolset.

### RF09 – Criar toolset para orquetração Multiagente
**Descrição:** O sistema deve permitir criar ferramentas que façam invoções de agentes.
**Ator:** Usuário. 
**Pré-condições:** Devem existir outros agentes criados no sistema para serem invocados.
**Pós-condições:** Uma ferramenta é criada permitindo que o agente atual delegue tarefas a outro agente específico.
**Fluxo Principal:**
 1. Dentro da criação de um Toolset do tipo "Custom", o usuário adiciona uma nova ferramenta na aba "Tools".
 2. No card da nova ferramenta, o usuário altera o "Tool Type" de "Webhook" para "Agent".
 3. O sistema exibe um seletor de agentes ("Target Agent").
 4. O usuário seleciona qual agente existente será invocado por esta ferramenta.
 5. O usuário nomeia a ferramenta (ex: "consultar_especialista_financeiro") e descreve a finalidade para que o modelo saiba quando usá-la.
 6. O usuário salva o Toolset.

### RF10 – Gerenciar toolsets
**Descrição:** O sistema deve permitir editar toolset e deletar toolsets.
**Ator:** Usuário. 
**Pré-condições:** Existir toolsets cadastrados.
**Pós-condições:** O toolset é atualizado ou removido do sistema.
**Fluxo Principal:**
 1. O usuário acessa a lista de Toolsets.
 2. O usuário identifica o toolset desejado.
 3. **Para Editar:**
    a. O usuário clica no ícone de edição.
    b. O sistema carrega o formulário com as configurações atuais.
    c. O usuário pode alterar nome, descrição, URL (para MCP) ou adicionar/remover/editar ferramentas (para Custom).
    d. O usuário salva as alterações.
 4. **Para Deletar:**
    a. O usuário clica no ícone de lixeira.
    b. O usuário confirma a exclusão.
    c. O sistema remove o toolset e suas ferramentas associadas.

### RF11 – Chat e Execução
**Descrição:** Interface para interagir com o agente, suportando histórico e visualização de uso de ferramentas.
**Ator:** Usuário.
**Pré-condições:** Pelo menos um agente deve estar ativo no sistema.
**Pós-condições:** A conversa é realizada, ferramentas podem ser executadas e o histórico da sessão é persistido.
**Fluxo Principal:**
 1. O usuário acessa a página "Chat".
 2. O sistema carrega uma nova sessão ou a última sessão acessada.
 3. O usuário seleciona o Agente com quem deseja conversar no menu suspenso (dropdown).
 4. O usuário digita uma mensagem na caixa de entrada e envia.
 5. O sistema exibe a mensagem do usuário.
 6. O agente processa a mensagem. Se necessário, ele decide usar ferramentas (RAG, Webhook, MCP, Outro Agente).
 7. O sistema exibe indicadores de uso de ferramenta ("Tool Use") se ocorrerem, permitindo ao usuário ver os inputs e outputs das ferramentas expandindo os detalhes.
 8. O agente gera e exibe a resposta final baseada no contexto e nos resultados das ferramentas.

### RF12 – Chats anteriores
**Descrição:** Interface para acessar interações anteriores com agentes.
**Ator:** Usuário.
**Pré-condições:** Deve existir pelo menos uma sessão de chat iniciada previamente.
**Pós-condições:** O histórico da conversa selecionada é carregado, permitindo a continuidade da interação.
**Fluxo Principal:**
 1. O usuário visualiza a barra lateral esquerda (Sidebar).
 2. O sistema exibe a lista de "Recent Chats" (Chats Recentes).
 3. O usuário clica no título de um dos chats listados.
 4. O sistema carrega o histórico completo de mensagens daquela sessão na área principal.
 5. O usuário pode continuar a conversa de onde parou.
 6. (Opcional) O usuário pode clicar no ícone de lápis para renomear o chat ou na lixeira para excluí-lo diretamente pela sidebar.

## Requisitos Não Funcionais

### RNF01 – Manutebilidade

O sistema deve ser arquitetado visando a facilidade de manutenção e a clareza do código. No backend, deve-se adotar uma estrutura modular inspirada em Domain-Driven Design (DDD), onde cada módulo (Agentes, Chat, Knowledge Base, Toolsets) encapsula suas próprias rotas, modelos, schemas e lógica de negócio. A utilização do framework FastAPI em conjunto com Pydantic deve garantir validação rigorosa de dados e tipagem forte, reduzindo erros em tempo de execução e facilitando a compreensão do fluxo de dados por novos desenvolvedores.

### RNF02 – Extensibilidade

A plataforma deve ser projetada para crescer e integrar-se a novos ecossistemas com mínimo esforço. O módulo de Toolsets deve suportar o protocolo MCP (Model Context Protocol) e Webhooks genéricos, permitindo que o sistema se conecte a qualquer API externa ou ferramenta sem necessidade de alteração no código fonte do núcleo da aplicação. Além disso, a abstração dos modelos de linguagem (LLMs) deve permitir a fácil adição de novos provedores de IA conforme o mercado evolui.

### RNF03 – Usabilidade

A interface do usuário deve ser construída com SolidJS, um framework reativo de alta performance, e estilizada com Tailwind CSS para garantir responsividade e consistência visual. O design deve priorizar a clareza, utilizando padrões de navegação familiares (como sidebar persistente e modais intuitivos) e feedback visual imediato (indicadores de carregamento, mensagens de erro e sucesso), assegurando que usuários, mesmo sem conhecimento técnico profundo, consigam configurar agentes e bases de conhecimento de forma autônoma.

### RNF04 – Desempenho

O sistema deve garantir tempos de resposta rápidos e alta vazão de requisições. Para isso, o backend deve utilizar a natureza assíncrona do FastAPI e Python (`async/await`) para lidar com operações de I/O intensivas, como chamadas a APIs de LLM. O armazenamento e recuperação de informações contextuais devem ser otimizados pelo uso do Qdrant, um banco de dados vetorial especializado em busca por similaridade de alta performance, garantindo que o RAG (Retrieval-Augmented Generation) funcione em tempo real mesmo com grandes volumes de dados.

---

# Manual de Utilização
---

## Criando e Configurando um Agente

### Guia de Instruções:
 1. Navegue até a página **Agents** através da Sidebar.
 2. Clique no botão de criar (ícone `+`) ou selecione um agente existente para editar.
 3. Preencha as **Informações Básicas**: Nome, Descrição e Cor (para identificação no chat).
 4. Configure o **Modelo**:
    - Selecione o provedor/modelo (ex: `openai:gpt-4o`).
    - Ajuste a `Temperatura` (maior = mais criativo, menor = mais preciso).
    - Defina `Max Response Tokens` para limitar o tamanho da resposta.
 5. Configure os **Prompts**:
    - `System Prompt`: A personalidade e instruções principais do agente.
    - `Contextualize System Prompt`: Instruções sobre como o agente deve usar o contexto RAG recuperado.
 6. Clique em **Save Agent** para registrar as alterações.

### Exceções:
 - Se a chave de API do modelo escolhido não estiver configurada no `.env` do backend, o agente retornará erro ao tentar conversar.

## Associando uma Base de Conhecimento e um Toolset a um Agente

### Guia de Instruções:
 1. Na tela de criação ou edição de Agente, clique na aba **Knowledge Bases**.
 2. O sistema listará as bases de conhecimento disponíveis. Clique sobre os cartões para selecionar ou desmarcar as bases desejadas. As selecionadas ficarão destacadas.
 3. Clique na aba **Toolsets**.
 4. O sistema listará os conjuntos de ferramentas disponíveis. Clique sobre os cartões para selecionar ou desmarcar os toolsets desejados.
 5. Clique em **Save Agent** para persistir as associações.

### Exceções:
 - Se um Toolset selecionado estiver com configuração inválida (ex: servidor MCP offline), o agente poderá falhar ao tentar usar ferramentas.

## Criando e Gerenciando Bases de Conhecimento (Upload de Arquivos)

### Guia de Instruções:
 1. Acesse a página **Knowledge Bases** pelo menu lateral.
 2. Clique no botão "Create Knowledge Base".
 3. Insira um nome e uma descrição para a nova base e clique em "Save".
 4. Na lista de bases, clique no link "View Files" ou no título do cartão da base criada.
 5. Arraste arquivos (PDF) para a área pontilhada ou clique em "Browse Computer" para selecionar do disco.
 6. O sistema iniciará o upload e processamento. O status mudará de `processing` para `active`.
 7. Para excluir um arquivo, clique no botão "Delete" na linha correspondente e confirme.

### Exceções:
 - Arquivos corrompidos ou protegidos por senha podem falhar no processamento (status `failed`).
 - O sistema aceita preferencialmente arquivos PDF para extração de texto.

## Criando e configurando Toolsets (CUSTOM/MCP)

### Guia de Instruções:
 1. Acesse a página **Toolsets** pelo menu lateral.
 2. Clique no botão "Create Toolset".
 3. Defina o nome e a descrição do Toolset.
 4. Selecione o **Toolset Type**:
    - **Custom:** Para definir ferramentas manualmente (Webhooks ou Agentes).
    - **MCP Server:** Para conectar a um servidor compatível com Model Context Protocol.
 5. Se escolheu **MCP Server**:
    - Insira a **MCP Server URL** (ex: `http://localhost:8000/mcp`).
    - (Opcional) Configure headers de autenticação se necessário.
 6. Clique em "Save Toolset". O sistema tentará conectar ao servidor MCP para descobrir as ferramentas automaticamente.

### Exceções:
 - Se a URL do servidor MCP estiver incorreta ou o servidor offline, o salvamento falhará ou as ferramentas não serão listadas.

## Criando e configurando ferramenta Webhook

### Guia de Instruções:
 1. Crie ou edite um Toolset do tipo **Custom**.
 2. Vá para a aba **Tools**.
 3. Clique em "+ Add Tool".
 4. Preencha o nome e a descrição da ferramenta.
 5. Certifique-se de que o seletor "Tool Type" esteja em **Webhook**.
 6. Escolha o método HTTP (GET, POST, etc.) e insira a **Webhook URL**.
 7. (Opcional) Configure headers de autenticação.
 8. Clique em "Show Advanced Configuration" para definir os JSON Schemas dos parâmetros (Query, Path, Body).
 9. Clique em "Save Toolset" para salvar todas as ferramentas configuradas.

### Exceções:
 - Schemas JSON inválidos podem impedir que a LLM entenda como usar a ferramenta corretamente.

## Criando e configurando ferramenta Multiagente

### Guia de Instruções:
 1. Crie ou edite um Toolset do tipo **Custom**.
 2. Vá para a aba **Tools** e clique em "+ Add Tool".
 3. Preencha o nome e a descrição (explique claramente o que o agente alvo faz).
 4. Altere o seletor "Tool Type" para **Agent**.
 5. No campo "Target Agent", selecione o agente que será invocado na lista suspensa.
 6. Clique em "Save Toolset".

### Exceções:
 - Se o agente alvo for deletado posteriormente, a ferramenta poderá falhar ao ser executada.

## Fazendo pergunta para um Agente

### Guia de Instruções:
 1. Acesse a página **Chat** pelo menu lateral.
 2. No topo da área de input, selecione o agente desejado no dropdown "Chat with:".
 3. Digite sua pergunta ou comando na caixa de texto.
 4. Pressione Enter ou clique no botão de enviar.
 5. Acompanhe a resposta. Se o agente usar ferramentas, blocos expansíveis aparecerão mostrando o nome da ferramenta, argumentos e resultado.
 6. A resposta final será gerada após a execução das ferramentas.

### Exceções:
 - Se o agente não tiver ferramentas adequadas para a solicitação, ele pode responder que não sabe ou alucinar uma resposta (dependendo da temperatura).
 - Erros de rede ou na API da LLM podem interromper a geração da resposta.

## Visualizando chats anteriores

### Guia de Instruções:
 1. Na página de Chat (ou qualquer outra), observe a barra lateral esquerda.
 2. A seção "Recent Chats" lista as conversas anteriores.
 3. Clique no título de um chat para carregar o histórico completo.
 4. Para renomear, passe o mouse sobre o chat na lista e clique no ícone de lápis. Digite o novo nome e confirme.
 5. Para excluir, clique no ícone de lixeira.

