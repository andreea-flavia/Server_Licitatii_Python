import socket
import threading
import json
import time

HOST = '0.0.0.0'  
PORT = 5000
LICITATIE_DURATION = 60 



# COMENZI TESTARE:
# 1. Creare imagine:   docker build -t server-licitatie .
# 2. Pornire server:   docker run -p 5000:5000 server-licitatie
# 3. Pornire client:   python client.py (in terminale NOI)
# *Oprire containere (in caz de eroare port): docker stop $(docker ps -q)

# docker system prune -a -f
# docker compose up --build

products = {}
clients = {}

data_lock = threading.Lock()

def broadcast(message):
    msg_encoded = json.dumps(message).encode('utf-8')
    with data_lock:
        for name, conn in clients.items():
            try:
                conn.sendall(msg_encoded)
            except:
                pass

def end_auction(product_name):
    with data_lock:
        if product_name in products:
            products[product_name]['active'] = False
            print(f"[SERVER] Licitatia pentru '{product_name}' s-a incheiat.")
    
    broadcast({
        "type": "notification",
        "message": f"Licitatia pentru produsul '{product_name}' a expirat!"
    })
    time.sleep(0.1)
    broadcast({
        "type": "update",
        "products": products
    })

def handle_client(conn, addr):
    username = None
    print(f"[SERVER] Conexiune noua de la {addr}")
    
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            
            request = json.loads(data)
            action = request.get("action")

            if action == "login":
                user_attempt = request.get("username")
                with data_lock:
                    if user_attempt in clients:
                        conn.sendall(json.dumps({"type": "error", "message": "Nume deja folosit!"}).encode('utf-8'))
                        return 
                    else:
                        username = user_attempt
                        clients[username] = conn
                        print(f"[SERVER] {username} s-a logat cu succes.")
                        conn.sendall(json.dumps({
                            "type": "welcome", 
                            "message": "Te-ai conectat!",
                            "products": products 
                        }).encode('utf-8'))
            
            elif action == "add_product":
                if username is None:
                    conn.sendall(json.dumps({"type": "error", "message": "Trebuie sa te loghezi mai intai!"}).encode('utf-8'))
                    continue
                prod_name = request.get("name")
                min_price = request.get("min_price")
                if not prod_name or not isinstance(min_price, int) or min_price <= 0:
                    conn.sendall(json.dumps({"type": "error", "message": "Date invalide pentru produs!"}).encode('utf-8'))
                    continue
                with data_lock:
                    if prod_name in products:
                        conn.sendall(json.dumps({"type": "error", "message": "Nume produs deja existent!"}).encode('utf-8'))
                        continue
                    products[prod_name] = {
                        "owner": username,
                        "min_price": min_price,
                        "current_price": min_price,
                        "bidders": [],
                        "active": True
                    }
                    timer = threading.Timer(LICITATIE_DURATION, end_auction, args=(prod_name,))
                    timer.start()
                    print(f"[SERVER] Produs '{prod_name}' adaugat de {username}.")
                broadcast({
                    "type": "notification",
                    "message": f"Produs nou: '{prod_name}' cu pret minim {min_price} de catre {username}."
                })
                time.sleep(0.1)
                broadcast({
                    "type": "update",
                    "products": products
                })
            
            elif action == "bid":
                if username is None:
                    conn.sendall(json.dumps({"type": "error", "message": "Trebuie sa te loghezi mai intai!"}).encode('utf-8'))
                    continue
                prod_name = request.get("product")
                bid_price = request.get("price")
                if not prod_name or not isinstance(bid_price, int) or bid_price <= 0:
                    conn.sendall(json.dumps({"type": "error", "message": "Date invalide pentru oferta!"}).encode('utf-8'))
                    continue
                with data_lock:
                    if prod_name not in products or not products[prod_name]["active"]:
                        conn.sendall(json.dumps({"type": "error", "message": "Produs inexistent sau licitatie expirata!"}).encode('utf-8'))
                        continue
                    if bid_price <= products[prod_name]["current_price"]:
                        conn.sendall(json.dumps({"type": "error", "message": "Oferta prea mica!"}).encode('utf-8'))
                        continue
                    products[prod_name]["current_price"] = bid_price
                    previous_bidders = products[prod_name]["bidders"][:]  
                    if username not in products[prod_name]["bidders"]:
                        products[prod_name]["bidders"].append(username)
                    print(f"[SERVER] Oferta {bid_price} pentru '{prod_name}' de catre {username}.")
                owner = products[prod_name]["owner"]
                notify_clients = set([owner] + previous_bidders)
                for client_name in notify_clients:
                    if client_name in clients:
                        try:
                            clients[client_name].sendall(json.dumps({
                                "type": "notification",
                                "message": f"Oferta noua: {bid_price} pentru '{prod_name}' de catre {username}."
                            }).encode('utf-8'))
                        except:
                            pass
                time.sleep(0.1)
                broadcast({
                    "type": "update",
                    "products": products
                })
            
            elif action == "list":
                conn.sendall(json.dumps({
                    "type": "update",
                    "products": products
                }).encode('utf-8'))
            
            else:
                conn.sendall(json.dumps({"type": "error", "message": "Actiune necunoscuta!"}).encode('utf-8'))
    
    except Exception as e:
        print(f"[SERVER] Eroare la clientul {username}: {e}")
    finally:
        with data_lock:
            if username in clients:
                del clients[username]
        conn.close()
        print(f"[SERVER] Clientul {username} s-a deconectat.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Serverul de licitatii a pornit pe portul {PORT}...")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()