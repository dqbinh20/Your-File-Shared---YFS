import socket
import select
import threading
import json
import os

V_P = {}
running = True

process_addr = {
    "A": ("localhost", 4001),
    "B": ("localhost", 4002),
    "C": ("localhost", 4003),
    "D": ("localhost", 4004),
    "E": ("localhost", 4005)
}

timestamp = {
    "A": 0,
    "B": 0,
    "C": 0,
    "D": 0,
    "E": 0
}

buffer = []

name = input("Name process: ")

PORT = process_addr[name][1]

def merge_timestamp(a, b):
    for key in a.keys() & b.keys():
        a[key] = max(a[key], b[key])

def log_message(message, description):
    with open("./" + name + "/log.txt", "a") as log_file:
        log_file.write(f"{description}\n")
        if message and "type" in message:
            log_file.write(f"- Type message: {message["type"]}\n")

        log_file.write(f"- Vector time current: {timestamp}\n")
        
        if message and "time" in message:
            log_file.write(f"- Vector time message: {message["time"]}\n")
        
        log_file.write(f"- Vector time process current:\n")
        for VT in V_P.items():
            log_file.write(f"-- {VT}\n")
        
        if message and "vector_process" in message:
            log_file.write(f"- Vector time process message:\n")
            for VT in message["vector_process"].items():
                log_file.write(f"-- {VT}\n")
        
        if message and "text" in message:
            log_file.write(f"- Text: {message["text"]}\n")
        
        log_file.write("\n\n")

def execute_buffer():
    exist_message_executed = False
    for message in buffer:
        ## ses_multicast
        # check deliver
        is_deliver = True
        if name in message["vector_process"]:
            tM = message["vector_process"][name]
            for key, value in timestamp.items():
                if (value) < tM[key]: 
                    is_deliver = False
                    break
        if is_deliver == False: continue

        ####### ###### if is deliver ########## ###### ####
        log_message(message, f"Deliver message from {message["name"]}")

        exist_message_executed = True
        # update timestamp and vector process
        merge_timestamp(timestamp,message["time"])
        timestamp[name] += 1
        vtM = message["vector_process"]
        for key,value in vtM.items():
            if key == name: continue
            if key in V_P: merge_timestamp(V_P[key],vtM[key])
            else: V_P[key] = value
        log_message(None,f"After deliver message from {message["name"]}")     

        # write mode
        if (message["type"] == "write"):
            ## noticfy process
            notice = "{\"type\": \"notice\", \"text\": \"Data from "+ name +" is old\"}"
            for process, addr in process_addr.items():
                if (process != name) : 
                    try: 
                        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as c:
                            c.connect(addr)
                            c.sendall(notice.encode())
                    except:
                        pass
            ## write to file
            with open("./" + name + "/file.txt","a") as file:
                file.write(message["text"])
        # read mode
        else: 
            with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as c:
                c.connect(process_addr[message["name"]])
                with open("./" + name + "/file.txt","r") as file:
                    mess = "{\"type\": \"file\",\"name\": \""+ name +"\",\"text\":\"" + file.read() + "\"}"
                    c.sendall(mess.encode())
        buffer.remove(message)
    return exist_message_executed

def handle_client(client):
    data = client.recv(1024)
    message = json.loads(data.decode())
    
    if (message["type"]=="notice"):
        print("\n --- " + message["text"] + "\n --- input your request: ",end="")
        return
    if (message["type"]=="file"):
        os.makedirs("./"+ name + "/" + message["name"],exist_ok=True) 
        with open("./"+ name + "/" + message["name"] + "/file.txt","w") as file:
            file.write(message["text"])
        return
    
    buffer.append(message)
    while execute_buffer(): pass

def create_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server: 
        server.bind(("localhost", PORT))
        server.setblocking(0)
        server.listen(5)
        # listenning connect
        inputs = [server] 
        while running:
            readable, _, _ = select.select(inputs,[],[],2)
            for fd in readable:
                if fd is server:
                    conn, addr = fd.accept()
                    inputs.append(conn)
                else:
                    # client send data
                    handle_client(fd)
                    fd.close()
                    inputs.remove(fd)   

def send_request():
    while True:
        request = input(" --- input your request: ")
        if request=="exit":
            global running
            running = False
            break

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect(process_addr[request[2]])
            timestamp[name]+=1 # update timestamp
            message = {
                "type": "read" if request[0]=="R" else "write",
                "name": name,
                "text": request[4:],
                "time": timestamp,
                "vector_process": V_P
            }
            log_message(message, f"Sending to process {request[2]} : ")
            client.sendall(json.dumps(message).encode())
            V_P[request[2]] = timestamp.copy()

def create_file_folder():
    os.makedirs("./"+name,exist_ok=True)
    file = open("./" + name + "/file.txt","a")
    file.close()

if __name__ == "__main__":

    create_file_folder()
    print("****** Format input: R/W B/C/D/E (text if is W mode) ******")
    print("******               Example: R B abc                ******", end="\n\n")

    server_thread = threading.Thread(target=create_server)
    server_thread.start()

    send_request()
