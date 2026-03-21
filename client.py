import socket
import threading
import json

def listen_to_server(client_socket):
    """Thread care asculta mereu notificarile de la server."""
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            message = json.loads(data)
            msg_type = message.get("type")
            if msg_type == "update":
                products = message.get("products", {})
                print("\n[UPDATE] Lista produse actualizata:")
                for name, info in products.items():
                    status = "Activ" if info.get("active", True) else "Expirat"
                    print(f"  {name}: Proprietar {info['owner']}, Min {info['min_price']}, Curent {info['current_price']}, {status}")
                print("> ", end="")
            elif msg_type == "notification":
                print(f"\n[NOTIFICARE] {message.get('message', 'Mesaj nou')}")
                print("> ", end="")
            elif msg_type == "error":
                print(f"\n[EROARE] {message.get('message', 'Eroare')}")
                print("> ", end="")
        except:
            print("\n[EROARE] Conexiunea cu serverul a fost pierduta.")
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('127.0.0.1', 5000))
    except:
        print("[EROARE] Nu s-a putut conecta la server.")
        return

    username = input("Introdu numele tau: ")
    login_request = {"action": "login", "username": username}
    client.sendall(json.dumps(login_request).encode('utf-8'))

    try:
        data = client.recv(1024).decode('utf-8')
        response = json.loads(data)
        if response.get("type") == "error":
            print(f"[EROARE] {response.get('message', 'Conectare esuata.')}")
            client.close()
            return
        elif response.get("type") == "welcome":
            print(f"[WELCOME] {response.get('message', 'Te-ai conectat!')}")
            products = response.get("products", {})
            print("Produse curente:")
            for name, info in products.items():
                status = "Activ" if info.get("active", True) else "Expirat"
                print(f"  {name}: Proprietar {info['owner']}, Min {info['min_price']}, Curent {info['current_price']}, {status}")
    except:
        print("[EROARE] Nu s-a putut primi raspunsul de la server.")
        client.close()
        return

    threading.Thread(target=listen_to_server, args=(client,), daemon=True).start()

    print("Te-ai conectat! Comenzi disponibile: add <nume_produs> <pret_minim>, bid <nume_produs> <pret>, list, exit")
    while True:
        cmd = input("> ")
        if cmd == "exit":
            break
        elif cmd.startswith("add "):
            parts = cmd.split()
            if len(parts) != 3:
                print("Format: add <nume_produs> <pret_minim>")
                continue
            try:
                name = parts[1]
                min_price = int(parts[2])
                request = {"action": "add_product", "name": name, "min_price": min_price}
                client.sendall(json.dumps(request).encode('utf-8'))
            except ValueError:
                print("Pretul trebuie sa fie un numar intreg.")
        elif cmd.startswith("bid "):
            parts = cmd.split()
            if len(parts) != 3:
                print("Format: bid <nume_produs> <pret>")
                continue
            try:
                prod = parts[1]
                price = int(parts[2])
                request = {"action": "bid", "product": prod, "price": price}
                client.sendall(json.dumps(request).encode('utf-8'))
            except ValueError:
                print("Pretul trebuie sa fie un numar intreg.")
        elif cmd == "list":
            request = {"action": "list"}
            client.sendall(json.dumps(request).encode('utf-8'))
        else:
            print("Comanda necunoscuta. Foloseste: add, bid, list, exit")

if __name__ == "__main__":
    start_client()