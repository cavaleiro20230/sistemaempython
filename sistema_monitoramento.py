import os
import json
import sqlite3
import datetime
import random
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import ipaddress
from io import BytesIO

# Configuração do banco de dados
def setup_database():
    conn = sqlite3.connect('access_logs.db')
    cursor = conn.cursor()
    
    # Tabela para logs de acesso
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS access_logs (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        ip TEXT,
        url TEXT,
        user_agent TEXT,
        status_code INTEGER,
        referrer TEXT,
        username TEXT,
        country TEXT,
        city TEXT
    )
    ''')
    
    # Tabela para estatísticas agregadas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS url_stats (
        url TEXT PRIMARY KEY,
        access_count INTEGER,
        last_updated TEXT
    )
    ''')
    
    conn.commit()
    return conn

# Simulador de coleta de dados (em produção, isso seria um script JS e logs de servidor)
def generate_sample_logs(num_logs=100):
    logs = []
    
    urls = [
        "/", "/about", "/products", "/contact", "/blog", 
        "/blog/post1", "/blog/post2", "/login", "/register", "/dashboard"
    ]
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15"
    ]
    
    referrers = [
        "https://www.google.com", 
        "https://www.bing.com", 
        "https://www.facebook.com", 
        "https://www.twitter.com", 
        ""  # Acesso direto
    ]
    
    usernames = [
        None, None, None, None, None,  # 80% de acessos anônimos
        "user1", "user2", "admin", "john_doe", "jane_doe"
    ]
    
    countries = ["Brasil", "Estados Unidos", "Canadá", "México", "Argentina", "Espanha", "Portugal"]
    cities = ["São Paulo", "Rio de Janeiro", "Nova York", "Toronto", "Cidade do México", "Buenos Aires", "Madrid", "Lisboa"]
    
    # Gerar IPs aleatórios
    ips = []
    for _ in range(20):
        ip = str(ipaddress.IPv4Address(random.randint(0, 2**32-1)))
        ips.append(ip)
    
    # Gerar logs
    now = datetime.datetime.now()
    for i in range(num_logs):
        # Timestamp aleatório nas últimas 24 horas
        random_hours = random.randint(0, 24)
        random_minutes = random.randint(0, 59)
        random_seconds = random.randint(0, 59)
        timestamp = now - datetime.timedelta(
            hours=random_hours, 
            minutes=random_minutes,
            seconds=random_seconds
        )
        
        log = {
            "timestamp": timestamp.isoformat(),
            "ip": random.choice(ips),
            "url": random.choice(urls),
            "user_agent": random.choice(user_agents),
            "status_code": random.choices([200, 404, 500], weights=[0.95, 0.04, 0.01])[0],
            "referrer": random.choice(referrers),
            "username": random.choice(usernames),
            "country": random.choice(countries),
            "city": random.choice(cities)
        }
        logs.append(log)
    
    return logs

# Processador de logs
def process_logs(logs, conn):
    cursor = conn.cursor()
    
    # Inserir logs no banco de dados
    for log in logs:
        cursor.execute('''
        INSERT INTO access_logs 
        (timestamp, ip, url, user_agent, status_code, referrer, username, country, city)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log["timestamp"], 
            log["ip"], 
            log["url"], 
            log["user_agent"], 
            log["status_code"], 
            log["referrer"], 
            log["username"], 
            log["country"], 
            log["city"]
        ))
    
    # Atualizar estatísticas de URL
    cursor.execute('''
    SELECT url, COUNT(*) as count 
    FROM access_logs 
    GROUP BY url
    ''')
    
    url_stats = cursor.fetchall()
    
    for url, count in url_stats:
        cursor.execute('''
        INSERT OR REPLACE INTO url_stats (url, access_count, last_updated)
        VALUES (?, ?, ?)
        ''', (url, count, datetime.datetime.now().isoformat()))
    
    conn.commit()

# Análise e geração de relatórios
def generate_reports(conn):
    # Carregar dados em DataFrames para análise
    logs_df = pd.read_sql_query("SELECT * FROM access_logs", conn)
    
    # Converter timestamp para datetime
    logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp'])
    
    # 1. URLs mais acessadas
    top_urls = logs_df['url'].value_counts().head(5)
    print("\n=== URLs Mais Acessadas ===")
    print(top_urls)
    
    # 2. IPs com mais acessos
    top_ips = logs_df['ip'].value_counts().head(5)
    print("\n=== IPs com Mais Acessos ===")
    print(top_ips)
    
    # 3. Distribuição por país
    country_dist = logs_df['country'].value_counts()
    print("\n=== Distribuição por País ===")
    print(country_dist)
    
    # 4. Usuários autenticados mais ativos
    auth_users = logs_df[logs_df['username'].notnull()]
    if not auth_users.empty:
        top_users = auth_users['username'].value_counts().head(5)
        print("\n=== Usuários Mais Ativos ===")
        print(top_users)
    
    # 5. Códigos de status
    status_dist = logs_df['status_code'].value_counts()
    print("\n=== Distribuição de Códigos de Status ===")
    print(status_dist)
    
    # Visualizações
    plt.figure(figsize=(12, 8))
    
    # Gráfico de URLs mais acessadas
    plt.subplot(2, 2, 1)
    top_urls.plot(kind='bar')
    plt.title('URLs Mais Acessadas')
    plt.tight_layout()
    
    # Gráfico de distribuição por país
    plt.subplot(2, 2, 2)
    country_dist.plot(kind='pie', autopct='%1.1f%%')
    plt.title('Distribuição por País')
    plt.tight_layout()
    
    # Gráfico de acessos por hora do dia
    plt.subplot(2, 2, 3)
    logs_df['hour'] = logs_df['timestamp'].dt.hour
    hour_counts = logs_df['hour'].value_counts().sort_index()
    hour_counts.plot(kind='line')
    plt.title('Acessos por Hora do Dia')
    plt.xlabel('Hora')
    plt.ylabel('Número de Acessos')
    plt.tight_layout()
    
    # Gráfico de códigos de status
    plt.subplot(2, 2, 4)
    status_dist.plot(kind='bar')
    plt.title('Códigos de Status HTTP')
    plt.tight_layout()
    
    plt.savefig('dashboard.png')
    print("\nDashboard salvo como 'dashboard.png'")
    
    # Retornar o buffer da imagem para exibição
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

# Função principal
def main():
    print("Iniciando Sistema de Monitoramento de Acesso a Sites")
    
    # Configurar banco de dados
    conn = setup_database()
    print("Banco de dados configurado.")
    
    # Gerar logs de exemplo
    logs = generate_sample_logs(500)
    print(f"Gerados {len(logs)} logs de exemplo.")
    
    # Processar logs
    process_logs(logs, conn)
    print("Logs processados e armazenados no banco de dados.")
    
    # Gerar relatórios
    generate_reports(conn)
    
    # Fechar conexão
    conn.close()
    print("Sistema finalizado.")

if __name__ == "__main__":
    main()