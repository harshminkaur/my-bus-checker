from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

app = Flask(__name__)

def get_buses(stop_id):
    try:
        url = f'https://rti-anywhere.net/stop/{stop_id}/'
        resp = requests.get(url, timeout=10)
        html = resp.text[:1000]  # first 1000 chars to debug if parsing fails
        soup = BeautifulSoup(resp.text, 'html.parser')
        rows = soup.select('table tbody tr')
        buses = []

        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                route = cols[0].text.strip()
                arrival = cols[1].text.strip()
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

        if not buses:
            return [{'route': 'No data', 'min': '-', 'time': html}]
        return buses

    except Exception as e:
        return [{'route': 'Error', 'min': '-', 'time': str(e)}]

@app.route('/')
@app.route('/buses')
def buses():
    s7709 = get_buses('7709')[:5]
    s5006 = [
        b for b in get_buses('5006')
        if b['route'] in {'14', '83', '84', '32x'}
        and isinstance(b['min'], int)
        and b['min'] > 4
    ][:3]

    html = '''
    <html>
    <head>
      <title>Bus Checker</title>
      <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
      <style>
        body { font-family: sans-serif; padding: 1em; background: #f7f7f7; color: #222; font-size: 18px; }
        h2 { margin-top: 1.5em; font-size: 1.2em; }
        ul { list-style: none; padding-left: 0; }
        li { margin: 0.5em 0; background: #fff; padding: 0.75em 1em; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        button {
          display: block; margin: 1em auto; padding: 10px 20px; font-size: 16px;
          background: #007bff; color: white; border: none; border-radius: 6px;
        }
      </style>
    </head>
    <body>
      <button onclick="location.reload()">🔁 Refresh</button>
      <h2>🚌 Stop 7709 – Next 5 Buses</h2>
      <ul>
        {% for b in s7709 %}
          <li><strong>Route {{b.route}}</strong>: {{b.min}} min ({{b.time}})</li>
        {% endfor %}
      </ul>

      <h2>🚌 Stop 5006 – Filtered</h2>
      <ul>
        {% for b in s5006 %}
          <li><strong>Route {{b.route}}</strong>: {{b.min}} min ({{b.time}})</li>
        {% endfor %}
      </ul>
    </body>
    </html>
    '''
    return render_template_string(html, s7709=s7709, s5006=s5006)

if __name__ == '__main__':
    app.run()
