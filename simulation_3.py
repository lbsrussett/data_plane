#Laura Sullivan-Russett and Grace Walkuski
#CSCI 466
#PA3
#November 2, 2018

import network_3
import link_3
import threading
from time import sleep

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 5 #give the network sufficient time to transfer all packets before quitting
table_a = {}
table_b = {}
table_c = {}
table_d = {}

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads
    
    #create routing tables
    table_a = {1:0,2:1}
    table_b = {1:0}
    table_c = {2:0}
    table_d = {1:0,2:1}
    #create network nodes
    client_1 = network_3.Host(1)
    object_L.append(client_1)
    client_2 = network_3.Host(2)
    object_L.append(client_2)
    server_1 = network_3.Host(3)
    object_L.append(server_1)
    server_2 = network_3.Host(4)
    object_L.append(server_2)
    router_a = network_3.Router(name='A', table=table_a, intf_count=2, max_queue_size=router_queue_size)
    object_L.append(router_a)
    router_b = network_3.Router(name='B', table=table_b, intf_count=1, max_queue_size=router_queue_size)
    object_L.append(router_b)
    router_c = network_3.Router(name='C', table=table_c, intf_count=1, max_queue_size=router_queue_size)
    object_L.append(router_c)
    router_d = network_3.Router(name='D', table=table_d, intf_count=2, max_queue_size=router_queue_size)
    object_L.append(router_d)
    #create a Link Layer to keep track of links between network nodes
    link_layer = link_3.LinkLayer()
    object_L.append(link_layer)
    
    #add all the links
    #link parameters: from_node, from_intf_num, to_node, to_intf_num, mtu
    link_layer.add_link(link_3.Link(client_1, 0, router_a, 0, 50))
    link_layer.add_link(link_3.Link(client_2, 0, router_a, 1, 50))
    link_layer.add_link(link_3.Link(router_a, 0, router_b, 0, 50))
    link_layer.add_link(link_3.Link(router_a, 1, router_c, 0, 50))
    link_layer.add_link(link_3.Link(router_b, 0, router_d, 0, 50))
    link_layer.add_link(link_3.Link(router_c, 0, router_d, 1, 50))
    link_layer.add_link(link_3.Link(router_d, 0, server_1, 0, 40))
    link_layer.add_link(link_3.Link(router_d, 1, server_2, 0, 40))

    
    
    #start all the objects
    thread_L = []
    thread_L.append(threading.Thread(name=client_1.__str__(), target=client_1.run))
    thread_L.append(threading.Thread(name=server_1.__str__(), target=server_1.run))
    thread_L.append(threading.Thread(name=client_2.__str__(), target=client_2.run))
    thread_L.append(threading.Thread(name=server_2.__str__(), target=server_2.run))
    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))
    thread_L.append(threading.Thread(name=router_b.__str__(), target=router_b.run))
    thread_L.append(threading.Thread(name=router_c.__str__(), target=router_c.run))
    thread_L.append(threading.Thread(name=router_d.__str__(), target=router_d.run))
    
    thread_L.append(threading.Thread(name="Network", target=link_layer.run))
    
    for t in thread_L:
        t.start()
    
    
    #create some send events    
    # for i in range(3):
    client_1.udt_send(1, 3, 1, 0, 0, 'Client 1 sample data %d that is too long to deliver through the current MTU lengths.' % 1)
    client_2.udt_send(2, 4, 1, 0, 0, 'Client 2 sample data %d that is too long to deliver through the current MTU lengths.' % 1)
    
    
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically