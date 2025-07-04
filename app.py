from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

STOP_1_URL = "https://rti-anywhere.net/stop/7709/"
STOP_2_URL = "https://rti-anywhere.net/stop/5006/"
STOP_2_FILTER_ROUTES = {"14", "17", "25", "83", "32", "39", "84"}

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
  margin
