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
            return [{'route': 'No table found', 'min': '-', 'time': 'table#stoptimetable tbody missing'}], datetime.now(tz=nz_tz)

        rows = table.find_all('tr')
        if not rows:
            return [{'route': 'No rows found', 'min': '-', 'time': str(table)[:1000]}], datetime.now(tz=nz_tz)

        buses = []
        now = datetime.now(tz=nz_tz)

        for row in rows:
            tds = row.find_all('td')
            if len(tds) >= 5:
                route_tag = tds[0].find('a')
                route = route_tag.text.strip() if route_tag else tds[0].text.strip()
                est = tds[4].text.strip()
                sched = tds[2].text.strip()

                # Use estimated time if available
                if 'min' in est.lower():
                    try:
                        minutes = int(est.split()[0])
                        time_str = (now + timedelta(minutes=minutes)).strftime('%-I:%M %p').lower()
                    except:
                        continue
                elif est.lower() == 'due':
                    minutes = 0
                    time_str = now.strftime('%-I:%M %p').lower()
                else:
                    try:
                        sched_time = datetime.strptime(sched, "%H:%M")
                        sched_time = nz_tz.localize(sched_time.replace(year=now.year, month=now.month, day=now.day))
                        if sched_time < now:
                            sched_time += timedelta(days=1)
                        minutes = int((sched_time - now).total_seconds() / 60)
                        time_str = sched_time.strftime('%-I:%M %p').lower()
                    except:
                        continue

                buses.append({'route': route, 'min': minutes, 'time': time_str})

        if not buses:
            return [{'route': 'No usable data', 'min': '-', 'time': str(table)[:1000]}], now
        return buses, now

    except Exception as e:
        return [{'route': 'Error', 'min': '-', 'time': str(e)}], datetime.now(tz=nz_tz)

@app.route('/')
@app.route('/buses')
def buses():
    s7709, updated_time = get_buses('7709')
    s5006_raw, _ = get_buses('5006')

    s7709 = s7709[:5]
    s5006 = [
        b for b in s5006_raw
        if b['route'] in {'14', '83', '84', '32x'}
        and isinstance(b['min'], int)
        and b['min'] >= 6
    ][:8]

    now = datetime.now(tz=nz_tz)
    minutes_ago = int((now - updated_time).total_seconds() / 60)

    html = '''
    <html>
    <head>
      <title>Bus Checker</title>
      <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
      <style>
        body {
          font-family: sans-serif;
          padding: 1em;
          background: #f7f7f7;
          color: #222;
          font-size: 14px;
        }
        h2 {
          margin-top: 1.5em;
          font-size: 1.2em;
        }
        ul {
          list-style: none;
          padding-left: 0;
        }
        li {
          margin: 0.5em 0;
          background: #fff;
          padding: 0.75em 1em;
          border-radius: 8px;
          box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .route-circle {
          display: inline-block;
          width: 28px;
          height: 28px;
          line-height: 28px;
          text-align: center;
          border-radius: 50%;
          background: #28a745;
          color: white;
          font-weight: bold;
          margin-right: 0.6em;
          font-size: 13px;
        }
        .subtitle {
          font-size: 12px;
          color: #666;
          margin-top: 4px;
        }
        .updated {
          text-align: center;
          margin: 0.5em 0 0.3em 0;
          font-size: 13px;
          color: #666;
        }
      </style>
      <script>
        // Live update timer
        document.addEventListener('DOMContentLoaded', function() {
          const el = document.getElementById('last-updated');
          const started = new Date().getTime();
          function update() {
            const now = new Date().getTime();
            const diffMin = Math.floor((now - started) / 60000);
            el.textContent = "Last updated " + diffMin + " minute" + (diffMin !== 1 ? "s" : "") + " ago";
          }
          update();
          setInterval(update, 60000);
        });
      </script>
    </head>
    <body>
      <div class="updated" id="last-updated">
        Last updated {{minutes_ago}} minute{{ 's' if minutes_ago != 1 else '' }} ago
      </div>

      <h2>Willis Street</h2>
      <ul>
        {% for b in s7709 %}
          <li>
            <span class="route-circle">{{b.route}}</span>
            {{b.min}} minutes away
            <div class="subtitle">Scheduled for {{b.time}}</div>
          </li>
        {% endfor %}
      </ul>

      <h2>Manners Street</h2>
      <ul>
        {% for b in s5006 %}
          <li>
            <span class="route-circle">{{b.route}}</span>
            {{b.min}} minutes away
            <div class="subtitle">Scheduled for {{b.time}}</div>
          </li>
        {% endfor %}
      </ul>
    </body>
    </html>
    '''
    return render_template_string(html, s7709=s7709, s5006=s5006, minutes_ago=minutes_ago)

if __name__ == '__main__':
    app.run()
