from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
nz_tz = pytz.timezone('Pacific/Auckland')

def get_buses(stop_id):
    try:
        url = f'https://rti-anywhere.net/stop/{stop_id}/'
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.select_one('table#stoptimetable tbody')

        if not table:
            return [{'route': 'No table found', 'min': '-', 'time': 'table#stoptimetable tbody missing'}]

        rows = table.find_all('tr')
        if not rows:
            return [{'route': 'No rows found', 'min': '-', 'time': str(table)[:1000]}]

        buses = []
        for row in rows:
            tds = row.find_all('td')
            if len(tds) >= 5:
                route_tag = tds[0].find('a')
                route = route_tag.text.strip() if route_tag else tds[0].text.strip()
                est = tds[4].text.strip()
                sched = tds[2].text.strip()

                now = datetime.now(tz=nz_tz)

                # Use estimated time if available
                if 'min' in est.lower():
                    try:
                        minutes = int(est.split()[0])
                        time_str = (now + timedelta(minutes=minutes)).strftime('%H:%M')
                    except:
                        continue
                elif est.lower() == 'due':
                    minutes = 0
                    time_str = now.strftime('%H:%M')
                else:
                    # fallback: calculate minutes from scheduled time
                    try:
                        sched_time = datetime.strptime(sched, "%H:%M")
                        sched_time = nz_tz.localize(sched_time.replace(year=now.year, month=now.month, day=now.day))
                        if sched_time < now:
                            sched_time += timedelta(days=1)
                        minutes = int((sched_time - now).total_seconds() / 60)
                        time_str = sched_time.strftime('%H:%M')
                    except:
                        continue

                buses.append({'route': route, 'min': minutes, 'time': time_str})

        if not buses:
            return [{'route': 'No usable data', 'min': '-', 'time': str(table)[:1000]}]
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
    ][:8]  # updated to 8 buses

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
          background: #28a745; color: white; border: none; border-radius: 6px;
        }
      </style>
    </head>
    <body>
      <button onclick="location.reload()">Refresh</button>

      <h2>Willis Street</h2>
      <ul>
        {% for b in s7709 %}
          <li><strong>Route {{b.route}}</strong>: {{b.min}} min ({{b.time}})</li>
        {% endfor %}
      </ul>

      <h2>Manners Street</h2>
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
