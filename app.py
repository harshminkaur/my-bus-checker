from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

app = Flask(__name__)

def get_buses(stop_id):
    url = f'https://rti-anywhere.net/stop/{stop_id}/'
    resp = requests.get(url, timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')
    rows = soup.select('table tbody tr')
    buses = []
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 2:
            route = cols[0].text.strip()
            arrival = cols[1].text.strip()
            minutes = 0
            if 'min' in arrival:
                try:
                    minutes = int(arrival.split()[0])
                except:
                    continue
            elif arrival.lower() == 'due':
                minutes = 0
            else:
                continue
            time_str = (datetime.now() + timedelta(minutes=minutes)).strftime('%H:%M')
            buses.append({'route': route, 'min': minutes, 'time': time_str})
    return buses

@app.route('/')
@app.route('/buses')
def buses():
    s7709 = get_buses('7709')[:5]
    s5006 = [b for b in get_buses('5006') if b['route'] in {'14','83','84','32x'} and b['min'] > 4][:3]

    html = '''
    <html>
    <head>
      <title>Bus Checker</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        h2 { color: #333; }
        .stop { margin-bottom: 30px; }
        .card {
          background: white;
          padding: 15px 20px;
          margin: 10px 0;
          border-radius: 8px;
          box-shadow: 0 2px 5px rgba(0,0,0,0.1);
          font-size: 18px;
          display: flex;
          justify-content: space-between;
          font-weight: 600;
        }
        button {
          background: #0066cc;
          color: white;
          border: none;
          border-radius: 6px;
          padding: 10px 20px;
          font-size: 16px;
          cursor: pointer;
          margin-bottom: 20px;
          box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
        button:hover {
          background: #004a99;
        }
      </style>
    </head>
    <body>
      <button onclick="location.reload()">🔁 Refresh</button>
      <div class="stop">
        <h2>🚌 Stop 7709 – Next 5 Buses</h2>
        {% for b in s7709 %}
          <div class="card">
            <span>Route {{b.route}}</span>
            <span>{{b.min}} min • {{b.time}}</span>
          </div>
        {% endfor %}
      </div>
      <div class="stop">
        <h2>🚌 Stop 5006 – Filtered</h2>
        {% for b in s5006 %}
          <div class="card">
            <span>Route {{b.route}}</span>
            <span>{{b.min}} min • {{b.time}}</span>
          </div>
        {% endfor %}
      </div>
    </body>
    </html>
    '''
    return render_template_string(html, s7709=s7709, s5006=s5006)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
