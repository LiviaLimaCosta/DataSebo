import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import requests
import sqlite3

def inicializar_bd():
    conn = sqlite3.connect('livros.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS livros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn TEXT,
        nome TEXT NOT NULL,
        autor TEXT,
        preco REAL,
        quantidade INTEGER
    )
    ''')
    conn.commit()
    conn.close()

def salvar_livro():
    isbn = entry_isbn.get()
    nome = entry_nome.get()
    autor = entry_autor.get()
    preco = entry_preco.get()
    quantidade = entry_quantidade.get()

    if not nome:
        messagebox.showerror("Erro", "Por favor, insira o nome do livro.")
        return

    conn = sqlite3.connect('livros.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, quantidade FROM livros WHERE isbn=? OR (nome=? AND autor=?)', (isbn, nome, autor))
    livro = cursor.fetchone()

    if livro:
        cursor.execute('UPDATE livros SET quantidade = quantidade + ? WHERE id = ?', (quantidade if quantidade else 1, livro[0]))
    else:
        cursor.execute('''
        INSERT INTO livros (isbn, nome, autor, preco, quantidade) VALUES (?, ?, ?, ?, ?)
        ''', (isbn, nome, autor, preco if preco else None, quantidade if quantidade else 1))

    conn.commit()
    conn.close()
    limpar_campos()
    entry_busca.delete(0, tk.END)
    label_status.config(text="Livro adicionado com sucesso!")
    atualizar_tabela()

def editar_livro():
    selected_item = table.selection()
    if not selected_item:
        messagebox.showerror("Erro", "Selecione um livro para editar.")
        return

    item_id = table.item(selected_item)['values'][0]

    conn = sqlite3.connect('livros.db')
    cursor = conn.cursor()

    # Buscar os dados atuais do livro
    cursor.execute('SELECT * FROM livros WHERE id = ?', (item_id,))
    livro_atual = cursor.fetchone()

    # Obter os novos valores dos campos
    isbn_novo = entry_isbn.get()
    nome_novo = entry_nome.get()
    autor_novo = entry_autor.get()
    preco_novo = entry_preco.get()
    quantidade_novo = entry_quantidade.get()

    # Verificar quais campos foram preenchidos e atualizar apenas esses campos no banco de dados
    atualizacoes = {}
    if isbn_novo and isbn_novo != livro_atual[1]:
        atualizacoes['isbn'] = isbn_novo
    if nome_novo and nome_novo != livro_atual[2]:
        atualizacoes['nome'] = nome_novo
    if autor_novo and autor_novo != livro_atual[3]:
        atualizacoes['autor'] = autor_novo
    if preco_novo and preco_novo != livro_atual[4]:
        atualizacoes['preco'] = preco_novo
    if quantidade_novo and quantidade_novo != livro_atual[5]:
        atualizacoes['quantidade'] = quantidade_novo

    # Gerar a string de atualização dinamicamente
    if atualizacoes:
        set_string = ', '.join([f"{key} = ?" for key in atualizacoes.keys()])
        values = tuple(atualizacoes.values())
        query = f'''
        UPDATE livros
        SET {set_string}
        WHERE id = ?
        '''
        # Adicionar o ID do livro ao final da tupla de valores
        values += (item_id,)
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        limpar_campos()
        entry_busca.delete(0, tk.END)
        label_status.config(text="Livro editado com sucesso!")
        atualizar_tabela()
    else:
        messagebox.showinfo("Informação", "Nenhum campo foi alterado.")


def deletar_livro():
    selected_item = table.selection()
    if not selected_item:
        messagebox.showerror("Erro", "Selecione um livro para deletar.")
        return

    item_id = table.item(selected_item)['values'][0]

    conn = sqlite3.connect('livros.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM livros WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    limpar_campos()
    entry_busca.delete(0, tk.END)
    label_status.config(text="Livro deletado com sucesso!")
    atualizar_tabela()

def buscar_livro():
    query = entry_busca.get()

    if not query:
        messagebox.showerror("Erro", "Digite um ISBN ou nome de livro para buscar.")
        return

    try:
        response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={query}")
        data = response.json()

        if "items" in data:
            item = data["items"][0]
            volume_info = item["volumeInfo"]
            isbn = volume_info.get("industryIdentifiers", [{}])[0].get("identifier", "")
            nome = volume_info.get("title", "")
            autor = volume_info.get("authors", [""])[0]

            entry_isbn.delete(0, tk.END)
            entry_nome.delete(0, tk.END)
            entry_autor.delete(0, tk.END)

            entry_isbn.insert(0, isbn)
            entry_nome.insert(0, nome)
            entry_autor.insert(0, autor)
        else:
            messagebox.showerror("Erro", "Livro não encontrado.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar livro: {str(e)}")

def visualizar_livros():
    atualizar_tabela()

def limpar_campos():
    entry_isbn.delete(0, tk.END)
    entry_nome.delete(0, tk.END)
    entry_autor.delete(0, tk.END)
    entry_preco.delete(0, tk.END)
    entry_quantidade.delete(0, tk.END)

def atualizar_tabela():
    conn = sqlite3.connect('livros.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM livros')
    rows = cursor.fetchall()
    conn.close()

    for row in table.get_children():
        table.delete(row)

    for row in rows:
        table.insert("", "end", values=row)

def abrir_pesquisa(root):
    pesquisa_window = tk.Toplevel(root)
    pesquisa_window.title("Pesquisa de Livros")

    label_pesquisa_termo = tk.Label(pesquisa_window, text="Pesquisar por ISBN ou Nome:")
    label_pesquisa_termo.grid(row=0, column=0, padx=10, pady=5)
    entry_pesquisa = tk.Entry(pesquisa_window)
    entry_pesquisa.grid(row=0, column=1, padx=10, pady=5)

    button_pesquisar = tk.Button(pesquisa_window, text="Pesquisar", command=lambda: pesquisar_livros_pesquisa(entry_pesquisa.get(), tabela_pesquisa))
    button_pesquisar.grid(row=0, column=2, padx=10, pady=5)

    tabela_pesquisa_frame = tk.Frame(pesquisa_window)
    tabela_pesquisa_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="NSEW")

    tabela_pesquisa = ttk.Treeview(tabela_pesquisa_frame, columns=("ID", "ISBN", "Nome", "Autor", "Preço", "Quantidade"), show="headings")
    tabela_pesquisa.heading("ID", text="ID")
    tabela_pesquisa.heading("ISBN", text="ISBN")
    tabela_pesquisa.heading("Nome", text="Nome")
    tabela_pesquisa.heading("Autor", text="Autor")
    tabela_pesquisa.heading("Preço", text="Preço")
    tabela_pesquisa.heading("Quantidade", text="Quantidade")
    tabela_pesquisa.pack(expand=True, fill="both")

    for col in ("ID", "ISBN", "Nome", "Autor", "Preço", "Quantidade"):
        tabela_pesquisa.column(col, width=120, anchor="w")

def pesquisar_livros_pesquisa(query, tabela_pesquisa):
    if not query:
        messagebox.showerror("Erro", "Digite um ISBN ou nome de livro para pesquisar.")
        return
    conn = sqlite3.connect('livros.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * FROM livros
    WHERE isbn LIKE ? OR nome LIKE ?
    ''', ('%' + query + '%', '%' + query + '%'))

    rows = cursor.fetchall()
    conn.close()

    for row in tabela_pesquisa.get_children():
        tabela_pesquisa.delete(row)

    for row in rows:
        tabela_pesquisa.insert("", "end", values=row)

# Inicializar o banco de dados
inicializar_bd()

root = tk.Tk()
root.title("Gerenciador de Livros")
root_width = root.winfo_screenwidth() // 2
root_height = root.winfo_screenheight() // 2
root.geometry(f"{1050}x{450}")

label_isbn = tk.Label(root, text="ISBN:")
label_isbn.grid(row=0, column=0, padx=10, pady=5)
entry_isbn = tk.Entry(root)
entry_isbn.grid(row=0, column=1, padx=10, pady=5)

label_nome = tk.Label(root, text="Nome:")
label_nome.grid(row=1, column=0, padx=10, pady=5)
entry_nome = tk.Entry(root)
entry_nome.grid(row=1, column=1, padx=10, pady=5)

label_autor = tk.Label(root, text="Autor:")
label_autor.grid(row=2, column=0, padx=10, pady=5)
entry_autor = tk.Entry(root)
entry_autor.grid(row=2, column=1, padx=10, pady=5)

label_preco = tk.Label(root, text="Preço (opcional):")
label_preco.grid(row=3, column=0, padx=10, pady=5)
entry_preco = tk.Entry(root)
entry_preco.grid(row=3, column=1, padx=10, pady=5)

label_quantidade = tk.Label(root, text="Quantidade:")
label_quantidade.grid(row=4, column=0, padx=10, pady=5)
entry_quantidade = tk.Entry(root)
entry_quantidade.grid(row=4, column=1, padx=10, pady=5)

button_adicionar = tk.Button(root, text="Adicionar Livro", command=salvar_livro)
button_adicionar.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="WE")

button_editar = tk.Button(root, text="Editar Livro", command=editar_livro)
button_editar.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="WE")

button_deletar = tk.Button(root, text="Deletar Livro", command=deletar_livro)
button_deletar.grid(row=7, column=0, columnspan=2, padx=10, pady=5, sticky="WE")

label_busca = tk.Label(root, text="Busca por ISBN ou Nome:")
label_busca.grid(row=8, column=0, padx=10, pady=5)
entry_busca = tk.Entry(root)
entry_busca.grid(row=8, column=1, padx=10, pady=5)

button_buscar = tk.Button(root, text="Buscar", command=buscar_livro)
button_buscar.grid(row=8, column=2, padx=10, pady=5)

label_status = tk.Label(root, text="")
label_status.grid(row=9, column=0, columnspan=3, padx=10, pady=5)

# Tabela para visualização dos livros
table_frame = tk.Frame(root)
table_frame.grid(row=0, column=3, rowspan=10, padx=10, pady=5, sticky="NSEW")

table = ttk.Treeview(table_frame, columns=("ID", "ISBN", "Nome", "Autor", "Preço", "Quantidade"), show="headings")
table.heading("ID", text="ID")
table.heading("ISBN", text="ISBN")
table.heading("Nome", text="Nome")
table.heading("Autor", text="Autor")
table.heading("Preço", text="Preço")
table.heading("Quantidade", text="Quantidade")
table.pack(expand=True, fill="both")

# Configurar o redimensionamento das colunas
table.column("ID", width=30, anchor="center")
table.column("ISBN", width=120, anchor="w")
table.column("Nome", width=200, anchor="w")
table.column("Autor", width=150, anchor="w")
table.column("Preço", width=70, anchor="w")
table.column("Quantidade", width=70, anchor="w")

# Atualizar a tabela de visualização com os dados do banco de dados
atualizar_tabela()

label_pesquisa = tk.Label(root, text="Pesquisa de Livros")
label_pesquisa.grid(row=10, column=0, columnspan=3, padx=10, pady=5)

button_pesquisar = tk.Button(root, text="Pesquisar Livros", command=lambda: abrir_pesquisa(root))
button_pesquisar.grid(row=11, column=0, columnspan=3, padx=10, pady=5)

root.mainloop()
