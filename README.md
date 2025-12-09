# Projeto Final de Programação - PUC-Rio

## Sobre o Projeto

Este projeto é uma plataforma completa para criação e gerenciamento de Agentes de Inteligência Artificial, Bases de Conhecimento (RAG) e Conjuntos de Ferramentas (Toolsets). O sistema permite que usuários configurem agentes personalizados com prompts específicos, integrem esses agentes com documentos para contexto (via RAG) e ferramentas externas (como servidores MCP e Webhooks).

**Funcionalidades Principais:**
- **Gestão de Agentes:** Criação de assistentes de IA com personalização de modelos (GPT-4, Claude, etc.), prompts de sistema e parâmetros como temperatura e máximo de tokens de output.
- **Bases de Conhecimento (RAG):** Upload de documentos (PDFs, textos) que são processados, vetorizados e armazenados no Qdrant para recuperação semântica durante as conversas.
- **Toolsets & MCP:** Suporte ao *Model Context Protocol* (MCP) para conectar ferramentas externas, Webhooks personalizados para integração com API's e tools para invocação de outros agentes.
- **Orquestração Multi-Agente:** A ferramenta permite uma lógica de orquestração de multiagentes através da criação de tools que invocam agentes criados na plataforma, possibilitando a criação de multiplos agentes que interagem entre si.
- **Chat Interativo:** Interface de chat para interagir com os agentes criados.

---

## Tech Stack

### Frontend
- **Framework:** [SolidJS](https://www.solidjs.com/) (Reatividade de alto desempenho)
- **Build Tool:** [Vite](https://vitejs.dev/)
- **Estilização:** [Tailwind CSS](https://tailwindcss.com/)
- **Linguagem:** TypeScript

### Backend
- **Framework Web:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
- **Banco de Dados Relacional:** PostgreSQL (com driver `asyncpg` e ORM SQLAlchemy)
- **Banco de Dados Vetorial:** [Qdrant](https://qdrant.tech/) (para RAG)
- **IA & LLM Orchestration:** 
  - [PydanticAI](https://github.com/pydantic/pydantic-ai)
  - [LangChain](https://www.langchain.com/)
  - [Zerox](https://github.com/getomni-ai/zerox) (Processamento de OCR/PDF)
- **Migrações:** Alembic
- **Infraestrutura:** Docker & Docker Compose

---

## Estrutura do Projeto

### Backend (`back-end/`)
O backend segue uma arquitetura modular baseada em domínios dentro de `src/modules`. Cada módulo geralmente contém os seguintes arquivos:
- `models.py`: Modelos de banco de dados (SQLAlchemy).
- `schemas.py`: Schemas Pydantic para validação interna e tipos.
- `routes.py`: Definição das rotas da API (Endpoints).
- `routes_schemas.py`: Schemas Pydantic específicos para requisições e respostas da API.
- `repositories/`: Camada de acesso a dados (CRUD).

#### Módulos (`src/modules/`)
- `agents`: Gerenciamento de agentes e suas configurações.
- `chat`: Orquestração do chat, histórico de mensagens e execução dos agentes.
- `knowledge_base`: Gestão de arquivos, processamento (chunking, embedding) e integração com Qdrant.
- `toolsets`: Gerenciamento de ferramentas (Tools), incluindo integração com servidores MCP e Webhooks.
- `copilot`: Rotas auxiliares, como listagem de modelos disponíveis.

#### Arquivos e Pastas Importantes
- `src/main.py`: Ponto de entrada da aplicação FastAPI. Configura rotas, middlewares e inicialização.
- `src/config.py`: Gerenciamento de configurações e variáveis de ambiente (carrega do `.env`).
- `src/database/`: Configuração da conexão com banco de dados (`session_manager.py`) e inicialização.
- `alembic/`: Scripts de migração de banco de dados para versionamento do schema.
- `docker-compose.yml`: Definição dos serviços (API, Postgres, Qdrant, PgAdmin) para execução em containers.
- `requirements.txt`: Lista de dependências Python do projeto.

### Frontend (`front-end/`)
O frontend é organizado por funcionalidades e páginas, com uma camada de API bem definida:

- `src/api`: Camada de comunicação com o Backend.
  - `api.ts`: Cliente HTTP base (wrapper do `fetch`) que gerencia requisições, tratamento de erros e tipagem de respostas.
  - `routes/`: Funções que encapsulam as chamadas aos endpoints da API, organizadas por domínio (ex: `agents.ts`, `chats.ts`).
  - `types/`: Interfaces TypeScript que espelham os schemas do backend (Pydantic), garantindo tipagem estática e segurança nos dados (ex: `AgentSchema`, `ChatResponse`).
- `src/components`: Componentes de UI reutilizáveis e específicos do negócio (ex: `JsonSchemaEditor`, `Sidebar`).
- `src/pages`: Páginas principais da aplicação (Gestão de Agentes, Chat, Bases de Conhecimento), responsáveis pela composição dos componentes e estado da página.
- `src/UsefulComponents`: Biblioteca de componentes genéricos e utilitários de interface (ex: `SimpleDropdown`, `SimpleSearchBar`).
- `src/App.tsx`: Componente raiz da aplicação. Configura o roteamento global (`@solidjs/router`), define o layout principal (`MainLayout`) e gerencia a estrutura de navegação da SPA (Single Page Application).

---

## Pré-requisitos

Antes de começar, certifique-se de ter as seguintes ferramentas instaladas em sua máquina:

1. **Docker e Docker Compose** (Para rodar o backend e bancos de dados)
   - [Instalar Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac/Linux)
   
2. **Node.js e npm** (Para rodar o frontend localmente)
   - [Instalar Node.js](https://nodejs.org/en/download/) (Recomenda-se a versão LTS)

---

## Instalação e Configuração

### 1. Configuração do Backend

1. Navegue até a pasta `back-end`:
   ```bash
   cd back-end
   ```

2. Crie um arquivo `.env` na pasta `back-end/src` baseado no modelo abaixo. Você precisará de chaves de API para os modelos que deseja utilizar (OpenAI, Anthropic, etc.):

   ```env
   # Configurações de Banco de Dados (Padrão do Docker Compose)
   DATABASE_URL=postgresql+asyncpg://fastapi:fastapi@db:5432/fastapi
   QDRANT_URL=http://qdrant:6333
   
   # Chaves de API (Preencha as que for utilizar)
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-...
   GOOGLE_API_KEY=...
   X_AI_API_KEY=...
   ```

### 2. Configuração do Frontend

1. Navegue até a pasta `front-end`:
   ```bash
   cd front-end
   ```

2. Instale as dependências do projeto:
   ```bash
   npm install
   ```

3. (Opcional) Crie um arquivo `.env` caso precise alterar o endereço da API (padrão é `http://localhost:80`):
   ```env
   VITE_API_HOST=http://localhost:80
   ```

---

## Como Executar o Projeto

### Rodando o Backend (via Docker)

Para iniciar a API, o banco de dados PostgreSQL, o Qdrant e o pgAdmin:

1. Na pasta `back-end`, execute:
   ```bash
   docker compose up --build
   ```

   > **Nota:** Na primeira execução, as migrações do banco de dados podem não rodar automaticamente. Se necessário, abra um novo terminal e execute:
   > ```bash
   > cd back-end
   > docker compose exec api alembic upgrade head
   > ```

O backend estará disponível em `http://localhost:80`.
A documentação da API (Swagger UI) pode ser acessada em `http://localhost:80/docs`.

### Rodando o Frontend (Localmente)

1. Na pasta `front-end`, inicie o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```

2. Acesse a aplicação no navegador através do link exibido no terminal (geralmente `http://localhost:3000`).

---

## Rodando Testes

O `pytest` é utilizado para os testes, localizados no diretório `tests/`.

### Rodar todos os testes

Para executar todos os testes:

```bash
cd back-end
docker compose exec api pytest
```

### Rodar testes específicos

Para executar módulos isolados:

* **Agents**: `docker compose exec api pytest tests/agents/test_agents.py`
* **Chat**: `docker compose exec api pytest tests/chat/test_chats.py`
* **Knowledge Base**: `docker compose exec api pytest tests/knowledge_base/test_knowledge_base.py`
* **Toolsets**: `docker compose exec api pytest tests/toolsets/test_toolsets.py`
* **Copilot**: `docker compose exec api pytest tests/copilot/test_copilot.py`

---

## Licença

Projeto acadêmico para fins educacionais e demonstrativos. Não deve ser usado em produção sem adaptações.  
Este projeto é disponibilizado sob a licença <a href="https://opensource.org/license/MIT" target="_New"><b>**MIT**</b></a>, que permite que qualquer pessoa utilize, copie, modifique e distribua o código.