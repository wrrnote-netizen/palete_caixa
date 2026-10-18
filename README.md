# Palete-Caixa 📦

Aplicação web (Streamlit) para resolver o **problema de empacotamento Palete-Caixa**: dado um palete (comprimento × largura) e um ou mais tipos de caixa, encontra via **programação linear inteira** (PuLP/CBC) layouts que maximizam o número de caixas, ou minimizam o espaço livre, sem sobreposição.

Inclui autenticação de usuários (admin e regular), gestão de contas em PostgreSQL e histórico de soluções salvo em pasta local ou no AWS S3.

---

## Funcionalidades

- **Otimização:** informa as dimensões do palete e uma tabela de tipos de caixa (comprimento, largura e quantidade mínima).
  - Função objetivo: *maximizar quantidade de caixas* ou *minimizar espaço livre no palete*.
  - Gera de 1 a 10 soluções distintas (cortes impedem repetir layouts) com tempo limite por solução (5 a 600 s).
  - Mostra a figura com os layouts e permite baixar a imagem.
- **Histórico:** lista as soluções salvas do usuário com metadados, parâmetros e imagem.
- **Usuários (apenas admin):** listar, criar, alterar status, alterar senha e deletar (exclusão lógica).
- **Alterar senha:** disponível para todos os usuários.
- **Login:** senhas com hash `bcrypt`; só entram contas com status `ativo`.

---

## Estrutura do projeto

```
palete_caixa/
├── app.py                    # Ponto de entrada Streamlit: login, menu lateral e roteamento
├── paginas/                  # Páginas da interface
│   ├── login.py              #   tela de login
│   ├── otimizacao.py         #   nova solução + histórico
│   ├── listar_usuarios.py    #   (admin) lista usuários
│   ├── criar_usuario.py      #   (admin) cria usuário
│   ├── alterar_status.py     #   (admin) altera status
│   ├── alterar_senha.py      #   altera a própria senha
│   └── deletar_usuario.py    #   (admin) exclusão lógica
├── otimizacao/
│   └── solver.py             # Modelo PL inteira (PuLP/CBC) e geração de múltiplas soluções
├── graficos/
│   └── plotagem.py           # Figura matplotlib com os layouts do palete
├── utilidades/
│   └── utils.py              # Funções auxiliares do solver, execução com limite de tempo, slug
├── banco_dados/
│   └── db.py                 # Conexão SQLAlchemy/PostgreSQL e operações da tabela de usuários
├── armazenamento/
│   ├── backend.py            # Escolhe local ou S3 conforme ARMAZENAMENTO
│   ├── local.py              # Salva soluções em pasta local
│   └── s3.py                 # Salva soluções em bucket AWS S3 (boto3)
├── src/palete_caixa/         # Pacote Python do projeto (entry point do pyproject)
├── db_palete_caixa.env       # Variáveis de ambiente (NÃO versionado)
├── pyproject.toml / uv.lock  # Dependências gerenciadas com uv
└── *.md                      # Guias: PostgreSQL, AWS e deploy
```

### Como os módulos se conectam

`app.py` → `paginas/*` → `banco_dados/db.py` (usuários) e `otimizacao/solver.py` (cálculo) → `graficos/plotagem.py` (imagem). O módulo `armazenamento/backend.py` seleciona `local.py` ou `s3.py` e expõe a mesma interface: `salvar_solucao`, `listar_solucoes`, `baixar_imagem` e `baixar_metadata`.

---

## Requisitos

- Python 3.14 (ver `.python-version`)
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL (local, RDS ou outro provedor)
- Conta AWS com bucket S3 (apenas se `ARMAZENAMENTO=s3`)

---

## Como executar

1. Instale as dependências:

   ```bash
   uv sync
   ```

2. Crie o banco e as tabelas `tipos_status`, `tipos_usuarios` e `clientes` seguindo o guia [Comandos Básicos do PostgreSQL](#comandos-básicos-do-postgresql). Crie também ao menos um usuário com `tipo = 'admin'`.

3. Crie o arquivo `db_palete_caixa.env` na raiz (veja a seção seguinte).

4. Inicie a aplicação:

   ```bash
   uv run streamlit run app.py
   ```

   A aplicação abre em `http://localhost:8501`.

---

## Variáveis de ambiente

Definidas em `db_palete_caixa.env` (ou no painel do provedor, em produção):

| Variável | Descrição | Padrão |
|---|---|---|
| `HOST` | Host do PostgreSQL | — |
| `DB_PORT` | Porta do PostgreSQL | — |
| `USER` | Usuário do banco | — |
| `PASS` | Senha do banco | — |
| `DATABASE` | Nome do banco | — |
| `ARMAZENAMENTO` | `local` ou `s3` | `local` |
| `ARMAZENAMENTO_DIR` | Pasta das soluções (modo `local`) | `solucoes_salvas` |
| `S3_BUCKET` | Bucket S3 (modo `s3`) | `palete-caixa-solucoes` |
| `REGION` | Região AWS do bucket | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | Chave de acesso (modo `s3`) | — |
| `AWS_SECRET_ACCESS_KEY` | Chave secreta (modo `s3`) | — |

> O arquivo `.env` contém segredos e está no `.gitignore`. Nunca o versione.

---

## Documentação complementar

Os guias abaixo estão no final deste README:

- [Comandos Básicos do PostgreSQL](#comandos-básicos-do-postgresql): instalação do PostgreSQL, comandos SQL e criação das tabelas.
- [Guia Completo de Configuração AWS](#guia-completo-de-configuração-aws): conta AWS, usuário IAM, S3 e RDS.
- [Guia: GitHub + DigitalOcean App Platform](#guia-github--digitalocean-app-platform): GitHub e deploy no App Platform da DigitalOcean.

---

## Tecnologias

Streamlit · PuLP (CBC) · SQLAlchemy + psycopg2 · bcrypt · boto3 · pandas · numpy · matplotlib · python-dotenv


---

## Comandos Básicos do PostgreSQL

Os comandos do PostgreSQL dividem-se principalmente entre comandos do terminal interativo (**psql**) e comandos da linguagem **SQL** (estruturados em DDL e DML).

---

### Instalando o PostgreSQL pela Linha de Comando

#### Windows (PowerShell)

* **Usando o winget** (já incluso no Windows 10/11) — instala o PostgreSQL 18:
  ```powershell
  winget install PostgreSQL.PostgreSQL.18 --override "--mode unattended --superpassword 123 --serverport 5432"
  ```
  O usuário `postgres` é criado com a senha `123` (apenas para facilitar o curso; não use em produção). Para digitar a senha no assistente gráfico, use `--interactive` no lugar de `--override`.

* **Adicionando a pasta `bin` ao `PATH` do sistema**. Abra o PowerShell **como Administrador** para alterar o PATH da máquina:
  ```powershell
  [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "Machine") + ";C:\Program Files\PostgreSQL\18\bin", "Machine")
  ```

* Após adicionar ao `PATH`, feche e reabra o PowerShell para que as alterações tenham efeito. Verifique a instalação com:
  ```powershell
  psql --version
  ```
#### macOS (Terminal)

* **Baixando e abrindo o instalador gráfico da EDB** — cria a pasta de instalação, baixa o `.dmg`, monta a imagem e abre o assistente:
  ```bash
  sudo mkdir -p /Library/PostgreSQL/18 && sudo chmod 755 /Library/PostgreSQL/18 && curl -fL -o ~/Downloads/postgresql-18-osx.dmg https://get.enterprisedb.com/postgresql/postgresql-18.0-1-osx.dmg && hdiutil attach ~/Downloads/postgresql-18-osx.dmg -quiet && open /Volumes/PostgreSQL*/*.app
  ```
  No assistente, informe `/Library/PostgreSQL/18` como diretório de instalação, defina a senha do usuário `postgres` (ex.: `123`, apenas para facilitar o curso; não use em produção) e mantenha a porta `5432`.
* **Adicionando a pasta `bin` ao `PATH`** (zsh, padrão do macOS):
  ```bash
  echo 'export PATH="/Library/PostgreSQL/18/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
  ```
* Verifique a instalação:
  ```bash
  psql --version
  ```
---

### Comandos SQL (DDL - Definição de Dados)

Utilizados para criar, alterar ou apagar a estrutura dos objetos do banco:

* **`CREATE DATABASE`** — Cria um novo banco de dados:
  ```sql
  CREATE DATABASE meu_banco;
  ```
  * **Criando o database pelo pgAdmin 4 (interface gráfica):**
    1. Abra o **pgAdmin 4** e informe a senha mestre, se solicitada.
    2. No painel esquerdo (*Object Explorer*), expanda **Servers** e conecte-se ao servidor (ex.: **PostgreSQL 18**), informando a senha `123`.
    3. Clique com o botão direito em **Databases** → **Create** → **Database...**.
    4. Na aba **General**, preencha o campo **Database** com o nome (ex.: `db_palete_caixa`) e mantenha **Owner** como `postgres`.
    5. Clique em **Save**. O novo banco aparecerá em **Databases**.
  * **Abrindo um editor de script (Query Tool) para rodar comandos:**
    1. No **Object Explorer**, clique com o botão direito no database desejado (ex.: `db_palete_caixa`).
    2. Selecione **Query Tool** (ou clique no banco e use o atalho `Alt + Shift + Q`).
    3. Digite o script SQL no editor, por exemplo:
       ```sql
       CREATE TABLE teste (id SERIAL PRIMARY KEY, nome VARCHAR(50));
       SELECT * FROM teste;
       ```
    4. Execute com o botão **Execute/Refresh** (ícone ▶) ou pela tecla `F5`. O resultado aparece no painel **Data Output** abaixo do editor.
* **`CREATE TABLE`** — Cria uma nova tabela:
  ```sql
  CREATE TABLE clientes (
      id SERIAL PRIMARY KEY,
      nome VARCHAR(100) NOT NULL,
      idade INT
  );
  ```
* **`DROP TABLE`** — Exclui uma tabela e todos os seus dados.

---

### Comandos SQL (DML / DQL - Manipulação e Consulta de Dados)

Utilizados para inserir, atualizar, consultar e remover registros:

* **`INSERT INTO`** — Adiciona novos registros a uma tabela:
  ```sql
  INSERT INTO clientes (nome, idade) VALUES ('Maria Silva', 30);
  ```
* **`SELECT`** — Consulta e recupera dados de uma ou mais tabelas:
  ```sql
  SELECT * FROM clientes;
  ```
* **`UPDATE`** — Atualiza registros existentes em uma tabela:
  ```sql
  UPDATE clientes SET idade = 31 WHERE nome = 'Maria Silva';
  ```
* **`DELETE`** — Remove registros de uma tabela:
  ```sql
  DELETE FROM clientes WHERE idade < 18;
  ```

* **COMANDOS PARA CRIAR TABELAS E INSERIR DADOS INICIAIS PARA O BANCO `db_palete_caixa`**
  ```sql
  -- CRIANDO A TABELA tipos_status
  CREATE TABLE IF NOT EXISTS tipos_status (
      id SERIAL PRIMARY KEY,
      nome_status VARCHAR(30) NOT NULL UNIQUE,
    descricao VARCHAR(255) NOT NULL UNIQUE
  );

  -- CRIANDO A TABELA tipos_usuarios
  CREATE TABLE IF NOT EXISTS tipos_usuarios (
      id SERIAL PRIMARY KEY,
      tipo VARCHAR(30) NOT NULL UNIQUE
  );

  -- CRIANDO A TABELA clientes
  CREATE TABLE IF NOT EXISTS clientes (
      id                SERIAL PRIMARY KEY,
      cnpj              VARCHAR(14) NOT NULL UNIQUE,
      razao_social      VARCHAR(255) NOT NULL,
      nome_fantasia     VARCHAR(255),
      nome_contato      VARCHAR(255),
      telefone_contato  VARCHAR(20),
      email_contato     VARCHAR(255),
      nome_usuario      VARCHAR(50)  NOT NULL UNIQUE,
      senha_hash        VARCHAR(255) NOT NULL,
      status            VARCHAR(30)  NOT NULL DEFAULT 'ativo',
      tipo              VARCHAR(30)  NOT NULL DEFAULT 'regular',
      data_criacao      TIMESTAMP    NOT NULL DEFAULT NOW(),
      deletado          BOOLEAN      NOT NULL DEFAULT FALSE,
      deletado_em       TIMESTAMP
  );


  -- COMANDO PARA CRIAR OS VALORES INICIAIS DA TABELA tipos_status
  INSERT INTO tipos_status (nome_status, descricao)
  VALUES ('ativo', 'Usuário ativo'), 
        ('inativo', 'Usuário inativo'), 
      ('suspenso', 'Usuário suspenso')
  ON CONFLICT (nome_status) DO NOTHING;

  -- COMANDO PARA CRIAR OS VALORES INICIAIS DA TABELA tipos_usuarios
  INSERT INTO tipos_usuarios (tipo)
  VALUES ('admin'), 
        ('regular')
  ON CONFLICT (tipo) DO NOTHING;

  -- COMANDO PARA CRIAR O USUÁRIO MESTRE DO APP (senha = 123456) NA TABELA clientes
  INSERT INTO clientes (cnpj, razao_social, nome_contato, nome_usuario,
                          senha_hash, tipo)
  VALUES ('12345678000190', 'Prandiano', 'Ricieri', 'prandiano',
          '$2b$12$r7b/P04Eq0E3AXJ6NNiPS.i9AgXuf15QKJbBMne.sQVN0GaVa0HiG', 'admin');
  ```
---

### Exportando um Banco Local e Subindo para um Banco Remoto na AWS (Windows e Mac)

#### 1. Exportar as tabelas do banco local para um arquivo

  ```bash
  pg_dump -U postgres -h localhost -d db_palete_caixa -Fc --no-owner --no-privileges -f backup.dump
  ```

  A senha do banco de dados local é `123`

#### 2. Subir o arquivo para o banco remoto na AWS (RDS)

Substitua `ENDPOINT_RDS` pelo endpoint da instância (ex.: `meu-db.xxxxxx.us-east-1.rds.amazonaws.com`).

  ```bash
  pg_restore -h ENDPOINT_RDS -p 5432 -U postgres -d db_palete_caixa --no-owner --no-privileges backup.dump
  ```

  A senha do banco de dados remoto na AWS é `palete_caixa_mmap3`


---

## Guia Completo de Configuração AWS

---

### 1. Criar uma conta AWS

1. Acesse [aws.amazon.com](https://aws.amazon.com) → **Create an AWS Account**
2. Preencha e-mail, nome da conta e senha

   ### 2.1 Verificação de e-mail
   Você receberá um e-mail de verificação. Consulte a caixa de entrada.
   Se tiver um código de verificação, insira-o para continuar. Se mostrar
   que este e-mail já está em uso, recomendo usar outro e-mail.

3. Escolha plano **Free** (gratuito)
4. Preencha os dados pessoais (nome, endereço, telefone ...)
5. Informe dados de cartão de crédito (obrigatório, mas não será cobrado no free tier)
6. Confirme a identidade por telefone (código SMS)
7. Após o cadastro, acesse o **Console AWS** com o e-mail de root

   ### 7.1 Avaliação final da gratuidade
   Se a amazon não conceder os créditos gratuitos, selecione a caixa para permitir cobrança.

8. Selecionar o plano de suporte (Basic é gratuito) → **Conclua a inscrição**
---

### 2. Criar um usuário IAM

1. No console, pesquise por **IAM** na barra de busca e acesse
2. No menu lateral → **Usuários do IAM** → **Criar usuário**
3. Defina um nome (ex: `palete-caixa-user`) → **Next**
4. Em **Opções de permissões**, selecione **Anexar políticas diretamente**
5. Adicione as políticas:
   - `AmazonS3FullAccess`
   - `AmazonRDSFullAccess`
6. Clique em **Próximo** → **Criar usuário**

#### Gerar as Access Keys

1. Clique no usuário recém-criado → aba **Credenciais de segurança**
2. Role até **Chaves de acesso** → **Criar chave de acesso**
3. Selecione **Interface de linha de comando (CLI)** → **Confirmação** → **Próximo**
4. A etiqueta de descrição é opcional, deixar em branco.
5. **Copie e salve** o `Access key ID` e o `Secret access key` — eles aparecem apenas uma vez

---

### 3. Configurar a Security Group

1. Pesquise por **VPC**
2. No menu lateral da VPC → **Grupos de Segurança** → **Criar grupo de segurança**
3. Preencha:
   - **Nome do grupo de segurança:** `palete-caixa-sg`
   - **Descrição:** `Acesso remoto PostgreSQL`
   - **VPC:** selecione a VPC padrão
3. Em **Regras de entrada** → **Adicionar regra**:

   | Campo | Valor |
   |---|---|
   | **Tipo** | `PostgreSQL` |
   | **Protocolo** | `TCP` (preenchido automaticamente) |
   | **Intervalo de portas** | `5432` (preenchido automaticamente) |
   | **Origem** | `Personalizado` → `0.0.0.0/0` |
   | **Descrição** | `Acesso remoto para desenvolvimento` |

4. Clique em **Criar grupo de segurança**

> **Atenção:** `0.0.0.0/0` permite acesso de qualquer IP. É funcional para desenvolvimento, mas para produção recomenda-se restringir aos IPs reais.

---

### 4. Criar um bucket S3

1. No console, pesquise por **S3** → **Criar bucket**
2. Preencha:
   - **Nome do bucket:** `palete-caixa-seu-nome` (deve ser único no mundo)
   - **Região AWS:** `US East (Ohio) us-east-2`
3. Marque a opção **Namespace regional da conta (recomendado)**
4. Em **Configurações de bloqueio de acesso público**: mantenha **tudo bloqueado** (padrão)
5. Deixe as demais opções padrão → **Criar bucket**

---

### 5. Criar banco de dados PostgreSQL no RDS

#### 5.1 Acessar o RDS

1. Pesquise por **RDS**
2. No menu lateral → **Bancos de dados** → **Criar banco de dados**

#### 5.2 Configuração completa

**Tipo de mecanismo:**
- **Tipo de mecanismo:** `PostgreSQL`
- **Escolher método de criação:** `Configuração completa`
- **Modelos:** `Sandbox` (para testes) ou `Production` (para produção)
- **Identificador da instância:** `palete-caixa`
- **Gerenciamento de credenciais:** `Autogerenciada` → defina uma senha fixa (ex: `palete_caixa_mmap3`) e confirme
- **Configurações adicionais de credenciais:** `Autenticação de senha` (padrão)
- **Tipo de instância:** `db.t4g.micro` (free tier)

**Armazenamento:**
- **Tipo de armazenamento:** `gp2`
- **Armazenamento alocado:** `20 GB`
- Desmarque **Habilitar escalonamento automático de armazenamento**

**Conectividade:**
- **Compute resource:** `Não se conectar a um recurso de computação do EC2`
- **Virtual private cloud (VPC):** selecione a VPC padrão
- **Acesso Público:** `Sim` ← **obrigatório para acesso remoto**
- **Grupos de segurança da VPC existentes:** selecione **Selecionar existente** → selecione `palete-caixa-sg` (criado no passo 3) e `default`
- **Zona de disponibilidade:** `Sem preferência`
- **Porta do banco de dados:** `5432`

**Configuração adicional:**
- **Nome do banco de dados inicial:** `db_palete_caixa`
- Desmarque `Habilitar backups automáticos`

Por fim → **Criar banco de dados**

#### 5.3 Obter o Endpoint

Após a criação (leva ~5 minutos, status muda para `Available`):

1. Clique no banco criado → aba **Segurança e Conexão**
2. Copie o **Endpoint**, que terá o formato:
   ```
   database-1.xxxxxxxxxxxx.us-east-2.rds.amazonaws.com
   ```

#### 5.4 Testar a conexão

Abrir o pgAdmin4 e clicar com o botão direito em **Servers** → **Create** → **Server**
- **General**
  - **Name:** `aws`
- **Connection**
  - **Host name/address:** `database-1.xxxxxxxxxxxx.us-east-2.rds.amazonaws.com`
  - **Port:** `5432`
  - **Maintenance database:** `db_palete_caixa`
  - **Username:** `postgres`
  - **Password:** `palete_caixa_mmap3`

Executar os comandos para criar as tabelas no banco de dados `db_palete_caixa` e os dados iniciais destas tabelas.

  ```sql
  -- CRIANDO A TABELA tipos_status
  CREATE TABLE IF NOT EXISTS tipos_status (
      id SERIAL PRIMARY KEY,
      nome_status VARCHAR(30) NOT NULL UNIQUE,
    descricao VARCHAR(255) NOT NULL UNIQUE
  );

  -- CRIANDO A TABELA tipos_usuarios
  CREATE TABLE IF NOT EXISTS tipos_usuarios (
      id SERIAL PRIMARY KEY,
      tipo VARCHAR(30) NOT NULL UNIQUE
  );

  -- CRIANDO A TABELA clientes
  CREATE TABLE IF NOT EXISTS clientes (
      id                SERIAL PRIMARY KEY,
      cnpj              VARCHAR(14) NOT NULL UNIQUE,
      razao_social      VARCHAR(255) NOT NULL,
      nome_fantasia     VARCHAR(255),
      nome_contato      VARCHAR(255),
      telefone_contato  VARCHAR(20),
      email_contato     VARCHAR(255),
      nome_usuario      VARCHAR(50)  NOT NULL UNIQUE,
      senha_hash        VARCHAR(255) NOT NULL,
      status            VARCHAR(30)  NOT NULL DEFAULT 'ativo',
      tipo              VARCHAR(30)  NOT NULL DEFAULT 'regular',
      data_criacao      TIMESTAMP    NOT NULL DEFAULT NOW(),
      deletado          BOOLEAN      NOT NULL DEFAULT FALSE,
      deletado_em       TIMESTAMP
  );


  -- COMANDO PARA CRIAR OS VALORES INICIAIS DA TABELA tipos_status
  INSERT INTO tipos_status (nome_status, descricao)
  VALUES ('ativo', 'Usuário ativo'), 
        ('inativo', 'Usuário inativo'), 
      ('suspenso', 'Usuário suspenso')
  ON CONFLICT (nome_status) DO NOTHING;

  -- COMANDO PARA CRIAR OS VALORES INICIAIS DA TABELA tipos_usuarios
  INSERT INTO tipos_usuarios (tipo)
  VALUES ('admin'), 
        ('regular')
  ON CONFLICT (tipo) DO NOTHING;

  -- COMANDO PARA CRIAR O USUÁRIO MESTRE DO APP (senha = 123456) NA TABELA clientes
  INSERT INTO clientes (cnpj, razao_social, nome_contato, nome_usuario,
                          senha_hash, tipo)
  VALUES ('12345678000190', 'Prandiano', 'Ricieri', 'prandiano',
          '$2b$12$r7b/P04Eq0E3AXJ6NNiPS.i9AgXuf15QKJbBMne.sQVN0GaVa0HiG', 'admin');
  ```
---

### Resumo das variáveis de ambiente resultantes

```
HOST=database-1.xxxxxxxxxxxx.us-east-2.rds.amazonaws.com
DB_PORT=5432
USER=postgres
PASS=palete_caixa_mmap3
DATABASE=db_palete_caixa
REGION=us-east-2
AWS_S3_BUCKET=palete-caixa-seu-nome
AWS_REGION=us-east-2
AWS_ACCESS_KEY_ID=SEU_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=SEU_SECRET_ACCESS_KEY
```


---

## Guia: GitHub + DigitalOcean App Platform

Passo a passo para subir o projeto no GitHub e publicá-lo como app (Streamlit) no App Platform da DigitalOcean, na configuração mais barata.

---

### 1. Preparar o projeto

#### 1.1 Nunca versionar segredos

O arquivo `db_palete_caixa.env` contém senhas e chaves AWS. O `.gitignore` já ignora `*.env`.

Recomendado: trocar `psycopg2` por `psycopg2-binary` (evita compilar o driver no build, que exigiria bibliotecas do PostgreSQL).

```bash
uv remove psycopg2
uv add psycopg2-binary
```

#### 1.2 Versão do Python

O projeto usa Python 3.14 (`.python-version`), suportado pelo buildpack (3.14.0 a 3.14.3 na stack Ubuntu-22). Se o build reclamar da versão, ajuste o `.python-version` e o `requires-python` do `pyproject.toml` para uma versão suportada (ex.: `3.13`) e rode `uv lock` de novo.

---

### 2. Subir para o GitHub

O repositório remoto já está configurado (`origin` → `https://github.com/jasenovski/palete-caixa.git`). Caso precise criar do zero:

1. Em [github.com/new](https://github.com/new) crie o repositório (ex.: `palete-caixa`), pode ser **Privado**.
2. No terminal, na pasta do projeto:

```bash
git init                                  # só se ainda não for um repositório
git status                                # confira que NÃO aparece nenhum .env
git add .                                 # se tiver mudanças importantes, adicione ao commit
git commit -m "Preparar deploy"           # cria o commit com as mudanças adicionadas
git branch -M main                        # renomeia a branch atual para main
git remote add origin https://github.com/SEU_USUARIO/palete-caixa.git   # só se não existir o remoto
git push -u origin main                   # envia o commit para o repositório remoto
```

Se o push pedir senha, use um **Personal Access Token** (GitHub → Settings → Developer settings → Personal access tokens) no lugar da senha.

---

### 3. Criar conta e app na DigitalOcean

1. Crie a conta em [digitalocean.com](https://www.digitalocean.com) e adicione uma forma de pagamento.
2. No painel, na parte superior **Create** → **App Platform**.
3. **Source:** escolha **GitHub** → autorize a DigitalOcean a acessar o repositório (pode limitar apenas ao `palete-caixa`).
4. Selecione:
   - **Repository:** `palete-caixa`
   - **Branch:** `main`
   - **Source Directory:**
   - **Autodeploy:** marcado (novo `push` na `main` = novo deploy)
5. **Next**. A DigitalOcean detecta Python e cria um **Web Service**.

---

### 4. Configurar o serviço (mais barato)

Na tela de recursos, clique em **Edit** no serviço:

| Campo | Valor |
|---|---|
| **Tipo** | `Web Service` |
| **Build Command** | *(vazio, padrão)* |
| **Run Command** | `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true` |
| **HTTP Port** | `8080` |
| **Instâncias** | `1` |
| **Plano** | `Shared` → **Basic** → menor opção (512 MB RAM / 1 vCPU compartilhada, ~US$ 5/mês) |

> Não habilite autoscaling (exige planos dedicados, mais caros).
> Confira o preço atual na tela de criação; ele pode mudar.
> Se o app ficar sem memória (reinícios, erros OOM) por causa de pandas/matplotlib/Streamlit, suba para o plano de 1 GB.

**Região:** escolha a mais próxima de você / do banco (ex.: `NYC`). Ela não precisa ser a mesma da AWS, mas a latência com o RDS será maior fora dos EUA.

---

### 5. Criar as variáveis de ambiente

Ainda em **Edit** do serviço → seção **Environment Variables** (nível do componente) → **Edit** / **Add Variable**.

Use as mesmas chaves de ambiente definidas no arquivo `.env` (`db_palete_caixa.env`).

| Variável | Valor | Encrypt |
|---|---|---|
| `HOST` | endpoint do RDS (`xxx.us-east-2.rds.amazonaws.com`) | não |
| `DB_PORT` | `5432` | não |
| `USER` | `postgres` | não |
| `PASS` | `palete_caixa_mmap3` | **sim** |
| `DATABASE` | `db_palete_caixa` | não |
| `ARMAZENAMENTO` | `s3` | não |
| `S3_BUCKET` | `palete-caixa-solucoes` | não |
| `REGION` | `us-east-2` | não |
| `AWS_ACCESS_KEY_ID` | chave do usuário IAM | **sim** |
| `AWS_SECRET_ACCESS_KEY` | chave secreta do usuário IAM | **sim** |

---

### 6. Finalizar e publicar

1. **Next** → confira o nome do app e a região.
2. Em **Review**, verifique o custo estimado (deve mostrar ~US$ 5/mês para um único serviço Basic).
3. Clique em **Create App**.
4. Acompanhe o build em **Activity / Deployments**. Ao terminar, o status fica **Deployed**.
5. Acesse a URL gerada (`https://nome-do-app-xxxxx.ondigitalocean.app`).

---

### 7. Atualizações e manutenção

- **Novo deploy:** basta `git push origin main` (autodeploy).
- **Alterar variáveis:** App → **Settings** → componente → **Environment Variables** → salve (gera novo deploy).
- **Logs:** aba **Runtime Logs** (erros de execução) e **Build Logs** (erros de instalação).
- **Reduzir custo:** se não precisar do app no ar, pode **destruir** o app em Settings → *Destroy App*. A cobrança é proporcional ao tempo de uso.

---

### 8. Problemas comuns

| Sintoma | Causa provável / solução |
|---|---|
| Build falha instalando pacote | Versão do Python incompatível ou pacote sem wheel; ajuste `.python-version`/`pyproject.toml` e rode `uv lock` |
| Deploy falha com *health check* | Run Command sem `--server.port=$PORT` / `--server.address=0.0.0.0` ou porta HTTP errada |
| `connection timed out` no banco | Security Group do RDS sem liberar porta 5432, ou RDS sem acesso público |
| `password authentication failed` | `USER`/`PASS` incorretos nas variáveis |
| Erro de acesso ao S3 | Chaves/`REGION`/`S3_BUCKET` incorretos ou política IAM sem acesso ao bucket |
| App reinicia sozinho | Falta de memória; use plano de 1 GB |
