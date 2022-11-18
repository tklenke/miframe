import socket
import logging
import time

#setup
logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')

def GetMyIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip
    
def CheckIPForMiFrameServer(szAddr,nPort):
    bRequest = bytes(f"GET /chksrvr HTTP/1.1\r\nHost:{szAddr}\r\n\r\n", encoding='utf-8')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(.1)
    try:
        s.connect((szAddr, nPort))
        s.send(bRequest)
        data = s.recv(1024)
    except (ConnectionRefusedError,socket.timeout) as err:
        s.close()
        return(False)
    s.close()
    if data[9:12] == b'202':
        return (True)
    else:
        logging.debug(f"Unexpected Response: {data}")
        return(False)

def ScanNetworkForMiFrameServer(nPort = 5000):
    szMyIP = GetMyIP() 

    # from my IP and compose a base like 192.168.1.xxx
    ip_parts = szMyIP.split('.')
    szBaseIP = ip_parts[0] + '.' + ip_parts[1] + '.' + ip_parts[2] + '.'
    
    for i in range(1, 255):
        szIP = f"{szBaseIP}{i}"
        bR = CheckIPForMiFrameServer(szIP,nPort)
        if bR:
            return (szIP)
      
    return (None)



#----------MAIN------------    
if __name__ == '__main__':
    tStart = time.process_time()
    logging.getLogger().setLevel(logging.DEBUG)

    logging.debug(f"Scanning Network for MiFrame-Server") 
    szIPServer = ScanNetworkForMiFrameServer()
    logging.debug(f"IP MiFrame Server:\t{szIPServer}")    


    tEnd = time.process_time()
    logging.debug(f"Elapsed Time:\t{tEnd-tStart}")
