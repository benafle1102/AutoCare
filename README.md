# AutoCare

**Seu carro em dia, sem surpresas.**

O AutoCare é um sistema inteligente de manutenção veicular, desenvolvido para ajudar motoristas a gerenciar veículos, registrar serviços, controlar despesas e acompanhar manutenções preventivas.

## Sprint 1 — Cadastro e autenticação

Nesta primeira entrega, foi implementada uma API de autenticação com:

- Cadastro de usuários com e-mail e senha.
- Armazenamento seguro de senhas usando hash com salt.
- Login com identificação de usuário por sessão.
- Mensagem genérica para credenciais incorretas.
- Validação de e-mail antes de consultar o banco de dados.
- Bloqueio por 10 minutos após três senhas incorretas.
- Validação de senha com no mínimo 8 caracteres.

As funcionalidades de veículos, despesas e alertas estão planejadas para entregas futuras.

## Equipe

**Integrante:** Benafle Soares da Hora

**GitHub:** @benafle1102

**Papéis:** Product Owner (PO), Scrum Master (SM) e Desenvolvedor.

**Professor:** Rafael (@rafsp).

## Tecnologias utilizadas

- Python
- Flask
- SQLite
- pytest
- GitHub Actions

## Como executar o projeto

É necessário ter o Python 3.10 ou superior instalado.

Clone o repositório:

```bash
git clone https://github.com/benafle1102/AutoCare.git
cd AutoCare
```

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

Execute a aplicação:

```bash
python app.py
```

A API estará disponível em:

http://127.0.0.1:5000

## Funcionalidades da API

| Método | Rota | Descrição |
|---|---|---|
| GET | / | Verifica se a API está ativa |
| POST | /cadastro | Cadastra um usuário |
| POST | /login | Autentica um usuário |
| GET | /perfil | Consulta o perfil autenticado |

Os endpoints de cadastro e login recebem JSON com os campos `email` e `senha`.

## Como executar os testes

Na pasta principal do projeto, execute:

```bash
python -m pytest -q
```

O comando executa os seis testes automatizados:

- T1: Cadastro com senha protegida.
- T2: Login com credenciais corretas.
- T3: Rejeição de senha incorreta.
- T4: Validação de e-mail antes do banco.
- T5: Bloqueio após três tentativas incorretas.
- T6: Rejeição de senha com menos de oito caracteres.

Os testes também são executados automaticamente pelo GitHub Actions.

## Planejamento

As histórias de usuário estão registradas nas Issues #1 a #6.

O objetivo da Sprint 1 está na Issue #7.

O acompanhamento das tarefas é realizado no GitHub Projects, utilizando um quadro Kanban com limites de trabalho em andamento.

## Próximas funcionalidades

- Cadastro de veículos.
- Histórico de manutenções.
- Controle de despesas.
- Alertas preventivos por data e quilometragem.
