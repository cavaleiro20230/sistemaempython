from flask import Flask, render_template, jsonify
import sqlite3
import pandas as pd
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__, template_folder='templates')

def get_db_connection():
    conn = sqlite3.connect('access_logs.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/stats/urls')
def url_stats():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT url, COUNT(*) as count FROM access_logs GROUP BY url ORDER BY count DESC LIMIT 10", conn)
    conn.close()
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/stats/ips')
def ip_stats():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT ip, COUNT(*) as count FROM access_logs GROUP BY ip ORDER BY count DESC LIMIT 10", conn)
    conn.close()
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/stats/countries')
def country_stats():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT country, COUNT(*) as count FROM access_logs GROUP BY country ORDER BY count DESC", conn)
    conn.close()
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/stats/users')
def user_stats():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT username, COUNT(*) as count FROM access_logs WHERE username IS NOT NULL GROUP BY username ORDER BY count DESC", conn)
    conn.close()
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/stats/hourly')
def hourly_stats():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM access_logs", conn)
    conn.close()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    hourly_counts = df['hour'].value_counts().sort_index()
    
    result = []
    for hour, count in hourly_counts.items():
        result.append({'hour': int(hour), 'count': int(count)})
    
    return jsonify(result)

@app.route('/api/chart/countries')
def country_chart():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT country, COUNT(*) as count FROM access_logs GROUP BY country ORDER BY count DESC", conn)
    conn.close()
    
    plt.figure(figsize=(8, 8))
    plt.pie(df['count'], labels=df['country'], autopct='%1.1f%%')
    plt.title('Distribuição de Acessos por País')
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return jsonify({'image': f'data:image/png;base64,{img_base64}'})

if __name__ == '__main__':
    app.run(debug=True, port=5001)