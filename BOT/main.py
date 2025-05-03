import telebot
from telebot import types
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import functools
from cachetools import TTLCache, cached
import concurrent.futures

# Cache aprimorado: maior capacidade e TTL mais longo para conteúdo que muda menos frequentemente
page_cache = TTLCache(maxsize=200, ttl=1800)  # 30 minutos para páginas
results_cache = TTLCache(maxsize=50, ttl=300)  # 5 minutos para resultados de partidas
roster_cache = TTLCache(maxsize=20, ttl=3600)  # 1 hora para roster
upcoming_cache = TTLCache(maxsize=20, ttl=600)  # 10 minutos para partidas futuras

# Carregar token
with open('token.txt') as arquivo:
    token = arquivo.read().strip()

bot = telebot.TeleBot(token)

# Dicionários de mensagens
messages_pt = {
    'welcome': 'Fala furioso! Eu sou o bot da FURIA CS e vou te deixar ligado sobre tudo a nossa seleção, como posso ajudar?',
    'choose_option': 'Escolha uma opção:',
    'help': 'Você pode usar os seguintes comandos:\n/start - Inicie o bot\n/help - Obtenha ajuda\n/english - Mudar para inglês',
    'language_switched': 'Idioma alterado para inglês!',
}

messages_en = {
    'welcome': 'Hey furious one! I am the FURIA CS bot, and I will keep you updated about our team, how can I help?',
    'choose_option': 'Choose an option:',
    'help': 'You can use the following commands:\n/start - Start the bot\n/help - Get help\n/english - Switch to Portuguese',
    'language_switched': 'Language switched to Portuguese!',
}

# Variável de idioma
current_language = 'pt'  # 'pt' ou 'en'

# Configuração do Selenium com Edge
def setup_driver():
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--disable-extensions")  # Desativa extensões para melhor desempenho
    edge_options.add_argument("--disable-images")  # Desativa carregamento de imagens
    edge_options.add_argument("--blink-settings=imagesEnabled=false")  # Desativa imagens no Blink
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36")
    # Configura preferências para reduzir uso de recursos
    edge_options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,  # Bloqueia carregamento de imagens
        "disk-cache-size": 4096,  # Cache de disco menor
        "profile.default_content_settings.cookies": 2  # Bloqueia cookies
    })
    service = Service("./msedgedriver.exe")
    return webdriver.Edge(service=service, options=edge_options)


def wait_for_page_load(driver, timeout=10):
    """Espera inteligente até que a página esteja carregada completamente."""
    try:
        # Espera pelo readyState completo
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        
        # Espera específica para elementos do HLTV 
        # Isso ajuda a garantir que o conteúdo principal esteja presente
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "contentCol"))
        )
    except Exception as e:
        print(f"Tempo esgotado esperando a página carregar: {e}")
        # Continue mesmo se o timeout ocorrer, o conteúdo parcial ainda pode ser útil

# Função otimizada para buscar conteúdo da página
@functools.lru_cache(maxsize=50)  # Adiciona um cache LRU local
def fetch_page_source(url):
    """Busca o código fonte da página com cache otimizado."""
    # Verifica se já está no cache
    if url in page_cache:
        return page_cache[url]
    
    try:
        driver = setup_driver()
        driver.get(url)
        wait_for_page_load(driver)
        
        # Otimiza memória extraindo apenas o conteúdo necessário
        content_element = driver.find_element(By.CLASS_NAME, "contentCol")
        if content_element:
            page_source = content_element.get_attribute('outerHTML')
        else:
            page_source = driver.page_source
            
        driver.quit()
        
        # Armazena no cache
        page_cache[url] = page_source
        return page_source
    except Exception as e:
        print(f"Erro ao buscar página {url}: {e}")
        driver.quit() if 'driver' in locals() else None
        return ""

# Enviar mensagem de boas-vindas com botões
def send_welcome(message):
    text = messages_pt['welcome'] if current_language == 'pt' else messages_en['welcome']
    bot.send_message(message.chat.id, text)

    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons_pt = [
        ('Histórico', '/historico'),
        ('Elenco', '/elenco'),
        ('Agenda', '/agenda'),
        ('Títulos', '/titulos'),
        ('Estatísticas', '/stats'),
        ('Mapas', '/mapas'),
        ('Notícias', '/novidades'),
        ('Ranking', '/ranking'),
        ('Campeonatos', '/camps'),
        ('Redes Sociais', '/redes')
    ]

    buttons_en = [
        ('History', '/historico'),
        ('Roster', '/elenco'),
        ('Schedule', '/agenda'),
        ('Titles', '/titulos'),
        ('Stats', '/stats'),
        ('Maps', '/mapas'),
        ('News', '/novidades'),
        ('Ranking', '/ranking'),
        ('Events', '/camps'),
        ('Social Media', '/redes')
    ]

    language_buttons = [
        ('Mudar para Português', '/portugues') if current_language == 'en' else ('Switch to English', '/english')
    ]

    buttons = buttons_pt if current_language == 'pt' else buttons_en

    for i in range(0, len(buttons), 2):
        row = []
        row.append(types.InlineKeyboardButton(buttons[i][0], callback_data=buttons[i][1]))
        if i + 1 < len(buttons):
            row.append(types.InlineKeyboardButton(buttons[i + 1][0], callback_data=buttons[i + 1][1]))
        markup.add(*row)

    for button_text, callback in language_buttons:
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback))

    choose = messages_pt['choose_option'] if current_language == 'pt' else messages_en['choose_option']
    bot.send_message(message.chat.id, choose, reply_markup=markup)

# Comandos básicos
@bot.message_handler(commands=['start', 'help'])
def start(message):
    send_welcome(message)

@bot.message_handler(func=lambda message: True)
def handle_unknown_message(message):
    send_welcome(message)

# Função de manipular os botões - não modificado
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global current_language
    
    if call.data == '/historico':
        bot.answer_callback_query(call.id, "Últimos resultados!" if current_language == 'pt' else "Latest results!")
        send_last_results(call.message.chat.id)

    elif call.data == '/elenco':
        bot.answer_callback_query(call.id, "Elenco atual!" if current_language == 'pt' else "Current roster!")
        send_roster(call.message.chat.id)

    elif call.data == '/agenda':
        bot.answer_callback_query(call.id, "Próximas partidas!" if current_language == 'pt' else "Upcoming matches!")
        send_upcoming_matches(call.message.chat.id)

    elif call.data == '/titulos':
        bot.answer_callback_query(call.id, "Títulos conquistados!" if current_language == 'pt' else "Titles won!")
        send_titles(call.message.chat.id)

    elif call.data == '/stats':
        bot.answer_callback_query(call.id, "Estatísticas da equipe!" if current_language == 'pt' else "Team stats!")
        send_stats(call.message.chat.id)

    elif call.data == '/novidades':
        bot.answer_callback_query(call.id, "Últimas notícias!" if current_language == 'pt' else "Latest news!")
        send_news(call.message.chat.id)

    elif call.data == '/ranking':
        bot.answer_callback_query(call.id, "Ranking atual!" if current_language == 'pt' else "Current ranking!")
        send_ranking(call.message.chat.id)

    elif call.data == '/redes':
        bot.answer_callback_query(call.id, "Redes sociais da FURIA!" if current_language == 'pt' else "FURIA's social media!")
        send_social_links(call.message.chat.id)

    elif call.data == '/camps':
        bot.answer_callback_query(call.id, "Colocações da FURIA!" if current_language == 'pt' else "FURIA's placements!")
        send_camps(call.message.chat.id)

    elif call.data == '/mapas':
        bot.answer_callback_query(call.id, "Mapas jogados pela FURIA!" if current_language == 'pt' else "Maps played by FURIA!")
        send_maps(call.message.chat.id)

    elif call.data == '/english':
        current_language = 'en'
        bot.answer_callback_query(call.id, "Language switched to English!")
        send_welcome(call.message)

    elif call.data == '/portugues':
        current_language = 'pt'
        bot.answer_callback_query(call.id, "Idioma alterado para Português!")
        send_welcome(call.message)


@cached(cache=results_cache)
def send_last_results(chat_id):
    """Busca e envia os últimos resultados com cache."""
    try:
        url = 'https://www.hltv.org/results?team=8297'
        page_source = fetch_page_source(url)
        
        if not page_source:
            bot.send_message(chat_id, "Erro ao buscar resultados." if current_language == 'pt' else "Error fetching results.")
            return
            
        soup = BeautifulSoup(page_source, 'html.parser')
        results = soup.select('.results-sublist .result-con')
        
        message = "🏴 Últimos resultados da FURIA:\n\n" if current_language == 'pt' else "🏴 Latest FURIA results:\n\n"

        count = 0
        for result in results:
            team1_elem = result.select_one('.team1 .team')
            team2_elem = result.select_one('.team2 .team')

            if not team1_elem or not team2_elem:
                continue

            team1 = team1_elem.text.strip()
            team2 = team2_elem.text.strip()

            scores = result.select_one('.result-score')
            if not scores:
                continue

            score_text = scores.text.strip()
            score_team1, score_team2 = map(str.strip, score_text.split('-'))

            if team1.lower() == "furia":
                furia_score = score_team1
                opponent = team2
                opponent_score = score_team2
            else:
                furia_score = score_team2
                opponent = team1
                opponent_score = score_team1

            event = result.select_one('.event .event-name').text.strip()
            date = result.find_parent('div', class_='results-sublist').select_one('.standard-headline').text.strip()

            message += f"📅 {date}\n"
            message += f"🏆 FURIA {furia_score} - {opponent_score} {opponent}\n"
            message += f"🎮 Campeonato: {event}\n\n"

            count += 1
            if count == 10:
                break

        if count == 0:
            message = "Nenhum jogo recente da FURIA encontrado." if current_language == 'pt' else "No recent FURIA matches found."

        bot.send_message(chat_id, message, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(chat_id, "Erro ao buscar resultados." if current_language == 'pt' else "Error fetching results.")
        print(f"Erro: {e}")

@cached(cache=roster_cache)
def send_roster(chat_id):
    """Busca e envia o elenco atual com cache."""
    try:
        url = 'https://www.hltv.org/team/8297/furia'
        page_source = fetch_page_source(url)
        
        if not page_source:
            bot.send_message(chat_id, "Erro ao buscar elenco." if current_language == 'pt' else "Error fetching roster.")
            return
            
        soup = BeautifulSoup(page_source, 'html.parser')
        players_table = soup.select_one('.table-container.players-table tbody')
        
        message = "🎯 Elenco atual da FURIA:\n\n" if current_language == 'pt' else "🎯 Current FURIA roster:\n\n"

        if players_table:
            rows = players_table.select('tr')
            for row in rows:
                nickname = row.select_one('.playersBox-playernick').text.strip()
                rating = row.select_one('.rating-cell').text.strip()
                message += f"• {nickname} - Rating: {rating}\n"
        else:
            message += "Nenhum jogador encontrado." if current_language == 'pt' else "No players found."

        bot.send_message(chat_id, message)

    except Exception as e:
        bot.send_message(chat_id, "Erro ao buscar elenco." if current_language == 'pt' else "Error fetching roster.")
        print(f"Erro: {e}")

@cached(cache=upcoming_cache)
def send_upcoming_matches(chat_id):
    """Busca e envia as próximas partidas com cache."""
    try:
        url = 'https://www.hltv.org/team/8297/furia#tab-matchesBox'
        page_source = fetch_page_source(url)
        
        if not page_source:
            bot.send_message(chat_id, "Erro ao buscar partidas." if current_language == 'pt' else "Error fetching matches.")
            return
            
        soup = BeautifulSoup(page_source, 'html.parser')
        message = "📅 **Próximas partidas da FURIA:**\n\n" if current_language == 'pt' else "📅 **Upcoming FURIA matches:**\n\n"

        rows = soup.select('.team-row')
        count = 0
        now = datetime.now(timezone.utc).timestamp()

        for match in rows:
            date_tag = match.select_one('.date-cell span')
            if not (date_tag and date_tag.has_attr('data-unix')):
                continue

            match_timestamp = int(date_tag['data-unix']) / 1000
            if match_timestamp < now:
                continue

            match_date = datetime.fromtimestamp(match_timestamp, timezone.utc)
            formatted_date = match_date.strftime('%d/%m/%Y')
            time_remaining = match_date - datetime.now(timezone.utc)
            days, seconds = divmod(time_remaining.total_seconds(), 86400)
            hours, seconds = divmod(seconds, 3600)
            minutes, _ = divmod(seconds, 60)
            countdown = f"{int(days)}d {int(hours)}h {int(minutes)}m restantes" if current_language == 'pt' else f"{int(days)}d {int(hours)}h {int(minutes)}m remaining"

            team1 = match.select_one('.team-name.team-1').text.strip()
            team2 = match.select_one('.team-name.team-2').text.strip()

            link_tag = match.select_one('.matchpage-button-cell a')
            match_link = link_tag['href'] if link_tag else '#'

            message += f"📅 {formatted_date} ({countdown})\n"
            message += f"⚔️ {team1} vs {team2}\n"
            message += f"[🔗 Link para a partida](https://www.hltv.org{match_link})\n\n"

            count += 1
            if count == 3:
                break

        if count == 0:
            message += "Nenhuma partida agendada." if current_language == 'pt' else "No scheduled matches."

        bot.send_message(chat_id, message, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(chat_id, "Erro ao buscar partidas." if current_language == 'pt' else "Error fetching matches.")
        print(f"Erro: {e}")


@cached(cache=TTLCache(maxsize=10, ttl=259200))  # 3 dias de cache (259200 segundos)
def send_titles(chat_id):
    """Busca e envia os títulos com cache."""
    try:
        url = 'https://www.hltv.org/team/8297/furia#tab-achievementsBox'
        page_source = fetch_page_source(url)
        
        if not page_source:
            bot.send_message(chat_id, "Erro ao buscar títulos." if current_language == 'pt' else "Error fetching titles.")
            return
            
        soup = BeautifulSoup(page_source, 'html.parser')

        major_section = soup.select_one('#majorAchievement tbody')
        major_titles = "🏆 **Títulos Major:**\n\n" if current_language == 'pt' else "🏆 **Major Titles:**\n\n"
        if major_section:
            for row in major_section.select('tr'):
                placement = row.select_one('.placement-cell').text.strip()
                tournament = row.select_one('.tournament-name-cell a').text.strip()
                major_titles += f"• {placement} - {tournament}\n"
        else:
            major_titles += "Nenhum título encontrado.\n" if current_language == 'pt' else "No titles found.\n"

        lan_section = soup.select_one('#lanAchievement tbody')
        lan_titles = "🏅 **Títulos LAN:**\n\n" if current_language == 'pt' else "🏅 **LAN Titles:**\n\n"
        if lan_section:
            for row in lan_section.select('tr'):
                placement = row.select_one('.placement-cell').text.strip()
                tournament = row.select_one('.tournament-name-cell a').text.strip()
                lan_titles += f"• {placement} - {tournament}\n"
        else:
            lan_titles += "Nenhum título encontrado.\n" if current_language == 'pt' else "No titles found.\n"

        message = major_titles + "\n" + lan_titles
        bot.send_message(chat_id, message, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(chat_id, "Erro ao buscar títulos." if current_language == 'pt' else "Error fetching titles.")
        print(f"Erro: {e}")

@cached(cache=TTLCache(maxsize=10, ttl=1800))  # 30 minutos de cache
def send_stats(chat_id):
    """Busca e envia as estatísticas com cache."""
    try:
        url = 'https://www.hltv.org/stats/teams/players/8297/furia'
        page_source = fetch_page_source(url)
        
        if not page_source:
            bot.send_message(chat_id, "Erro ao buscar estatísticas." if current_language == 'pt' else "Error fetching stats.")
            return
            
        soup = BeautifulSoup(page_source, 'html.parser')

        stats_table = soup.select_one('.stats-table.player-ratings-table tbody')
        message = "📊 **Estatísticas dos nossos players:**\n\n" if current_language == 'pt' else "📊 **FURIA Player Stats:**\n\n"

        if stats_table:
            rows = stats_table.select('tr')
            for row in rows:
                columns = row.select('td')
                if len(columns) < 6:
                    continue

                player = columns[0].select_one('a').text.strip()
                maps_played = columns[1].text.strip()
                rounds_played = columns[2].text.strip()
                kd_diff = columns[3].text.strip()
                kd_ratio = columns[4].text.strip()
                rating = columns[5].text.strip()

                message += f"• {player}: {maps_played} mapas, {rounds_played} rounds, K-D Diff: {kd_diff}, K/D: {kd_ratio}, Rating: {rating}\n\n"

        else:
            message += "Nenhuma estatística encontrada.\n" if current_language == 'pt' else "No player stats found.\n"

        bot.send_message(chat_id, message, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(chat_id, "Erro ao buscar estatísticas." if current_language == 'pt' else "Error fetching stats.")
        print(f"Erro: {e}")

@cached(cache=TTLCache(maxsize=10, ttl=3600))  # 1 hora de cache
def send_news(chat_id):
    """Busca e envia as notícias com cache."""
    try:
        url = 'https://www.hltv.org/team/8297/furia#tab-newsBox'
        page_source = fetch_page_source(url)
        
        if not page_source:
            bot.send_message(chat_id, "Erro ao buscar notícias." if current_language == 'pt' else "Error fetching news.")
            return
            
        soup = BeautifulSoup(page_source, 'html.parser')

        news_items = soup.select('.subTab-newsArticle')
        message = "📰 **Notícias da FURIA desta semana:**\n\n" if current_language == 'pt' else "📰 **FURIA news from this week:**\n\n"

        now = datetime.now(timezone.utc)
        start_of_week = now - timedelta(days=now.weekday())

        if news_items:
            for news in news_items:
                title = news.text.strip()
                link = news.get('href')
                date_unix = int(news.select_one('.subTab-newsDate')['data-unix']) / 1000
                news_date = datetime.fromtimestamp(date_unix, timezone.utc)

                if news_date >= start_of_week:
                    date_formatted = news_date.strftime('%d/%m/%Y')
                    if current_language == 'pt':
                        message += f"📅 {date_formatted} - [{title}](https://www.hltv.org{link})\n"
                    else:
                        message += f"📅 {date_formatted} - [{title}](https://www.hltv.org{link})\n"

        if len(message.strip()) == len("📰 **Notícias da FURIA desta semana:**\n\n") or \
           len(message.strip()) == len("📰 **FURIA news from this week:**\n\n"):
            message += "Nenhuma notícia encontrada nesta semana." if current_language == 'pt' else "No news found this week."

        bot.send_message(chat_id, message, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(chat_id, "Erro ao buscar notícias." if current_language == 'pt' else "Error fetching news.")
        print(f"Erro: {e}")

@cached(cache=TTLCache(maxsize=10, ttl=3600))  # 1 hora de cache
def send_ranking(chat_id):
    """Busca e envia o ranking com cache."""
    try:
        url = "https://www.hltv.org/ranking/teams"
        page_source = fetch_page_source(url)
        
        if not page_source:
            bot.send_message(chat_id, "Erro ao buscar ranking." if current_language == 'pt' else "Error fetching ranking.")
            return
            
        soup = BeautifulSoup(page_source, "html.parser")

        rows = soup.select("div.ranked-team.standard-box")

        top_teams = []
        for row in rows[:20]:
            rank = row.select_one(".position").text.strip()
            team = row.select_one(".teamLine .name").text.strip()
            points = row.select_one(".teamLine .points").text.strip("()")

            if team.lower() == "furia":
                top_teams.append(f"{rank} - {team} ({points}) 🔥")
            else:
                top_teams.append(f"{rank} - {team} ({points})")

        if not top_teams:
            message = "Nenhum ranking encontrado." if current_language == 'pt' else "No ranking found."
        else:
            header = "🌟 **Ranking Atual:**\n\n" if current_language == 'pt' else "🌟 **Current Ranking:**\n\n"
            message = header + "\n".join(top_teams)

        bot.send_message(chat_id, message, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(chat_id, "Erro ao buscar ranking." if current_language == 'pt' else "Error fetching ranking.")
        print(f"Erro: {e}")

@cached(cache=TTLCache(maxsize=10, ttl=259200))  # 3 dias de cache (259200 segundos)
def send_camps(chat_id):
    """Busca e envia os campeonatos e colocações com cache."""
    try:
        url = 'https://www.hltv.org/stats/teams/events/8297/furia?startDate=2025-01-01&endDate=2025-12-31'
        page_source = fetch_page_source(url)
        
        if not page_source:
            bot.send_message(chat_id, "Erro ao buscar campeonatos." if current_language == 'pt' else "Error fetching events.")
            return
            
        soup = BeautifulSoup(page_source, 'html.parser')

        events_table = soup.select_one('.stats-table tbody')
        message = "🏆 **Colocações da FURIA em 2025:**\n\n" if current_language == 'pt' else "🏆 **FURIA's placements in 2025:**\n\n"

        if events_table:
            rows = events_table.select('tr')
            for row in rows:
                placement_tag = row.select_one('.statsCenterText')
                event_name_tag = row.select_one('.image-and-label span')
                event_link_tag = row.select_one('.image-and-label')

                if placement_tag and event_name_tag and event_link_tag:
                    placement = placement_tag.text.strip()
                    event_name = event_name_tag.text.strip()
                    message += f"• {placement} - [{event_name}]\n"
                else:
                    print("Elemento não encontrado em uma das linhas da tabela.")
        else:
            message += "Nenhum campeonato encontrado." if current_language == 'pt' else "No events found."

        bot.send_message(chat_id, message, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(chat_id, "Erro ao buscar campeonatos." if current_language == 'pt' else "Error fetching events.")
        print(f"Erro: {e}")

def send_social_links(chat_id):
    """Envia links para redes sociais."""
    try:
        markup = types.InlineKeyboardMarkup(row_width=2)

        buttons = [
            ("🌐 Site Oficial", "https://www.furia.gg/"),
            ("❌ X", "https://twitter.com/furiagg"),
            ("📸 Instagram", "https://www.instagram.com/furiagg/"),
            ("📺 YouTube", "https://www.youtube.com/c/FURIAgg"),
            ("📘 Facebook", "https://www.facebook.com/furiagg"),
            ("🎮 Twitch", "https://www.twitch.tv/team/furia"),
        ]

        for text, url in buttons:
            markup.add(types.InlineKeyboardButton(text, url=url))

        # Enviar mensagem com os botões
        message = "🌟 **Redes sociais e sites da FURIA:**" if current_language == 'pt' else "🌟 **FURIA's social media and websites:**"
        bot.send_message(chat_id, message, reply_markup=markup, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(chat_id, "Erro ao carregar links." if current_language == 'pt' else "Error loading links.")
        print(f"Erro: {e}")

@cached(cache=TTLCache(maxsize=10, ttl=3600))  # Cache de 1 hora
def send_maps(chat_id):
    """Busca e envia as estatísticas de mapas com cache."""
    try:
        global current_language

        # URL da página de mapas
        url = 'https://www.hltv.org/stats/teams/maps/8297/furia'
        page_source = fetch_page_source(url)  # Usa a função otimizada com cache
        soup = BeautifulSoup(page_source, 'html.parser')

        # Selecionar os mapas da pool atual
        maps_pool = soup.select('.map-pool-map-holder.map-stats')
        message = "🗺️ **Nossas vitórias nos mapas da pool atual:**\n\n" if current_language == 'pt' else "🗺️ **Current map pool played by FURIA:**\n\n"

        # Lista de mapas da pool atual
        current_pool = ["Ancient", "Anubis", "Dust2", "Inferno", "Mirage", "Nuke", "Train"]

        if maps_pool:
            for map_item in maps_pool:
                map_name = map_item.select_one('.map-pool-map-name').text.strip()
                # Separar o nome do mapa e a taxa de vitória
                if ' - ' in map_name:
                    map_name, win_rate = map_name.split(' - ')
                else:
                    continue  # Ignorar se o formato não for esperado

                # Verificar se o mapa está na pool atual
                if map_name in current_pool:
                    message += f"• {map_name}: {win_rate} de vitórias\n" if current_language == 'pt' else f"• {map_name}: {win_rate} win rate\n"
        else:
            message += "Nenhum mapa encontrado." if current_language == 'pt' else "No maps found."

        # Enviar a mensagem com os mapas
        bot.send_message(chat_id, message, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(chat_id, "Erro ao buscar mapas." if current_language == 'pt' else "Error fetching maps.")
        print(f"Erro: {e}")


# Inicializar o bot
def main():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    main()