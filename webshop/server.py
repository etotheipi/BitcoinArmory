from flask import Flask, render_template, session, redirect, url_for, request
from flask.ext.socketio import SocketIO, emit

import argparse
import base64
import httplib
import json
import os
import sys


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
lockbox_args = None

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
        if lockbox_args:
            lockbox = armoryd_request("createlockbox", lockbox_args)
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

@app.route("/email", methods=['POST'])
def email():
    if not session["ship"]:
        session["ship"] = {}
    session["ship"]["email"] = request.form['email']
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--mainnet", action="store_true", default=False,
                        help="connect to mainnet")
    parser.add_argument("--lockbox", action="store", default=None,
                        help="Comma-separated list of wallets to use for an m-of-n lockbox to receive payment. There should be n elements.")
    parser.add_argument("-m", action="store", type=int, default=2,
                        help="M in m-of-n for the lockbox. M is the number of signatures required to unlock funds.")
    options = parser.parse_args()
    # check that the lockboxes are vaild
    if options.lockbox:
        lockboxes = options.lockbox.split(",")
        if len(lockboxes) < options.m:
            print "There are only %s lockboxes when you need at least %s" % (len(lockboxes), options.m)
            sys.exit()
        lockbox_args = [options.m, len(lockboxes)]
        # make sure the wallets in the lockbox list are valid
        wallets = armoryd_request("listloadedwallets", [])
        wallet_lookup = { v:True for v in wallets.values() }
        for lockbox in lockboxes:
            if not wallet_lookup.get(lockbox):
                print "%s is not a valid wallet to create a lockbox" % lockbox
                sys.exit()
            lockbox_args.append(lockbox)

    socketio.run(app,host="0.0.0.0")
