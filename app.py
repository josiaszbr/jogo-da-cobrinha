# Programa em Python para criar o Jogo da Cobrinha (Snake Game)

from tkinter import *
import random

# Inicializando dimensões e configurações do jogo
LARGURA = 500
ALTURA = 500
VELOCIDADE = 200
TAMANHO_ESPACO = 20
TAMANHO_CORPO = 2
COR_COBRA = "#00FF00"
COR_COMIDA = "#FFFFFF"
COR_FUNDO = "#000000"

# Classe para desenhar e controlar a cobra
class Cobra:

    def __init__(self):
        self.tamanho_corpo = TAMANHO_CORPO
        self.coordenadas = []
        self.quadrados = []

        for i in range(0, TAMANHO_CORPO):
            self.coordenadas.append([0, 0])

        for x, y in self.coordenadas:
            quadrado = tela.create_rectangle(
                x, y, x + TAMANHO_ESPACO, y + TAMANHO_ESPACO, 
                fill=COR_COBRA, tag="cobra")
            self.quadrados.append(quadrado)

# Classe para desenhar e controlar a comida
class Comida:

    def __init__(self):

        x = random.randint(0, 
                   (LARGURA // TAMANHO_ESPACO) - 1) * TAMANHO_ESPACO
        y = random.randint(0, 
                   (ALTURA // TAMANHO_ESPACO) - 1) * TAMANHO_ESPACO

        self.coordenadas = [x, y]

        tela.create_oval(x, y, x + TAMANHO_ESPACO, y +
                         TAMANHO_ESPACO, fill=COR_COMIDA, tag="comida")

# Função para verificar o próximo movimento da cobra
def proximo_turno(cobra, comida):

    x, y = cobra.coordenadas[0]

    if direcao == "cima":
        y -= TAMANHO_ESPACO
    elif direcao == "baixo":
        y += TAMANHO_ESPACO
    elif direcao == "esquerda":
        x -= TAMANHO_ESPACO
    elif direcao == "direita":
        x += TAMANHO_ESPACO

    cobra.coordenadas.insert(0, (x, y))

    quadrado = tela.create_rectangle(
        x, y, x + TAMANHO_ESPACO,
        y + TAMANHO_ESPACO, fill=COR_COBRA)

    cobra.quadrados.insert(0, quadrado)

    if x == comida.coordenadas[0] and y == comida.coordenadas[1]:

        global pontuacao

        pontuacao += 1

        rotulo.config(text="Pontos: {}".format(pontuacao))

        tela.delete("comida")

        comida = Comida()

    else:

        del cobra.coordenadas[-1]

        tela.delete(cobra.quadrados[-1])

        del cobra.quadrados[-1]

    if verificar_colisoes(cobra):
        fim_de_jogo()

    else:
        janela.after(VELOCIDADE, proximo_turno, cobra, comida)

# Função para controlar a direção da cobra
def mudar_direcao(nova_direcao):

    global direcao

    if nova_direcao == 'esquerda':
        if direcao != 'direita':
            direcao = nova_direcao
    elif nova_direcao == 'direita':
        if direcao != 'esquerda':
            direcao = nova_direcao
    elif nova_direcao == 'cima':
        if direcao != 'baixo':
            direcao = nova_direcao
    elif nova_direcao == 'baixo':
        if direcao != 'cima':
            direcao = nova_direcao

# Função para verificar colisões e posição da cobra
def verificar_colisoes(cobra):

    x, y = cobra.coordenadas[0]

    if x < 0 or x >= LARGURA:
        return True
    elif y < 0 or y >= ALTURA:
        return True

    for parte_corpo in cobra.coordenadas[1:]:
        if x == parte_corpo[0] and y == parte_corpo[1]:
            return True

    return False

# Função para encerrar o jogo
def fim_de_jogo():

    tela.delete(ALL)
    tela.create_text(tela.winfo_width() / 2, 
                     tela.winfo_height() / 2,
                     font=('consolas', 70), 
                     text="FIM DE JOGO", fill="red", 
                     tag="fim_de_jogo")

# Definindo a janela do jogo
janela = Tk()
janela.title("Jogo da Cobrinha")

pontuacao = 0
direcao = 'baixo'

# Exibição dos pontos no jogo
rotulo = Label(janela, text="Pontos: {}".format(pontuacao), 
               font=('consolas', 20))
rotulo.pack()

tela = Canvas(janela, bg=COR_FUNDO, 
              height=ALTURA, width=LARGURA)
tela.pack()

janela.update()

largura_janela = janela.winfo_width()
altura_janela = janela.winfo_height()
largura_tela = janela.winfo_screenwidth()
altura_tela = janela.winfo_screenheight()

x = int((largura_tela / 2) - (largura_janela / 2))
y = int((altura_tela / 2) - (altura_janela / 2))

janela.geometry(f"{largura_janela}x{altura_janela}+{x}+{y}")

janela.bind('<Left>', 
            lambda event: mudar_direcao('esquerda'))
janela.bind('<Right>', 
            lambda event: mudar_direcao('direita'))
janela.bind('<Up>', 
            lambda event: mudar_direcao('cima'))
janela.bind('<Down>', 
            lambda event: mudar_direcao('baixo'))

cobra = Cobra()
comida = Comida()

proximo_turno(cobra, comida)

janela.mainloop()