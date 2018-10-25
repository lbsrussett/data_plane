#Laura Sullivan-Russett and Grace Walkuski
#CSCI 466
#PA3
#November 2, 2018

import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = None
    
    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)
        
        
## Implements a network layer packet 
class NetworkPacket:
    ## packet encoding lengths
    src_addr_S_length = 5 
    dst_addr_S_length = 5
    id_num_S_length = 2
    frag_offset_S_length = 5
    frag_flag_S_length = 1
    
    ##@param dst_addr: address of the destination host
    #@param id_num: id number of packet for identification of packet fragments
    #@frag_offset: offset value of packet fragment for reassembly
    #@frag_flag: flag indicating whether the fragment is the last of a packet
    # @param data_S: packet payload
    def __init__(self, src_addr, dst_addr, id_num, frag_offset, frag_flag, data_S):
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.id_num = id_num
        self.frag_offset = frag_offset
        self.frag_flag = frag_flag
        self.data_S = data_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.src_addr).zfill(self.src_addr_S_length)
        byte_S += str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += str(self.id_num).zfill(self.id_num_S_length)
        byte_S += str(self.frag_offset).zfill(self.frag_offset_S_length)
        byte_S += str(self.frag_flag)
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        src_addr = int(byte_S[0:NetworkPacket.src_addr_S_length])
        dst_addr = int(byte_S[NetworkPacket.src_addr_S_length : NetworkPacket.src_addr_S_length+NetworkPacket.dst_addr_S_length])
        id_num = int(byte_S[NetworkPacket.src_addr_S_length+NetworkPacket.dst_addr_S_length : NetworkPacket.src_addr_S_length+NetworkPacket.dst_addr_S_length+NetworkPacket.id_num_S_length])
        frag_offset = int(byte_S[NetworkPacket.src_addr_S_length+NetworkPacket.dst_addr_S_length+NetworkPacket.id_num_S_length : NetworkPacket.src_addr_S_length+NetworkPacket.dst_addr_S_length+NetworkPacket.id_num_S_length+NetworkPacket.frag_offset_S_length])
        frag_flag = int(byte_S[NetworkPacket.src_addr_S_length+NetworkPacket.dst_addr_S_length+NetworkPacket.id_num_S_length+NetworkPacket.frag_offset_S_length : NetworkPacket.src_addr_S_length+NetworkPacket.dst_addr_S_length+NetworkPacket.id_num_S_length+NetworkPacket.frag_offset_S_length+1])
        data_S = byte_S[NetworkPacket.src_addr_S_length+NetworkPacket.dst_addr_S_length+NetworkPacket.id_num_S_length+NetworkPacket.frag_offset_S_length+1 : ]
        return self(src_addr, dst_addr, id_num, frag_offset, frag_flag, data_S)
    

    

## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, src_addr, dst_addr, id_num, frag_offset, frag_flag, data_S):
        p = NetworkPacket(src_addr, dst_addr, id_num, frag_offset, frag_flag, data_S)
        temp_pkt = p.to_byte_S()
        header = temp_pkt[0:18]
        temp_pkt = temp_pkt[len(header):]
        chunk = self.out_intf_L[0].mtu - len(header)
        if (len(temp_pkt)+len(header)) > self.out_intf_L[0].mtu:
            while (len(temp_pkt)+len(header)) > self.out_intf_L[0].mtu:
                pkt_S = header + temp_pkt[:chunk]
                self.out_intf_L[0].put(pkt_S)
                temp_pkt = temp_pkt[chunk:]
                print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, pkt_S, self.out_intf_L[0].mtu))
            pkt_S = header + temp_pkt
            self.out_intf_L[0].put(pkt_S)
            print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, pkt_S, self.out_intf_L[0].mtu))
        else:
            self.out_intf_L[0].put(p.to_byte_S()) #send packets always enqueued successfully
            print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            recon_pkt_S = pkt_S[:18]
            while pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S)
                if p.frag_flag == 1:
                    print('Packet was fragmented. Reconstructing.\n')    
                    recon_pkt_S += pkt_S[p.frag_offset:]    
                else: 
                    recon_pkt_S += pkt_S[:p.frag_offset]
                pkt_S = self.in_intf_L[0].get()
                print('%s: reconstructed packet "%s" on the in interface' % (self, recon_pkt_S))

                    
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router described in class
class Router:
    
    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, table, intf_count, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #set the routing table for the router
        self.table = table
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)
    
    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                #get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                #if packet exists make a forwarding decision
                if pkt_S is not None:
                    p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                    out_intf = self.table.get(p.src_addr)
                    temp_pkt = p.to_byte_S()
                    header = temp_pkt[0:18]
                    temp_pkt = temp_pkt[len(header):]
                    chunk = self.out_intf_L[0].mtu - len(header)
                    offset = 0
                    # print('This is the outinterface for the packet: %d' % out)
                    if (len(temp_pkt)+18) > self.out_intf_L[out_intf].mtu:
                        while (len(temp_pkt)+18) > self.out_intf_L[out_intf].mtu:
                            print('%s: fragmenting packet "%s"' % (self, pkt_S))
                            frag = header + temp_pkt[:chunk]
                            temp_pkt = temp_pkt[chunk:]
                            frag_pkt = NetworkPacket.from_byte_S(frag)
                            frag_pkt.frag_flag = 1
                            frag_pkt.frag_offset = offset
                            offset = 18
                            self.out_intf_L[out_intf].put(frag_pkt.to_byte_S(), True)
                    else:
                        frag = header + temp_pkt
                        frag_pkt = NetworkPacket.from_byte_S(frag)
                        frag_pkt.frag_flag = 0
                        frag_pkt.frag_offset = 18
                        self.out_intf_L[out_intf].put(frag_pkt.to_byte_S(), True)    
                    # HERE you will need to implement a lookup into the 
                    # forwarding table to find the appropriate outgoing interface
                    # for now we assume the outgoing interface is also i
                    self.out_intf_L[out_intf].put(p.to_byte_S(), True)
                    print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' \
                        % (self, p, i, out_intf, self.out_intf_L[out_intf].mtu))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, out_intf))
                pass
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 