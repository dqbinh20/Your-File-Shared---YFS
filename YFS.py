import socket
import select
import threading
import json
import os

# mutex is used to manage access timestamp and Vector process
mutex = threading.Lock()

# List of machines addresses
process_addr = {
    "A": ("localhost", 4001),
    "B": ("localhost", 4002),
    "C": ("localhost", 4003),
    "D": ("localhost", 4004),
    "E": ("localhost", 4005)
}

class Process:
    def __init__(self, name):
        self.name = name
        self.addr = {
            "A": ("localhost", 4001),
            "B": ("localhost", 4002),
            "C": ("localhost", 4003),
            "D": ("localhost", 4004),
            "E": ("localhost", 4005)
        }[name]
        self.timestamp = {
            "A": 0,
            "B": 0,
            "C": 0,
            "D": 0,
            "E": 0
        }
        self.buffer = []
        self.V_P = {}
        self.running = True

    def merge_timestamp(self, a, b):
        for key in a.keys() & b.keys():
            a[key] = max(a[key], b[key])

    def log_message(self, message, description):
        with open("./" + self.name + "/log.txt", "a") as log_file:
            log_file.write(f"{description}\n")
            if message and "type" in message:
                log_file.write(f"- Type message: {message['type']}\n")

            log_file.write(f"- Vector time current: {self.timestamp}\n")

            if message and "time" in message:
                log_file.write(f"- Vector time message: {message['time']}\n")

            log_file.write(f"- Vector time process current:\n")
            for VT in self.V_P.items():
                log_file.write(f"-- {VT}\n")

            if message and "vector_process" in message:
                log_file.write(f"- Vector time process message:\n")
                for VT in message["vector_process"].items():
                    log_file.write(f"-- {VT}\n")

            if message and "text" in message:
                log_file.write(f"- Text: {message['text']}\n")

            log_file.write("\n\n")

    def execute_buffer(self):
        exist_message_executed = False
        for message in self.buffer:
            # ses_multicast
            # check deliver
            is_deliver = True
            if self.name in message["vector_process"]:
                tM = message["vector_process"][self.name]
                for key, value in self.timestamp.items():
                    if (value) < tM[key]:
                        is_deliver = False
                        break
            if is_deliver == False: continue

            ####### ###### if is deliver ########## ###### ####
            self.log_message(message, f"Deliver message from {message['name']}")

            exist_message_executed = True
            # update timestamp and vector process
            self.merge_timestamp(self.timestamp, message["time"])
            self.timestamp[self.name] += 1
            vtM = message["vector_process"]
            for key, value in vtM.items():
                if key == self.name: continue
                if key in self.V_P: self.merge_timestamp(self.V_P[key], vtM[key])
                else: self.V_P[key] = value
            self.log_message(None, f"After deliver message from {message['name']}")

            # write mode
            if (message["type"] == "write"):
                # noticfy process
                notice = "{\"type\": \"notice\", \"text\": \"Data from " + self.name + " is old\"}"
                for process, addr in process_addr.items():
                    if (process != self.name):
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
                                c.connect(addr)
                                c.sendall(notice.encode())
                        except:
                            pass
                # write to file
                with open("./" + self.name + "/file.txt", "a") as file:
                    file.write(message["text"])
            # read mode
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
                    c.connect(process_addr[message["name"]])
                    with open("./" + self.name + "/file.txt", "r") as file:
                        mess = "{\"type\": \"file\",\"name\": \"" + self.name + "\",\"text\":\"" + file.read() + "\"}"
                        c.sendall(mess.encode())
            self.buffer.remove(message)
        return exist_message_executed

    def handle_client(self, client):
        data = client.recv(1024)
        message = json.loads(data.decode())

        if (message["type"] == "notice"):
            print("\n --- " + message["text"] + "\n --- input your request: ", end="")
            return
        if (message["type"] == "file"):
            os.makedirs("./" + self.name + "/" + message["name"], exist_ok=True)
            with open("./" + self.name + "/" + message["name"] + "/file.txt", "w") as file:
                file.write(message["text"])
            return

        self.buffer.append(message)

        mutex.acquire()
        while self.execute_buffer(): pass
        mutex.release()

    def create_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(self.addr)
            server.setblocking(0)
            server.listen(5)
            # listenning connect
            inputs = [server]
            while self.running:
                readable, _, _ = select.select(inputs, [], [], 1)
                for fd in readable:
                    if fd is server:
                        conn, addr = fd.accept()
                        inputs.append(conn)
                    else:
                        self.handle_client(fd)
                        fd.close()
                        inputs.remove(fd)

    def send_request(self):
        while True:
            request = input(" --- input your request: ")
            if request == "exit":
                self.running = False
                break
            
            mutex.acquire()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect(process_addr[request[2]])
                self.timestamp[self.name] += 1  # update timestamp
                message = {
                    "type": "read" if request[0] == "R" else "write",
                    "name": self.name,
                    "text": request[4:],
                    "time": self.timestamp,
                    "vector_process": self.V_P
                }
                self.log_message(message, f"Sending to process {request[2]} : ")
                client.sendall(json.dumps(message).encode())
                self.V_P[request[2]] = self.timestamp.copy()
                
            mutex.release()
    def create_file_folder(self):
        os.makedirs("./" + self.name, exist_ok=True)
        file = open("./" + self.name + "/file.txt", "a")
        file.close()

if __name__ == "__main__":
    # User input name from console : A/B/C/D
    name = input("Name process: ")

    # init Process with name
    process = Process(name)

    # create folder and file for other machines to mount
    process.create_file_folder()

    # Print to console how to create the command
    print("****** Format input: R/W B/C/D/E (text if is W mode) ******")
    print("******               Example: R B abc                ******", end="\n\n")

    # Create threading to listend request form machines
    server_thread = threading.Thread(target=process.create_server)
    server_thread.start()

    # Listening request from user
    process.send_request()