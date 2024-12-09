from flask import Flask, render_template, request, redirect, session, send_from_directory
from mysql.connector import Error
from config import *
from db_functions import *
import os

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["UPLOAD_FOLDER"] = "uploads/"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session:
        if 'adm' in session:
            return redirect('/adm')
        else:
            return redirect('/empresa')

    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        if not email or not senha:  # Corrigi aqui para verificar ambos os campos corretamente
            erro = "Os campos precisam estar preenchidos!"
            return render_template('login.html', msg_erro=erro)

        if email == MASTER_EMAIL and senha == MASTER_PASSWORD:
            session['adm'] = True
            return redirect('/adm')

        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM empresa WHERE email = %s AND senha = %s'
            cursor.execute(comandoSQL, (email, senha))
            empresa = cursor.fetchone()

            if not empresa:
                return render_template('login.html', msgerro='E-mail e/ou senha estão errados!')

            # Acessar os dados como dicionário
            if empresa['status'] == 'inativa':
                return render_template('login.html', msgerro='Empresa desativada! Procure o administrador!')

            session['idEmpresa'] = empresa['idEmpresa']
            session['nomeEmpresa'] = empresa['nomeEmpresa']
            return redirect('/empresa')
        
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

@app.route('/adm')
def adm():
    if not session:
        return redirect('/login')
    if not 'adm' in session:
        return redirect('/empresa')
  
    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT * FROM Empresa WHERE status = "ativa"'
        cursor.execute(comandoSQL)
        empresas_ativas = cursor.fetchall()

        comandoSQL = 'SELECT * FROM Empresa WHERE status = "inativa"'
        cursor.execute(comandoSQL)
        empresas_inativas = cursor.fetchall()

        return render_template('adm.html', empresas_ativas=empresas_ativas, empresas_inativas=empresas_inativas)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route('/cadastrar_empresa', methods=['GET','POST'])
def cadastrar_empresa():
    if not session:
        return redirect('/login')
    if not session['adm']:
        return redirect('/empresa')

    if request.method == 'GET':
        return render_template('cadastrar_empresa.html')
    if request.method == 'POST':
        nomeEmpresa = request.form['nomeEmpresa']
        cnpj = request.form['cnpj']
        telefone = request.form['telefone']
        email = request.form['email']
        senha = request.form['senha']
        
        if not nomeEmpresa or not cnpj or not telefone or not email or not senha:
            return render_template('cadastrar_empresa.html', msg_erro="Todos os campos são obrigatórios")
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'INSERT INTO empresa (nomeEmpresa,cnpj,telefone,email,senha) VALUES (%s,%s,%s,%s,%s)'
            cursor.execute(comandoSQL, (nomeEmpresa,cnpj,telefone,email,senha))
            conexao.commit()
            return redirect('/adm')
        except Error as erro:
            if erro.errno == 1062:
                return render_template('cadastrar_empresa.html', msg_erro="Esse email ja existe")
            else:
                return f"Erro de BD: {erro}"
        except Exception as erro:
            return f"Erro de BackEnd: {erro}"
        finally:
            encerrar_db(cursor,conexao)
@app.route('/editar_empresa/<int:idEmpresa>', methods=['GET','POST'])
def editar_empresa(idEmpresa):
    if not session:
        return redirect('/login')
    
    if not session['adm']:
        return redirect('/login')
    
    if request.method == 'GET':
        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM empresa WHERE idEmpresa = %s'
            cursor.execute(comandoSQL, (idEmpresa,))
            empresa = cursor.fetchone()
            return render_template('editar_empresa.html',empresa=empresa)
        except Error as erro:
            return f"Erro de BD: {erro}"
        except Exception as erro:
            return f"Erro de BackEnd: {erro}"
        finally:
            encerrar_db(cursor, conexao)
    if request.method == 'POST':
        nomeEmpresa = request.form['nomeEmpresa']
        cnpj = request.form['cnpj']
        telefone = request.form['telefone']
        email = request.form['email']
        senha = request.form['senha']
        
        if not nomeEmpresa or not cnpj or not telefone or not email or not senha:
            return render_template('editar_empresa.html', msg_erro="Todos os campos são obrigatórios")
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = ''' 
            UPDATE empresa
            SET nomeEmpresa=%s, cnpj=%s,telefone=%s, email=%s, senha=%s
            WHERE idEmpresa = %s;
            '''
            cursor.execute(comandoSQL, (nomeEmpresa,cnpj,telefone,email,senha,idEmpresa))
            conexao.commit()
            return redirect('/adm')
        except Error as erro:
            if erro.errno == 1062:
                return render_template('editar_empresa.html', msg_erro="Esse email ja existe")
            else:
                return f"Erro de BD: {erro}"
        except Exception as erro:
            return f"Erro de BackEnd: {erro}"
        finally:
            encerrar_db(cursor,conexao)

@app.route('/status_empresa/<int:idEmpresa>')
def status(idEmpresa):
    if not session:
        return redirect('/login')
    if not session['adm']:
        return redirect('/login')
    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT status FROM empresa WHERE idEmpresa = %s'
        cursor.execute(comandoSQL, (idEmpresa,))
        status_empresa = cursor.fetchone()
        if status_empresa['status'] == 'ativa':
            novo_status = 'inativa'
        else:
            novo_status = 'ativa'
        comandoSQL = 'UPDATE empresa SET status=%s WHERE idEmpresa = %s'
        cursor.execute(comandoSQL, (novo_status, idEmpresa))
        conexao.commit()
        
        if novo_status == 'inativo':
            comandoSQL = 'UPDATE vaga SET status = %s WHERE idEmpresa = %s'
            cursor.execute(comandoSQL, (novo_status, idEmpresa))
            conexao.commit()
        return redirect('/adm')
    except Error as erro:
        return f"Erro de BD: {erro}"
    except Exception as erro:
        return f"Erro de BackEnd: {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route('/excluir_empresa/<int:idEmpresa>')
def excluir_empresa(idEmpresa):
    if not session:
        return redirect('/login')
    if not session['adm']:
        return redirect('/login')
    
    try:
        conexao, cursor = conectar_db()

        comandoSQL = 'DELETE FROM vaga WHERE idEmpresa=%s'
        cursor.execute(comandoSQL, (idEmpresa,))
        conexao.commit()

        comandoSQL = 'DELETE FROM empresa WHERE idEmpresa=%s'
        cursor.execute(comandoSQL, (idEmpresa,))
        conexao.commit()

        return redirect('/adm')
    except Error as erro:
        return f"Erro de BD: {erro}"
    except Exception as erro:
        return f"Erro de BackEnd: {erro}"
    finally:
        encerrar_db(cursor, conexao)
@app.route('/empresa')
def empresa():
    if not session:
        return redirect('/login')
    if 'adm' in session:
        return redirect('/adm')

    idEmpresa = session['idEmpresa']
    nomeEmpresa = session['nomeEmpresa']

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT * FROM vaga WHERE idEmpresa = %s AND status = "ativa" ORDER BY idVaga DESC'
        cursor.execute(comandoSQL, (idEmpresa,))
        vagas_ativas = cursor.fetchall()

        comandoSQL = 'SELECT * FROM vaga WHERE idEmpresa = %s AND status = "inativa" ORDER BY idVaga DESC'
        cursor.execute(comandoSQL, (idEmpresa,))
        vagas_inativas = cursor.fetchall()

        return render_template('empresa.html', nome_empresa=nomeEmpresa, vagas_ativas=vagas_ativas, vagas_inativas=vagas_inativas)         
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route('/')
def index():
    if session:
        if 'adm' in session:
            login = 'adm'
        else:
            login = 'empresa'
    else:
        login = False

    try:
        comandoSQL = '''
        SELECT vaga.*, empresa.nomeEmpresa 
        FROM vaga 
        JOIN empresa ON vaga.idEmpresa = empresa.idEmpresa
        WHERE vaga.status = 'ativa'
        ORDER BY vaga.idVaga DESC;
        '''
        conexao, cursor = conectar_db()
        cursor.execute(comandoSQL)
        vagas = cursor.fetchall()
        return render_template('index.html', vagas=vagas, login=login)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route('/cadastrar_vaga', methods=['POST','GET'])
def cadadastrar_vaga():
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')
    
    if request.method == 'GET':
        return render_template('cadastrar_vaga.html')
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        formato = request.form['formato']
        tipo = request.form['tipo']
        local = ''
        local = request.form['local']
        salario = ''
        salario = request.form['salario']
        idEmpresa = session['idEmpresa']

        if not titulo or not descricao or not formato or not tipo:
            return render_template('cadastrar_vaga.html', msg_erro="Os campos obrigatório precisam estar preenchidos!")
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = '''
            INSERT INTO Vaga (titulo, descricao, formato, tipo, local, salario, idEmpresa)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(comandoSQL, (titulo, descricao, formato, tipo, local, salario, idEmpresa))
            conexao.commit()
            return redirect('/empresa')
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

@app.route('/editar_vaga/<int:idVaga>', methods=['GET','POST'])
def editar_vaga(idVaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    if request.method == 'GET':
        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM vaga WHERE idVaga = %s;'
            cursor.execute(comandoSQL, (idVaga,))
            vaga = cursor.fetchone()
            return render_template('editar_vaga.html', vaga=vaga)
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        formato = request.form['formato']
        tipo = request.form['tipo']
        local = request.form['local']
        salario = request.form['salario']

        if not titulo or not descricao or not formato or not tipo:
            return redirect('/empresa')
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = '''
            UPDATE vaga SET titulo=%s, descricao=%s, formato=%s, tipo=%s, local=%s, salario=%s
            WHERE idVaga = %s;
            '''
            cursor.execute(comandoSQL, (titulo, descricao, formato, tipo, local, salario, idVaga))
            conexao.commit()
            return redirect('/empresa')
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

@app.route("/status_vaga/<int:idVaga>")
def status_vaga(idVaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT status FROM vaga WHERE idVaga = %s;'
        cursor.execute(comandoSQL, (idVaga,))
        vaga = cursor.fetchone()
        if vaga['status'] == 'ativa':
            status = 'inativa'
        else:
            status = 'ativa'

        comandoSQL = 'UPDATE vaga SET status = %s WHERE idVaga = %s'
        cursor.execute(comandoSQL, (status, idVaga))
        conexao.commit()
        return redirect('/empresa')
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route("/excluir_vaga/<int:idVaga>")
def excluir_vaga(idVaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'DELETE FROM vaga WHERE idVaga = %s AND status = "inativa"'
        cursor.execute(comandoSQL, (idVaga,))
        conexao.commit()
        return redirect('/empresa')
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route('/sobre_vaga/<int:idVaga>')
def sobre_vaga(idVaga):
    try:
        comandoSQL = '''
        SELECT vaga.*, empresa.nomeEmpresa 
        FROM vaga 
        JOIN empresa ON vaga.idEmpresa = empresa.idEmpresa 
        WHERE vaga.idVaga = %s;
        '''
        conexao, cursor = conectar_db()
        cursor.execute(comandoSQL, (idVaga,))
        vaga = cursor.fetchone()
        
        if not vaga:
            return redirect('/')
        
        return render_template('sobre_vaga.html', vaga=vaga)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)    
    
@app.route('/candidatar/<int:idVaga>', methods=['GET','POST'])
def candidatar(idVaga):
    if request.method == 'GET':
        return render_template('candidatar.html', idVaga=idVaga)

    if request.method == 'POST':
        nomeCandidato = request.form['nomeCandidato']
        emailCandidato = request.form['emailCandidato']
        telefoneCandidato = request.form['telefoneCandidato']
        curriculo = request.files['curriculo']

        if not nomeCandidato or not emailCandidato or not curriculo.filename or not telefoneCandidato:
            return redirect('/')
        
        try:
            nome_arquivo = f"{idVaga}_{nomeCandidato}_{curriculo.filename}"
            curriculo.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))
            conexao, cursor = conectar_db()
            comandoSQL = '''
            INSERT INTO candidato (nomeCandidato, emailCandidato, telefoneCandidato, curriculo, idVaga)
            VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.execute(comandoSQL, (nomeCandidato, emailCandidato, telefoneCandidato, nome_arquivo, idVaga))
            conexao.commit()
            return redirect('/')
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

@app.route('/curriculos/<int:idVaga>')
def ver_candidatos(idVaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')
    try:
        conexao, cursor = conectar_db()
        comandoSQL = '''
        SELECT * FROM candidato WHERE idVaga = %s
        '''
        cursor.execute(comandoSQL, (idVaga,))
        curriculos = cursor.fetchall()
        return render_template('curriculos.html', curriculos=curriculos)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

# @app.route('/curriculos/<int:idVaga>')
# def ver_candidatos(idVaga):
#     # Verifica se não tem sessão ativa
#     if not session:
#         return redirect('/login')
#     # Verifica se o adm está tentando acessar indevidamente
#     if 'adm' in session:
#         return redirect('/adm')
#     try:
#         conexao, cursor = conectar_db()

#         # Recupera o ID da empresa logada
#         empresa_id = session.get('empresa_id')  # Supondo que o ID está salvo na sessão
#         if not empresa_id:
#             return "Erro: Sessão não possui ID da empresa."

#         # Verifica se a vaga pertence à empresa logada
#         comando_verifica = '''
#         SELECT idEmpresa FROM vaga WHERE idVaga = %s
#         '''
#         cursor.execute(comando_verifica, (idVaga,))
#         resultado = cursor.fetchone()

#         if not resultado:
#             return "Erro: Vaga não encontrada no banco de dados."
        
#         id_empresa_vaga = resultado['idEmpresa']
#         if id_empresa_vaga != empresa_id:
#             return f"Acesso negado: Vaga pertencente à empresa {id_empresa_vaga}, mas sua empresa é {empresa_id}."

#         # Recupera os candidatos apenas se a validação for bem-sucedida
#         comandoSQL = '''
#         SELECT * FROM candidato WHERE idVaga = %s
#         '''
#         cursor.execute(comandoSQL, (idVaga,))
#         curriculos = cursor.fetchall()
#         return render_template('curriculos.html', curriculos=curriculos)
#     except Error as erro:
#         return f"ERRO! Erro de Banco de Dados: {erro}"
#     except Exception as erro:
#         return f"ERRO! Outros erros: {erro}"
#     finally:
#         encerrar_db(cursor, conexao)


@app.route('/procurar_vagas')
def procurar_vagas():
    try:
        word = request.args.get('word')
        comandoSQL = '''
        select vaga.*, empresa.nomeEmpresa
        from vaga
        join empresa on vaga.idEmpresa = empresa.idEmpresa
        where vaga.titulo like %s and vaga.status = 'ativa'
        order by vaga.idVaga desc;
        '''
        conexao, cursor = conectar_db()
        cursor.execute(comandoSQL, (f"%{word}%",))
        vagas_buscadas = cursor.fetchall()
        return render_template('buscar_vaga.html', vagas=vagas_buscadas, word=word)
    except Error as erro:
        return f"ERRO! Erro de banco de dados: {erro}"
    except Exception as erro:
        return f"ERRO! Erro de back-end: {erro}"
    finally:
        encerrar_db(cursor, conexao)
@app.route("/deletar_curriculo/<int:idCandidato>")
def deletar_curriculo(idCandidato):
    try:
        comandoSQL = '''
        select curriculo, idVaga from candidato where idCandidato = %s
        '''
        conexao, cursor = conectar_db()
        cursor.execute(comandoSQL, (idCandidato,))
        candidato_encontrado = cursor.fetchone()
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], candidato_encontrado["curriculo"]))

        comandoSQL = 'delete from candidato where idCandidato = %s '
        cursor.execute(comandoSQL, (idCandidato,))
        conexao.commit()
        return redirect(f"/curriculos/{candidato_encontrado['idVaga']}")
    except Error as erro:
        return f"ERRO! Erro de banco de dados: {erro}"
    except Exception as erro:
        return f"ERRO! Erro de back-end: {erro}"
    finally:
        encerrar_db(cursor, conexao)


@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)