"""Testes de aceitação T1 a T6 da Sprint 1 do AutoCare.

Execute na raiz do repositório: python -m pytest -q
"""

import sqlite3
from unittest.mock import patch

import pytest
from werkzeug.security import check_password_hash

from app import criar_app


@pytest.fixture
def ambiente(tmp_path):
    # Cada teste utiliza um banco isolado e um relógio controlável.
    relogio = {"agora": 1_700_000_000.0}
    caminho_banco = tmp_path / "autocare_teste.db"
    aplicacao = criar_app({
        "TESTING": True,
        "SECRET_KEY": "chave-apenas-para-testes",
        "DATABASE": str(caminho_banco),
        "NOW_FN": lambda: relogio["agora"],
    })
    return aplicacao.test_client(), caminho_banco, relogio


def cadastrar(cliente, email="motorista@exemplo.com", senha="SenhaSegura123"):
    return cliente.post("/cadastro", json={"email": email, "senha": senha})


def entrar(cliente, email="motorista@exemplo.com", senha="SenhaSegura123"):
    return cliente.post("/login", json={"email": email, "senha": senha})


def test_t1_cadastro_usa_hash_com_salt(ambiente):
    cliente, banco, _ = ambiente
    assert cadastrar(cliente).status_code == 201
    assert cadastrar(cliente, email="outro@exemplo.com").status_code == 201

    with sqlite3.connect(banco) as conexao:
        registros = conexao.execute(
            "SELECT email, senha_hash FROM usuarios ORDER BY id"
        ).fetchall()

    assert len(registros) == 2
    primeiro_hash, segundo_hash = registros[0][1], registros[1][1]
    assert primeiro_hash != "SenhaSegura123"
    assert segundo_hash != "SenhaSegura123"
    assert primeiro_hash != segundo_hash  # Salt aleatório por usuário.
    assert check_password_hash(primeiro_hash, "SenhaSegura123")
    assert check_password_hash(segundo_hash, "SenhaSegura123")


def test_t2_login_valido_cria_sessao(ambiente):
    cliente, _, _ = ambiente
    cadastro = cadastrar(cliente)
    resposta = entrar(cliente)

    assert cadastro.status_code == 201
    assert resposta.status_code == 200
    assert resposta.get_json()["usuario_id"] == cadastro.get_json()["usuario_id"]
    assert cliente.get("/perfil").status_code == 200
    assert cliente.get("/perfil").get_json()["email"] == "motorista@exemplo.com"


def test_t3_senha_errada_retorna_erro_generico(ambiente):
    cliente, _, _ = ambiente
    cadastrar(cliente)
    resposta = entrar(cliente, senha="SenhaErrada123")
    resposta_sem_conta = entrar(cliente, email="inexistente@exemplo.com")

    assert resposta.status_code == 401
    assert resposta_sem_conta.status_code == 401
    assert resposta.get_json() == resposta_sem_conta.get_json()
    assert resposta.get_json() == {"erro": "E-mail ou senha inválidos"}
    assert cliente.get("/perfil").status_code == 401


def test_t4_email_invalido_nao_consulta_banco(ambiente):
    cliente, _, _ = ambiente
    # A aplicação e seu banco já foram inicializados na fixture.
    # Aqui, qualquer acesso ao SQLite indica falha na validação inicial.
    with patch("sqlite3.connect", side_effect=AssertionError("Consultou o banco")):
        for email in ("", "motoristaexemplo.com"):
            resposta = entrar(cliente, email=email)
            assert resposta.status_code == 400
            assert resposta.get_json() == {"erro": "Formato de e-mail inválido"}


def test_t5_tres_erros_bloqueiam_quarta_tentativa_correta(ambiente):
    cliente, banco, relogio = ambiente
    cadastrar(cliente)

    for _ in range(3):
        assert entrar(cliente, senha="SenhaErrada123").status_code == 401

    with sqlite3.connect(banco) as conexao:
        tentativas, bloqueado_ate = conexao.execute(
            "SELECT tentativas, bloqueado_ate FROM usuarios WHERE email = ?",
            ("motorista@exemplo.com",),
        ).fetchone()

    assert tentativas == 3
    assert bloqueado_ate == pytest.approx(relogio["agora"] + 600)

    # A quarta tentativa usa a senha CORRETA e precisa ser recusada.
    assert entrar(cliente).status_code == 423
    assert cliente.get("/perfil").status_code == 401

    # Simula 10 minutos decorridos, sem esperar tempo real.
    relogio["agora"] += 601
    assert entrar(cliente).status_code == 200


def test_t6_senha_curta_rejeitada(ambiente):
    cliente, banco, _ = ambiente
    resposta_curta = cadastrar(cliente, senha="1234567")
    assert resposta_curta.status_code == 400
    assert resposta_curta.get_json() == {
        "erro": "A senha deve conter pelo menos 8 caracteres"
    }

    with sqlite3.connect(banco) as conexao:
        quantidade = conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    assert quantidade == 0

    # O limite é inclusivo: exatamente oito caracteres devem funcionar.
    assert cadastrar(cliente, senha="12345678").status_code == 201
