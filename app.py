import json
import random
import time
from pathlib import Path
from tkinter import *
from tkinter import messagebox

try:
    import winsound
except ImportError:
    winsound = None


LARGURA = 480
ALTURA = 480
TAMANHO_ESPACO = 24
COR_FUNDO = "#0b1220"
COR_TABULEIRO = "#101b2d"
COR_GRADE = "#17263b"
COR_COBRA = "#48e5a3"
COR_CABECA = "#8bffc6"
COR_BRILHO = "#d5ffe9"
COR_COMIDA = "#ff6b6b"
COR_BONUS = "#ffd166"
DURACAO_BONUS_MS = 7000
VELOCIDADES = {"Fácil": 170, "Médio": 130, "Difícil": 95}
ARQUIVO_RECORDE = Path(__file__).with_name("recorde.json")


def carregar_recorde():
    if not ARQUIVO_RECORDE.exists():
        return 0

    try:
        dados = json.loads(ARQUIVO_RECORDE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        messagebox.showerror(
            "Erro ao carregar recorde",
            f"Não foi possível ler {ARQUIVO_RECORDE.name}:\n{erro}",
            parent=janela,
        )
        return 0

    recorde = dados.get("recorde") if isinstance(dados, dict) else None
    if not isinstance(recorde, int) or isinstance(recorde, bool) or recorde < 0:
        messagebox.showerror(
            "Recorde inválido",
            f"O conteúdo de {ARQUIVO_RECORDE.name} não contém um recorde válido.",
            parent=janela,
        )
        return 0
    return recorde


def salvar_recorde():
    try:
        ARQUIVO_RECORDE.write_text(
            json.dumps({"recorde": melhor_pontuacao}, indent=2),
            encoding="utf-8",
        )
    except OSError as erro:
        messagebox.showerror(
            "Erro ao salvar recorde",
            f"Não foi possível salvar {ARQUIVO_RECORDE.name}:\n{erro}",
            parent=janela,
        )


def tocar_som(tipo):
    if winsound is None:
        janela.bell()
        return

    sons = {
        "comer": winsound.MB_OK,
        "virar": winsound.MB_ICONEXCLAMATION,
        "fim": winsound.MB_ICONHAND,
    }
    winsound.MessageBeep(sons[tipo])


def posicao_livre(extras=()):
    ocupadas = set(cobra)
    ocupadas.update(posicao for posicao in extras if posicao is not None)
    livres = [
        (x, y)
        for x in range(0, LARGURA, TAMANHO_ESPACO)
        for y in range(0, ALTURA, TAMANHO_ESPACO)
        if (x, y) not in ocupadas
    ]
    return random.choice(livres) if livres else None


def desenhar_grade():
    for x in range(0, LARGURA, TAMANHO_ESPACO):
        tela.create_line(x, 0, x, ALTURA, fill=COR_GRADE, tags="grade")
    for y in range(0, ALTURA, TAMANHO_ESPACO):
        tela.create_line(0, y, LARGURA, y, fill=COR_GRADE, tags="grade")
    tela.tag_lower("grade")


def desenhar_comidas():
    tela.delete("fruta")
    tela.delete("bonus")

    if comida is not None:
        x, y = comida
        centro_x = x + TAMANHO_ESPACO // 2
        centro_y = y + TAMANHO_ESPACO // 2
        raio = 7 + pulso_fruta_atual
        tela.create_oval(
            centro_x - raio,
            centro_y - raio,
            centro_x + raio,
            centro_y + raio,
            fill=COR_COMIDA,
            outline="#ff9a9a",
            width=1,
            tags="fruta",
        )
        tela.create_oval(
            centro_x - 2,
            centro_y - 4,
            centro_x + 1,
            centro_y - 1,
            fill="#ffe0e0",
            outline="",
            tags="fruta",
        )

    if fruta_bonus is not None:
        x, y = fruta_bonus
        centro_x = x + TAMANHO_ESPACO // 2
        centro_y = y + TAMANHO_ESPACO // 2
        raio = 8 + pulso_fruta_atual
        tela.create_oval(
            centro_x - raio,
            centro_y - raio,
            centro_x + raio,
            centro_y + raio,
            fill=COR_BONUS,
            outline="#fff0b3",
            width=1,
            tags="bonus",
        )
        tela.create_text(
            centro_x,
            centro_y,
            text="+",
            fill="#76520a",
            font=("Segoe UI", 10, "bold"),
            tags="bonus",
        )

    if estado == "pausado":
        tela.tag_raise("overlay")


def desenhar_cobra():
    tela.delete("cobra")
    centros = [
        (x + TAMANHO_ESPACO // 2, y + TAMANHO_ESPACO // 2)
        for x, y in cobra
    ]
    cor_corpo = COR_BRILHO if brilho_cobra else COR_COBRA

    if len(centros) > 1:
        coordenadas = [valor for ponto in centros for valor in ponto]
        tela.create_line(
            *coordenadas,
            fill=cor_corpo,
            width=18,
            capstyle="round",
            joinstyle="round",
            tags="cobra",
        )

    for centro_x, centro_y in centros[1:]:
        tela.create_oval(
            centro_x - 9,
            centro_y - 9,
            centro_x + 9,
            centro_y + 9,
            fill=cor_corpo,
            outline="",
            tags="cobra",
        )

    centro_x, centro_y = centros[0]
    cor_cabeca = COR_BRILHO if brilho_cobra else COR_CABECA
    tela.create_oval(
        centro_x - 10,
        centro_y - 10,
        centro_x + 10,
        centro_y + 10,
        fill=cor_cabeca,
        outline="",
        tags="cobra",
    )

    dx, dy = direcao[0]
    perpendicular = (-dy, dx)
    for lado in (-1, 1):
        olho_x = centro_x + dx * 5 + perpendicular[0] * lado * 4
        olho_y = centro_y + dy * 5 + perpendicular[1] * lado * 4
        tela.create_oval(
            olho_x - 2,
            olho_y - 2,
            olho_x + 2,
            olho_y + 2,
            fill="#173329",
            outline="",
            tags="cobra",
        )

    if estado == "pausado":
        tela.tag_raise("overlay")


def desenhar_tabuleiro():
    tela.delete(ALL)
    desenhar_grade()
    desenhar_comidas()
    desenhar_cobra()


def animar_comida():
    global id_animacao, pulso_fruta_atual
    id_animacao = None
    if estado not in ("jogando", "pausado"):
        return

    pulso_fruta_atual = 1 - pulso_fruta_atual
    desenhar_comidas()
    id_animacao = janela.after(160, animar_comida)


def animar_particulas(etapa, particulas):
    global id_particulas
    if etapa >= 6:
        for id_particula, _, _ in particulas:
            tela.delete(id_particula)
        id_particulas = None
        return

    for id_particula, dx, dy in particulas:
        tela.move(id_particula, dx, dy)
    id_particulas = janela.after(
        35, lambda: animar_particulas(etapa + 1, particulas)
    )


def soltar_particulas(posicao, cor):
    global id_particulas
    if id_particulas is not None:
        janela.after_cancel(id_particulas)
        id_particulas = None
    tela.delete("particula")

    x, y = posicao
    centro_x = x + TAMANHO_ESPACO // 2
    centro_y = y + TAMANHO_ESPACO // 2
    particulas = []
    for _ in range(10):
        dx = random.uniform(-2.5, 2.5)
        dy = random.uniform(-2.5, 2.5)
        id_particula = tela.create_oval(
            centro_x - 2,
            centro_y - 2,
            centro_x + 2,
            centro_y + 2,
            fill=cor,
            outline="",
            tags="particula",
        )
        particulas.append((id_particula, dx, dy))
    id_particulas = janela.after(35, lambda: animar_particulas(0, particulas))


def remover_bonus():
    global fruta_bonus, id_bonus, prazo_bonus, tempo_bonus_restante
    fruta_bonus = None
    id_bonus = None
    prazo_bonus = None
    tempo_bonus_restante = 0
    desenhar_comidas()


def criar_bonus():
    global fruta_bonus, id_bonus, prazo_bonus, tempo_bonus_restante
    fruta_bonus = posicao_livre((comida,))
    if fruta_bonus is None:
        return
    tempo_bonus_restante = DURACAO_BONUS_MS
    prazo_bonus = time.monotonic() + tempo_bonus_restante / 1000
    id_bonus = janela.after(tempo_bonus_restante, remover_bonus)
    desenhar_comidas()


def atualizar_pontuacao(pontos):
    global pontuacao, melhor_pontuacao, recorde_novo
    pontuacao += pontos
    rotulo_pontos.config(text=f"{pontuacao:02d}")

    if pontuacao > melhor_pontuacao:
        melhor_pontuacao = pontuacao
        recorde_novo = True
        rotulo_recorde.config(text=f"RECORDE  {melhor_pontuacao:02d}")
        rotulo_recorde_menu.config(text=f"Recorde atual: {melhor_pontuacao:02d}")
        salvar_recorde()


def exibir_fim_de_jogo(vitoria=False):
    global estado
    estado = "vitoria" if vitoria else "fim"
    cancelar_temporizadores()
    tocar_som("fim")
    tela.delete("overlay")
    tela.create_rectangle(
        0,
        0,
        LARGURA,
        ALTURA,
        fill="#07101d",
        stipple="gray50",
        outline="",
        tags="overlay",
    )
    tela.create_text(
        LARGURA // 2,
        ALTURA // 2 - 54,
        text="VOCÊ VENCEU!" if vitoria else "FIM DE JOGO",
        fill=COR_CABECA if vitoria else "#ffffff",
        font=("Segoe UI", 26, "bold"),
        tags="overlay",
    )
    tela.create_text(
        LARGURA // 2,
        ALTURA // 2 - 10,
        text=f"Pontuação final: {pontuacao}",
        fill="#ffffff",
        font=("Segoe UI", 15, "bold"),
        tags="overlay",
    )
    texto_recorde = (
        "Novo recorde!" if recorde_novo else f"Recorde: {melhor_pontuacao}"
    )
    tela.create_text(
        LARGURA // 2,
        ALTURA // 2 + 23,
        text=texto_recorde,
        fill=COR_BONUS,
        font=("Segoe UI", 12),
        tags="overlay",
    )
    rotulo_rodape.pack_forget()
    controles_fim.pack(pady=(10, 0))


def cancelar_temporizadores():
    global id_tick, id_animacao, id_bonus, id_particulas, id_br
    for identificador in (id_tick, id_animacao, id_bonus, id_particulas, id_br):
        if identificador is not None:
            janela.after_cancel(identificador)
    id_tick = None
    id_animacao = None
    id_bonus = None
    id_particulas = None
    id_br = None


def proximo_turno():
    global id_tick, id_bonus, cobra, comida, fruta_bonus, direcao_pendente
    global comidas_normais, brilho_cobra, id_br
    id_tick = None
    if estado != "jogando":
        return

    if direcao_pendente is not None:
        direcao[0] = direcao_pendente
        direcao_pendente = None

    x, y = cobra[0]
    dx, dy = direcao[0]
    proxima = (x + dx * TAMANHO_ESPACO, y + dy * TAMANHO_ESPACO)
    if modo_var.get() == "Sem paredes":
        proxima = (proxima[0] % LARGURA, proxima[1] % ALTURA)

    cobra.insert(0, proxima)
    comeu_bonus = proxima == fruta_bonus
    comeu_normal = proxima == comida

    if comeu_bonus:
        fruta_bonus = None
        if id_bonus is not None:
            janela.after_cancel(id_bonus)
        id_bonus = None
        atualizar_pontuacao(5)
        tocar_som("comer")
        soltar_particulas(proxima, COR_BONUS)
        iniciar_brilho()
    elif comeu_normal:
        atualizar_pontuacao(1)
        comidas_normais += 1
        tocar_som("comer")
        soltar_particulas(proxima, COR_COMIDA)
        iniciar_brilho()
    else:
        cobra.pop()

    if comeu_normal:
        comida = posicao_livre((fruta_bonus,))
        if comida is None:
            desenhar_comidas()
            desenhar_cobra()
            exibir_fim_de_jogo(vitoria=True)
            return
        if comidas_normais % 5 == 0 and fruta_bonus is None:
            criar_bonus()

    desenhar_comidas()
    desenhar_cobra()
    if verificar_colisoes():
        exibir_fim_de_jogo()
    else:
        id_tick = janela.after(velocidade_atual, proximo_turno)


def iniciar_brilho():
    global brilho_cobra, id_br
    brilho_cobra = True
    desenhar_cobra()
    if id_br is not None:
        janela.after_cancel(id_br)
    id_br = janela.after(180, encerrar_brilho)


def encerrar_brilho():
    global brilho_cobra, id_br
    brilho_cobra = False
    id_br = None
    if estado in ("jogando", "pausado"):
        desenhar_cobra()


def verificar_colisoes():
    x, y = cobra[0]
    if modo_var.get() == "Clássico" and (
        x < 0 or x >= LARGURA or y < 0 or y >= ALTURA
    ):
        return True
    return cobra[0] in cobra[1:]


def mudar_direcao(nova_direcao):
    global direcao_pendente
    direcao_base = direcao_pendente if direcao_pendente is not None else direcao[0]
    if (
        direcao_pendente is None
        and nova_direcao != (-direcao_base[0], -direcao_base[1])
        and nova_direcao != direcao_base
    ):
        direcao_pendente = nova_direcao
        tocar_som("virar")


def alternar_pausa():
    global estado, id_tick, id_bonus, prazo_bonus, tempo_bonus_restante
    if estado == "jogando":
        estado = "pausado"
        if id_tick is not None:
            janela.after_cancel(id_tick)
            id_tick = None
        if id_bonus is not None:
            janela.after_cancel(id_bonus)
            id_bonus = None
            tempo_bonus_restante = max(
                1, int((prazo_bonus - time.monotonic()) * 1000)
            )
        tela.delete("overlay")
        tela.create_rectangle(
            0,
            0,
            LARGURA,
            ALTURA,
            fill="#07101d",
            stipple="gray50",
            outline="",
            tags="overlay",
        )
        tela.create_text(
            LARGURA // 2,
            ALTURA // 2 - 10,
            text="PAUSADO",
            fill="#ffffff",
            font=("Segoe UI", 26, "bold"),
            tags="overlay",
        )
        tela.create_text(
            LARGURA // 2,
            ALTURA // 2 + 28,
            text="P ou Espaço para continuar",
            fill="#a8b8ce",
            font=("Segoe UI", 11),
            tags="overlay",
        )
        tela.tag_raise("overlay")
    elif estado == "pausado":
        estado = "jogando"
        tela.delete("overlay")
        id_tick = janela.after(velocidade_atual, proximo_turno)
        if fruta_bonus is not None:
            prazo_bonus = time.monotonic() + tempo_bonus_restante / 1000
            id_bonus = janela.after(tempo_bonus_restante, remover_bonus)


def tratar_tecla(evento):
    teclas = {
        "Up": (0, -1),
        "w": (0, -1),
        "W": (0, -1),
        "Down": (0, 1),
        "s": (0, 1),
        "S": (0, 1),
        "Left": (-1, 0),
        "a": (-1, 0),
        "A": (-1, 0),
        "Right": (1, 0),
        "d": (1, 0),
        "D": (1, 0),
    }

    if evento.keysym in ("p", "P", "space"):
        alternar_pausa()
    elif evento.keysym in ("r", "R") and estado in ("jogando", "pausado"):
        iniciar_jogo()
    elif evento.keysym == "Escape" and estado in ("fim", "vitoria"):
        voltar_ao_menu()
    elif evento.keysym in teclas and estado == "jogando":
        mudar_direcao(teclas[evento.keysym])


def iniciar_jogo():
    global estado, cobra, comida, fruta_bonus, direcao_pendente
    global pontuacao, comidas_normais, velocidade_atual, brilho_cobra
    global prazo_bonus, tempo_bonus_restante, recorde_novo, pulso_fruta_atual
    global id_tick, id_animacao

    cancelar_temporizadores()
    estado = "jogando"
    cobra = [
        (LARGURA // 2, ALTURA // 2),
        (LARGURA // 2 - TAMANHO_ESPACO, ALTURA // 2),
        (LARGURA // 2 - 2 * TAMANHO_ESPACO, ALTURA // 2),
    ]
    direcao[0] = (1, 0)
    direcao_pendente = None
    pontuacao = 0
    comidas_normais = 0
    velocidade_atual = VELOCIDADES[dificuldade_var.get()]
    fruta_bonus = None
    prazo_bonus = None
    tempo_bonus_restante = 0
    brilho_cobra = False
    recorde_novo = False
    pulso_fruta_atual = 0
    comida = posicao_livre()
    rotulo_pontos.config(text="00")

    menu_frame.pack_forget()
    game_frame.pack()
    controles_fim.pack_forget()
    rotulo_rodape.pack(pady=12)
    desenhar_tabuleiro()
    id_tick = janela.after(velocidade_atual, proximo_turno)
    id_animacao = janela.after(160, animar_comida)


def voltar_ao_menu():
    global estado
    cancelar_temporizadores()
    estado = "menu"
    game_frame.pack_forget()
    menu_frame.pack(fill="both", expand=True)


janela = Tk()
janela.title("Cobrinha")
janela.configure(bg=COR_FUNDO)
janela.resizable(False, False)
janela.geometry("540x680")

pontuacao = 0
melhor_pontuacao = carregar_recorde()
recorde_novo = False
comidas_normais = 0
velocidade_atual = VELOCIDADES["Médio"]
estado = "menu"
cobra = []
comida = None
fruta_bonus = None
direcao = [(1, 0)]
direcao_pendente = None
brilho_cobra = False
pulso_fruta_atual = 0
prazo_bonus = None
tempo_bonus_restante = 0
id_tick = None
id_animacao = None
id_bonus = None
id_particulas = None
id_br = None

conteudo = Frame(janela, bg=COR_FUNDO, padx=24, pady=20)
conteudo.pack(fill="both", expand=True)

menu_frame = Frame(conteudo, bg=COR_FUNDO)
Label(
    menu_frame,
    text="COBRINHA",
    bg=COR_FUNDO,
    fg="#f4f7fb",
    font=("Segoe UI", 28, "bold"),
).pack(pady=(42, 4))
Label(
    menu_frame,
    text="Uma cobrinha, muitas frutas.",
    bg=COR_FUNDO,
    fg="#93a6bf",
    font=("Segoe UI", 11),
).pack(pady=(0, 24))

rotulo_recorde_menu = Label(
    menu_frame,
    text=f"Recorde atual: {melhor_pontuacao:02d}",
    bg=COR_FUNDO,
    fg=COR_BONUS,
    font=("Segoe UI", 12, "bold"),
)
rotulo_recorde_menu.pack(pady=(0, 22))

dificuldade_var = StringVar(value="Médio")
modo_var = StringVar(value="Clássico")
for texto, variavel, opcoes in (
    ("DIFICULDADE", dificuldade_var, tuple(VELOCIDADES)),
    ("MODO", modo_var, ("Clássico", "Sem paredes")),
):
    Label(
        menu_frame,
        text=texto,
        bg=COR_FUNDO,
        fg="#a8b8ce",
        font=("Segoe UI", 9, "bold"),
    ).pack(pady=(10, 4))
    seletor = OptionMenu(menu_frame, variavel, *opcoes)
    seletor.config(
        bg="#17263b",
        fg="#f4f7fb",
        activebackground="#263750",
        activeforeground="#f4f7fb",
        highlightthickness=0,
        width=18,
        font=("Segoe UI", 10),
    )
    seletor["menu"].config(
        bg="#17263b",
        fg="#f4f7fb",
        activebackground="#263750",
    )
    seletor.pack()

Button(
    menu_frame,
    text="JOGAR",
    command=iniciar_jogo,
    bg="#48e5a3",
    fg="#092016",
    activebackground="#8bffc6",
    relief="flat",
    font=("Segoe UI", 12, "bold"),
    padx=32,
    pady=9,
).pack(pady=(28, 16))
Label(
    menu_frame,
    text="WASD ou setas: mover   |   P ou Espaço: pausar\n"
    "Fruta dourada: +5 pontos, aparece a cada 5 frutas",
    bg=COR_FUNDO,
    fg="#93a6bf",
    font=("Segoe UI", 9),
    justify="center",
).pack(pady=8)

game_frame = Frame(conteudo, bg=COR_FUNDO)
cabecalho = Frame(game_frame, bg=COR_FUNDO)
cabecalho.pack(fill="x", pady=(0, 14))
Label(
    cabecalho,
    text="COBRINHA",
    bg=COR_FUNDO,
    fg="#f4f7fb",
    font=("Segoe UI", 20, "bold"),
).pack(side="left")

rotulo_recorde = Label(
    cabecalho,
    text=f"RECORDE  {melhor_pontuacao:02d}",
    bg=COR_FUNDO,
    fg="#93a6bf",
    font=("Segoe UI", 9, "bold"),
)
rotulo_recorde.pack(side="right", padx=(12, 0), pady=(8, 0))

placar = Frame(cabecalho, bg="#17263b", padx=12, pady=5)
placar.pack(side="right")
Label(
    placar,
    text="PONTOS",
    bg="#17263b",
    fg="#93a6bf",
    font=("Segoe UI", 8, "bold"),
).pack(side="left", padx=(0, 8))
rotulo_pontos = Label(
    placar,
    text="00",
    bg="#17263b",
    fg=COR_CABECA,
    font=("Segoe UI", 12, "bold"),
)
rotulo_pontos.pack(side="left")

tela = Canvas(
    game_frame,
    bg=COR_TABULEIRO,
    height=ALTURA,
    width=LARGURA,
    highlightthickness=1,
    highlightbackground="#263750",
)
tela.pack()

rotulo_rodape = Label(
    game_frame,
    text="WASD ou setas para mover     •     P ou Espaço para pausar",
    bg=COR_FUNDO,
    fg="#93a6bf",
    font=("Segoe UI", 9),
)

controles_fim = Frame(game_frame, bg=COR_FUNDO)
Button(
    controles_fim,
    text="JOGAR DE NOVO",
    command=iniciar_jogo,
    bg="#48e5a3",
    fg="#092016",
    activebackground="#8bffc6",
    relief="flat",
    font=("Segoe UI", 10, "bold"),
    padx=18,
    pady=7,
).pack(side="left", padx=6)
Button(
    controles_fim,
    text="MENU",
    command=voltar_ao_menu,
    bg="#263750",
    fg="#f4f7fb",
    activebackground="#344965",
    relief="flat",
    font=("Segoe UI", 10, "bold"),
    padx=18,
    pady=7,
).pack(side="left", padx=6)

janela.bind("<KeyPress>", tratar_tecla)
menu_frame.pack(fill="both", expand=True)
janela.mainloop()
