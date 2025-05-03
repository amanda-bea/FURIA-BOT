# FURIA-BOT (@CSFuriosoBot)

<div align="center">
  <img src="https://github.com/FURIA.png" width="200" alt="FURIA Logo">
  <br>
  <h3>Bot Telegram para fãs da FURIA CS</h3>
</div>

## 📖 Sobre

FURIA-BOT é um assistente de Telegram desenvolvido como parte do desafio para a posição de Engenheiro de Software na FURIA Esports. Este bot mantém os fãs da FURIA atualizados sobre o time de Counter-Strike, fornecendo informações em tempo real sobre resultados, agenda, elenco, estatísticas e muito mais.

## ✨ Funcionalidades

O bot oferece diversas funcionalidades para manter você atualizado sobre tudo relacionado à FURIA CS:

- 🏴 **Histórico de Partidas**: Últimos resultados da equipe
- 👥 **Elenco**: Informações sobre o elenco atual
- 📅 **Agenda**: Próximas partidas agendadas com contagem regressiva
- 🏆 **Títulos**: Conquistas e colocações em campeonatos
- 📊 **Estatísticas**: Performance dos jogadores e da equipe
- 🗺️ **Mapas**: Estatísticas de vitórias nos mapas da pool atual
- 📰 **Notícias**: Últimas notícias sobre a equipe
- 🌐 **Ranking**: Posição atual no ranking mundial
- 🏅 **Campeonatos**: Participações e colocações em eventos
- 📱 **Redes Sociais**: Links para todas as redes sociais oficiais

## 🌎 Suporte a Idiomas

O bot possui suporte bilíngue:
- 🇧🇷 Português (padrão)
- 🇺🇸 Inglês

## 🛠️ Tecnologias

- **Python**: Linguagem principal do projeto
- **Telebot**: Framework para desenvolvimento do bot do Telegram
- **Selenium**: Para web scraping e obtenção de dados atualizados
- **BeautifulSoup**: Para análise e extração de dados HTML
- **Edge WebDriver**: Driver para automação do navegador
- **Caching System**: Sistema de cache otimizado para reduzir requisições e melhorar o desempenho

## 📦 Instalação

### Pré-requisitos

- Python 3.8+
- Microsoft Edge instalado
- Microsoft Edge WebDriver (compatível com sua versão do Edge)

### Passos para instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/furia-bot.git
cd furia-bot
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Crie um arquivo `token.txt` na pasta raiz e adicione seu token do Telegram Bot (obtido via BotFather):
```bash
echo "SEU_TOKEN" > token.txt
```

4. Certifique-se de que o Microsoft Edge WebDriver (`msedgedriver.exe`) está na pasta raiz do projeto.

5. Execute o bot:
```bash
python main.py
```

## 🚀 Uso

1. Inicie uma conversa com o bot no Telegram buscando por `@CSFuriosoBot`
2. Use o comando `/start` para começar
3. Navegue pelas opções disponíveis usando os botões interativos

## 🔧 Otimizações

- **Sistema de Cache**: Implementação de cache TTL (Time-To-Live) para reduzir chamadas repetidas ao servidor
- **Web Scraping Otimizado**: Configuração eficiente do Selenium para minimizar uso de recursos
- **Multithreading**: Processamento concorrente para melhorar a resposta do bot
- **Manipulação de Erros**: Sistema robusto para lidar com falhas na extração de dados

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

Desenvolvido como parte do desafio para a posição de Engenheiro de Software na FURIA Esports.
by: Eu, Amanda... curte ai...

---

<div align="center">
  <p>🎮 FURIA É NOSSO TIME 🎮</p>
</div>