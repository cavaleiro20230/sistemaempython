from flask import Flask, request, jsonify
import sqlite3
import json
import datetime
import requests

app = Flask(__name__)

# Função para obter geolocalização a partir do IP
def get_geolocation(ip):
    try:
        # Em produção, você usaria um serviço como MaxMind ou ipstack
        # Este é um exemplo simplificado
        response = requests.get(f"https://ipapi.co/{ip}/json/")
        if response.status_code == 200:
            data = response.json()
            return {
                'country': data.get('country_name'),
                'city': data.get('city'),
                'region': data.get('region'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude')
            }
    except Exception as e:
        print(f"Erro ao obter geolocalização: {e}")
    
    # Valores padrão se a geolocalização falhar
    return {
        'country': 'Unknown',
        'city': 'Unknown',
        'region': 'Unknown',
        'latitude': 0,
        'longitude': 0
    }

@app.route('/api/collect', methods=['POST'])
def collect_data():
    # Obter dados do request
    data = request.json
    
    # Obter IP do cliente
    client_ip = request.remote_addr
    
    # Adicionar IP aos dados
    data['ip'] = client_ip
    
    # Obter geolocalização
    geo_data = get_geolocation(client_ip)
    data.update(geo_data)
    
    # Adicionar timestamp do servidor
    data['server_timestamp'] = datetime.datetime.now().isoformat()
    
    # Conectar ao banco de dados
    conn = sqlite3.connect('access_logs.db')
    cursor = conn.cursor()
    
    # Inserir no banco de dados
    # (Na prática, você provavelmente enviaria para uma fila como Kafka primeiro)
    cursor.execute('''
    INSERT INTO access_logs 
    (timestamp, ip, url, user_agent, status_code, referrer, username, country, city)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('timestamp'),
        data.get('ip'),
        data.get('url'),
        data.get('userAgent'),
        200,  # Assumimos status 200 para eventos do cliente
        data.get('referrer'),
        data.get('username'),
        data.get('country'),
        data.get('city')
    ))
    
    conn.commit()
    conn.close()
    
    # Também poderíamos salvar os logs brutos para processamento posterior
    with open('raw_logs.jsonl', 'a') as f:
        f.write(json.dumps(data) + '\n')
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)