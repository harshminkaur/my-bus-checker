from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys

app = Flask(__name__)

STOP_1_URL = "https://rti-anywhere.net/stop/7709/"
STOP_2_URL = "https://rti-anywhere.net/stop/5006/"
STOP_2_FILTER_ROUTES = {"14", "32X", "83", "84"}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en-nz">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Bus Times</title>
  <style>
    body {
      font-family: sans-serif;
      padding: 1em;
      background: #f7f7f7;
      color: #222;
      font-size: 13px;
      margin: 0;
    }
    h2 {
      margin-top: 1.1em;
      font-size: 1.1em;
    }
    ul {
      list-style: none;
      padding-left: 0;
      margin-top: 0.3em;
    }
    li {
      margin: 0.75em 0;
      background: #fff;
      padding: 0.75em 1em;
      border-radius: 10px;
      border: 1.5px solid #999;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
      transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .subtitle {
      font-size: 11px;
      color: #666;
      margin-top: 3px;
    }
    .route-circle {
      display: inline-block;
      width: 26px;
      height: 26px;
      line-height: 26px;
      text-align: center;
      border-radius: 50%;
      font-weight: bold;
      margin-right: 0.5em;
      font-size: 12px;
    }

    /* Route-specific styling */
    .route-7 {
      background: purple;
      color: white;
    }
    .route-14, .route-17, .route-25, .route-83 {
      background: #007ab0;
      color: white;
    }
    .route-32, .route-39, .route-84 {
      background: #ccc;
      color: black;
    }

    .updated {
      text-align: center;
      margin: 0.4em 0 0.2em 0;
      font-size: 12px;
      color: #666;
    }
  </style>
</head>
<body>

<div class="updated" id="last-updated">Last updated 0 minutes ago</div>

<h2>Willis Street</h2>
<ul>
  {% for bus in stop1_buses %}
  <li>
    <span class="route-circle route-{{ bus.route_class }}">{{ bus.route }}</span>
    {{ bus.minutes }} minutes away
    <div class="subtitle">Scheduled for {{ bus.sched_time }}</div>
  </li>
  {% endfor %}
</ul>

<h2>Manners Street</h2>
<ul>
  {% for bus in stop2_buses %}
  <li>
    <span class="route-circle route-{{ bus.route_class }}">{{ bus.route }}</span>
    {{ bus.minutes }} minutes away
    <div class="subtitle">Scheduled for {{ bus.sched_time }}</div>
  </li>
  {% endfor %}
</ul>

<script>
const el = document.getElementById('last-updated');
const started = new Date().getTime();
function update() {
  const now = new Date().getTime();
  const diffMin = Math.floor((now - started) / 60000);
  el.textContent = "Last updated " + diffMin + " minute" + (diffMin !== 1 ? "s" : "") + " ago";
}
update();
setInterval(update, 60000);
</script>

</body>
</html>
"""

def normalize_route(route_str):
    return route_str.strip().lower()

def parse_stop(url, filter_routes=None, min_minutes=0, max_buses=None):
    r = requests.get(url)
    if r.status_code != 200:
        sys.stderr.write(f"Failed
