import socket
import time
import csv
import numpy as np
import threading
from datetime import datetime

class StreamingLatencyCollector:
    def __init__(self, port=9999, window_size=5, output_file="latencies_stream.csv"):
        self.port = port
        self.window_size = window_size
        self.output_file = output_file
        self.latencies = []
        self.window_start = time.time()
        self.running = True
        self.lock = threading.Lock()
        self.total_requests = 0
        self.total_windows = 0
        
        # Initialize CSV
        with open(self.output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',
                'window_start', 
                'window_end',
                'duration_s',
                'count',
                'throughput_rps',
                'avg_ms',
                'min_ms',
                'p50_ms',
                'p90_ms',
                'p95_ms',
                'p99_ms',
                'max_ms',
                'stdev_ms'
            ])
        
        print(f"=" * 60)
        print(f"  Streaming Latency Collector")
        print(f"=" * 60)
        print(f"  Port:        {self.port}")
        print(f"  Window size: {self.window_size}s")
        print(f"  Output:      {self.output_file}")
        print(f"=" * 60)
        print()
    
    def flush_window(self):
        """Flush current window to CSV"""
        with self.lock:
            if not self.latencies:
                return
            
            latencies_array = np.array(self.latencies)
            count = len(latencies_array)
            
            window_end = time.time()
            window_duration = window_end - self.window_start
            timestamp = window_end
            window_start_str = datetime.fromtimestamp(self.window_start).strftime('%Y-%m-%d %H:%M:%S')
            window_end_str = datetime.fromtimestamp(window_end).strftime('%Y-%m-%d %H:%M:%S')
            
            avg = np.mean(latencies_array)
            min_lat = np.min(latencies_array)
            p50 = np.percentile(latencies_array, 50)
            p90 = np.percentile(latencies_array, 90)
            p95 = np.percentile(latencies_array, 95)
            p99 = np.percentile(latencies_array, 99)
            max_lat = np.max(latencies_array)
            stdev = np.std(latencies_array)
            throughput = count / window_duration if window_duration > 0 else 0
            
            # Write to CSV
            with open(self.output_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    f"{timestamp:.3f}",
                    window_start_str,
                    window_end_str,
                    f"{window_duration:.2f}",
                    count,
                    f"{throughput:.2f}",
                    f"{avg:.3f}",
                    f"{min_lat:.3f}",
                    f"{p50:.3f}",
                    f"{p90:.3f}",
                    f"{p95:.3f}",
                    f"{p99:.3f}",
                    f"{max_lat:.3f}",
                    f"{stdev:.3f}"
                ])
            
            self.total_windows += 1
            
            # Print stats
            print(f"[Win {self.total_windows:3d}] {window_start_str} | "
                  f"Reqs: {count:7,d} ({throughput:7.1f} req/s) | "
                  f"Avg: {avg:7.2f}ms | "
                  f"P90: {p90:7.2f}ms | "
                  f"P95: {p95:7.2f}ms | "
                  f"P99: {p99:7.2f}ms | "
                  f"Max: {max_lat:7.2f}ms")
            
            # Reset for next window
            self.latencies = []
            self.window_start = time.time()
    
    def window_flusher_thread(self):
        """Periodically flush windows"""
        while self.running:
            time.sleep(self.window_size)
            if self.running:
                self.flush_window()
    
    def udp_receiver_thread(self):
        """Receive latency data via UDP"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 * 1024 * 1024)  # 2MB buffer
        sock.settimeout(1.0)
        sock.bind(('0.0.0.0', self.port))
        
        print(f"✓ Listening on UDP port {self.port}")
        print(f"✓ Ready to receive latency stream")
        print()
        
        while self.running:
            try:
                data, addr = sock.recvfrom(64)  # Small packets
                try:
                    # Parse simple float
                    latency_ms = float(data.decode('utf-8').strip())
                    
                    if latency_ms > 0 and latency_ms < 60000:  # Sanity check: < 60 seconds
                        with self.lock:
                            self.latencies.append(latency_ms)
                            self.total_requests += 1
                            
                except (ValueError, UnicodeDecodeError):
                    pass  # Ignore malformed packets
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error: {e}")
        
        sock.close()
    
    def start(self):
        """Start all threads"""
        receiver = threading.Thread(target=self.udp_receiver_thread, daemon=True)
        flusher = threading.Thread(target=self.window_flusher_thread, daemon=True)
        
        receiver.start()
        flusher.start()
        
        print("Press Ctrl+C to stop")
        print()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n")
            print("=" * 60)
            print("  Shutting down gracefully...")
            print("=" * 60)
            self.running = False
            time.sleep(2)
            
            # Flush remaining data
            self.flush_window()
            
            print()
            print("=" * 60)
            print("  Summary")
            print("=" * 60)
            print(f"  Total requests: {self.total_requests:,}")
            print(f"  Total windows:  {self.total_windows}")
            print(f"  Output file:    {self.output_file}")
            print("=" * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Streaming latency collector for wrk2')
    parser.add_argument('--port', type=int, default=9999, help='UDP port (default: 9999)')
    parser.add_argument('--window', type=int, default=5, help='Window size in seconds (default: 5)')
    parser.add_argument('--output', type=str, default='latencies_stream.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    collector = StreamingLatencyCollector(
        port=args.port,
        window_size=args.window,
        output_file=args.output
    )
    collector.start()
