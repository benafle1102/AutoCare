import os
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from flask import Flask, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash


def email_valido(email):
    return (
        isinstance(email, str)
        and email.count("@") == 1
        and all(email.split("@"))
        and not any(caractere.isspace() for caractere in email)
    )


def criar_app(configuracao_teste=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("AUTOCARE_SECRET_KEY") or secrets.token_hex(32),
        DATABASE=str(Path(app.instance_path) / "autocare.db"),
        NOW_FN=time.time,
    )
    if configuracao_teste:
        app.config.update(configuracao_teste)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    def conectar():
        banco = sqlite3.connect(app.config["DATABASE"])
        banco.row_factory = sqlite3.Row
        return banco

    with closing(conectar()) as banco, banco:
        banco.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                tentativas INTEGER NOT NULL DEFAULT 0,
                bloqueado_ate REAL
            )
        """)

    @app.get("/")
    def inicio():
        return jsonify({"aplicacao": "AutoCare", "mensagem": "API de autenticação ativa"})

    @app.post("/cadastro")
    def cadastro():
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            return jsonify({"erro": "Envie os dados em JSON"}), 400

        email = dados.get("email")
        senha = dados.get("senha")
        if not email_valido(email):
            return jsonify({"erro": "Formato de e-mail inválido"}), 400
        if not isinstance(senha, str) or len(senha) < 8:
            return jsonify({"erro": "A senha deve conter pelo menos 8 caracteres"}), 400

        try:
            with closing(conectar()) as banco, banco:
                cursor = banco.execute(
                    "INSERT INTO usuarios (email, senha_hash) VALUES (?, ?)",
                    (email.lower(), generate_password_hash(senha)),
                )
                usuario_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            return jsonify({"erro": "E-mail já cadastrado"}), 409

        return jsonify({"mensagem": "Conta criada com sucesso", "usuario_id": usuario_id}), 201

    @app.post("/login")
    def login():
        session.clear()
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            return jsonify({"erro": "Envie os dados em JSON"}), 400

        email = dados.get("email")
        senha = dados.get("senha")
        if not email_valido(email):
            return jsonify({"erro": "Formato de e-mail inválido"}), 400

        with closing(conectar()) as banco, banco:
            usuario = banco.execute(
                "SELECT * FROM usuarios WHERE email = ?", (email.lower(),)
            ).fetchone()
            if usuario is None:
                return jsonify({"erro": "E-mail ou senha inválidos"}), 401

            agora = app.config["NOW_FN"]()
            bloqueado_ate = usuario["bloqueado_ate"]
            if bloqueado_ate is not None and agora < bloqueado_ate:
                return jsonify({"erro": "Conta temporariamente bloqueada"}), 423

            tentativas = 0 if bloqueado_ate is not None else usuario["tentativas"]
            if not isinstance(senha, str) or not check_password_hash(usuario["senha_hash"], senha):
                tentativas += 1
                novo_bloqueio = agora + 600 if tentativas >= 3 else None
                banco.execute(
                    "UPDATE usuarios SET tentativas = ?, bloqueado_ate = ? WHERE id = ?",
                    (tentativas, novo_bloqueio, usuario["id"]),
                )
                return jsonify({"erro": "E-mail ou senha inválidos"}), 401

            banco.execute(
                "UPDATE usuarios SET tentativas = 0, bloqueado_ate = NULL WHERE id = ?",
                (usuario["id"],),
            )
            usuario_id = usuario["id"]

        session["usuario_id"] = usuario_id
        return jsonify({"mensagem": "Login realizado com sucesso", "usuario_id": usuario_id}), 200

    @app.get("/perfil")
    def perfil():
        usuario_id = session.get("usuario_id")
        if usuario_id is None:
            return jsonify({"erro": "Acesso não autorizado"}), 401
        with closing(conectar()) as banco:
            usuario = banco.execute(
                "SELECT id, email FROM usuarios WHERE id = ?", (usuario_id,)
            ).fetchone()
        if usuario is None:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        return jsonify({"id": usuario["id"], "email": usuario["email"]})

    return app


app = criar_app()

if __name__ == "__main__":
    app.run(debug=False)
