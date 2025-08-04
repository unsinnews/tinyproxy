import socket
import threading
import argparse
import sys

def handle_client(client_socket, client_address):
    print(f"接收到客户端 {client_address} 的请求")
    
    try:
        # 接收客户端发送的 HTTP 请求
        request = client_socket.recv(4096)
        
        if not request:
            return
            
        # 解析请求行，获取目标主机和端口
        request_lines = request.split(b'\r\n')
        request_line = request_lines[0]
        method, url, version = request_line.split(b' ')
        
        # 解析目标主机和端口
        if b'http://' in url:
            url = url[7:]  # 去掉 "http://" 前缀
        
        # 分离主机和路径
        host_and_port = url.split(b'/', 1)
        host_port = host_and_port[0]
        path = b'/' + host_and_port[1] if len(host_and_port) > 1 else b'/'
        
        # 默认端口是 80
        if b':' in host_port:
            host, port = host_port.split(b':')
            port = int(port)
        else:
            host = host_port
            port = 80

        # 创建一个新的 socket 来连接目标服务器
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(10)  # 设置超时
        
        # 连接到目标服务器
        server_socket.connect((host.decode(), port))
        
        # 构造新的 HTTP 请求
        new_request = f"{method.decode()} {path.decode()} {version.decode()}\r\n"
        new_request = new_request.encode() + b'\r\n'.join(request_lines[1:])
        
        # 发送请求到目标服务器
        server_socket.send(new_request)
        
        # 接收目标服务器的响应
        response = server_socket.recv(4096)
        
        # 将响应返回给客户端
        client_socket.send(response)
        
        print(f"请求 {method.decode()} {host.decode()}{path.decode()} 处理完成")
        
    except Exception as e:
        print(f"错误: {e}")
        client_socket.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
    
    finally:
        # 关闭连接
        try:
            client_socket.close()
        except:
            pass
        try:
            server_socket.close()
        except:
            pass

def start_proxy_server(host='127.0.0.1', port=8080):
    # 创建 socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"HTTP 代理服务器启动，监听 {host}:{port}")
        print("按 Ctrl+C 停止服务器")
        
        while True:
            # 接受客户端连接
            client_socket, client_address = server_socket.accept()
            
            # 为每个客户端请求创建一个新线程
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.daemon = True  # 设置为守护线程
            client_thread.start()
            
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"服务器启动失败: {e}")
    finally:
        server_socket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='简易 HTTP 代理服务器')
    parser.add_argument('--host', default='127.0.0.1', help='监听地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080, help='监听端口 (默认: 8080)')
    
    args = parser.parse_args()
    start_proxy_server(args.host, args.port)
