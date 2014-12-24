from flask import Flask, render_template, session, redirect, url_for, request
from flask.ext.socketio import SocketIO, emit

import base64
import httplib
import json
import optparse
import os


ORDERS_DIRECTORY = "orders"
app = Flask(__name__)
app.config['SECRET_KEY'] = 'somesecret'
app.debug = True
socketio = SocketIO(app)

products = {
    "key": {
        "name": "key",
        "nicename": "USB Key",
        "description": "Secure your bitcoins with this handsome USB Key.",
        "img": "key.jpg",
        "price": 0.042,
     },
    "shirt": {
        "name": "shirt",
        "nicename": "T-Shirt",
        "description": "Wear this good-looking t-shirt.",
        "img": "shirt.jpg",
        "price": 0.084,
     },
}

options = {}

def armoryd_request(method, params):
    subdir = "testnet3"
    conf = os.path.join(os.getenv('HOME'), '.armory', subdir, "armoryd.conf")
    user_pass = open(conf, 'r').read()
    port = 18225
    if options.mainnet:
        port = 8225
    c = httplib.HTTPConnection("localhost", port)
    data = {"jsonrpc":"1.0","id":1,"method":method,"params":params}
    serialized = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
        "Content-Length":len(serialized),
        "Authorization":"Basic " + base64.b64encode(user_pass),
    }
    c.request("POST","/", serialized, headers)
    response = json.loads(c.getresponse().read())
    return response["result"]

@app.route("/")
def home():
    return render_template("home.html", products=products.values())


@app.route("/product/<path:product>")
def product(product):
    return render_template("product.html", product=products[product])

@app.route("/cart")
def cart():
    if not session.get("cart"):
        session["cart"] = {}
    p = {}
    total = 0
    for product, quantity in session["cart"].items():
        if quantity > 0:
            s = products[product]["price"] * quantity
            p[product] = {
                "name": product,
                "nicename": products[product]["nicename"],
                "price": products[product]["price"],
                "quantity": quantity,
                "total": s,
            }
            total += s
    return render_template("cart.html", products=p.values(), total=total)

@app.route("/ship")
def ship():
    if not session.get("ship"):
        session["ship"] = {}

    if not session.get("cart") or len(session["cart"]) == 0:
        return redirect(url_for('cart'))
    total = 0
    for product, quantity in session["cart"].items():
        if quantity > 0:
            s = products[product]["price"] * quantity
            total += s
    return render_template("ship.html", ship=session["ship"], total=total)

@app.route("/pay")
def pay():
    if not session.get("cart") or len(session["cart"]) == 0:
        return redirect(url_for('cart'))
    if not session.get("ship") or not session["ship"].get("address"):
        return redirect(url_for('ship'))

    if not session.get("bitcoinaddress"):
        if options.lockbox:
            wallets = armoryd_request("listloadedwallets", [])
            args = [2,3]
            for key in sorted(wallets.keys()):
                args.append(wallets[key])
            lockbox = armoryd_request("createlockbox", args)
            session["bitcoinaddress"] = lockbox["p2shaddr"]
        else:
            session["bitcoinaddress"] = armoryd_request("getnewaddress",[])

    total = 0
    for product, quantity in session["cart"].items():
        if quantity > 0:
            s = products[product]["price"] * quantity
            total += s
    # record the order
    f = open(os.path.join(ORDERS_DIRECTORY,session["bitcoinaddress"]), "w")
    data = dict(cart=session["cart"],ship=session["ship"],bitcoinaddress=session["bitcoinaddress"],total=total)
    f.write(json.dumps(data, indent=4, sort_keys=True))
    f.close()
    return render_template(
        "pay.html", ship=session["ship"], total=total,
        bitcoinaddress=session["bitcoinaddress"])

@app.route("/check/<path:address>")
def check(address):
    amount = armoryd_request("getreceivedbyaddress", address)
    return amount

@app.route("/add/<path:product>/<path:quantity>")
def add(product, quantity):
    if not session.get("cart"):
        session["cart"] = {product:0}
    if not session["cart"].get(product):
        session["cart"][product] = 0
    session["cart"][product] += int(quantity)
    return "success"

@app.route("/update/<path:product>/<path:quantity>")
def update(product, quantity):
    if not session.get("cart"):
        session["cart"] = {product:0}
    if not session["cart"].get(product):
        session["cart"][product] = 0
    session["cart"][product] = int(quantity)
    return "success"

@app.route("/remove/<path:product>")
def remove(product):
    if not session.get("cart"):
        session["cart"] = {product:0}
    if not session["cart"].get(product):
        session["cart"][product] = 0
    session["cart"][product] = 0
    return "success"

@app.route("/address", methods=['POST'])
def address():
    if not session["ship"]:
        session["ship"] = {}
    session["ship"]["address"] = request.form['address']
    return "success"

@app.route("/reset")
def reset():
    session["bitcoinaddress"] = None
    session["cart"] = None
    return "success"

@socketio.on('connect', namespace='/ws')
def ws_connect():
    emit('connected', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/ws')
def ws_disconnect():
    print 'Client disconnected'

@socketio.on('listen', namespace='/ws')
def ws_listen(message):
    address = message['bitcoinaddress']
    amount = message['amount']
    # wait until we receive something
    received = 0
    while received < amount:
        old_received = received
        received = armoryd_request("getreceivedbyaddress", [address, 0])
        if old_received != received:
            emit('broadcast', {'data': "received %s" % received})
    emit('broadcast', {'data': "paid"})


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-m", "--mainnet", action="store_true", dest="mainnet",
                      default=False, help="connect to mainnet")
    parser.add_option("-l", "--lockbox", action="store_true", dest="lockbox",
                      default=False, help="Use a 2 of 3 lockbox")
    options, args = parser.parse_args()
    socketio.run(app,host="0.0.0.0")
