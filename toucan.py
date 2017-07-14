
#-------------------------
# Toucan WIDS 
# Author: Collin Sullivan
# Year: 2017
# Version: 0.0.1
#-------------------------

#--------------------------------------------------------------------------------------------------------------------------------
# Monitors a LANs and will protect against spoofing attacks for MITM purposes
# 1. Scans Network for Active Hosts
# 2. Scans hosts for Layer 2 Addresses and will "attack back" when a MITM is discovered by correcting poisoned hosts
# 3. Will send ALERT packet to DG (need to write protocol for this still)
# Needs to be run as ROOT
#--------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------
#                    GNU GENERAL PUBLIC LICENSE
#                      Version 3, 29 June 2007

# Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
# Everyone is permitted to copy and distribute verbatim copies
# of this license document, but changing it is not allowed.
#--------------------------------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------------------------------

# TO DO:
# 1. Option parser for fast use - but then you don't get to seee my toucan =( 
# 2. Write alert protocol

#--------------------------------------------------------------------------------------------------------------------------------


import logging
import socket, sys
from scapy.all import *
from scapy.error import Scapy_Exception
from scapy.all import sr1,IP,ICMP
from scapy.all import srp
from scapy.all import Ether, ARP, conf
import os
import sys
import threading
from optparse import OptionParser
import signal
from struct import *
from termcolor import colored, cprint
import time
import termcolor
logging.basicConfig(filename='toucan.log',level=logging.DEBUG)



toucan = """\033[95m
                                                                                                        ............
                                                                                                ..............-.-----.
                                         .-.                                               ..--.........:---:-------:-
                                           .--                                          .-:-........:-:-:---....``````.
                                            `.-.`````````.-:-.                     .-//:-.....--:::----..
                                            `..--..`````.-:+:-..-//:.           -+sdmmo-..-.--/::----.
                                            .-///.--:/-.`..-:+///-.:/:.        +hm   h/.--+::-----.
                                            .--/:::-.``-:+-.--/-/+/-----      hmdhssysy/://:::::.
                                                    ````....-:---.``.``````+mddhddddmd//+oyds.
                                            ..::--...-````....---...```````ommmmddmmmmmsdmmNs
                                            ..-.-:-...``````..-::-:-`.````ommdddmmmmmdddmmmh.
                                            ...-::...```````:--:/::```-+hmmddhdmmdyhhhhmmm+`
                                           .---.-:...```````-.-::+--/sdmmdhhhyyddddhhddmmm-
                                            -.`.--...``````.:/oshdddmddddhhyyyssdmdddddmmm.
                                                .....````-+ydmmNmmmmddddmmhyyyssosydmdmmmmd.
                                                `...```.+hmmmmmmmddddddmNNmhyyyssooosyhdmNNh`
                                                .````.odddddddhdddddmmmNNNmdyyysosoosyyhddh/
                                                   +dmdddddhddddhdddmmNNNmdyyysoossyyhddh+
                                                 -ydddddddddddddmddhdmmdddddhyyyyyyhhddh+
                              ``.`.`            dddddddddddddddhdhydmhhyhmmdhyyyhhddhy:
                                .-:-..`.       dddddhdddddyssyhhyyyyddyhhhmmmmdddddds.```.----...````.-..
                                 .-:+/:..    /dddddhdddho///osyyssssydddddmNNNNNNNms....:::--------.--:-.
                                         /:-. :oyhhhhhhs+//:://ossssssyhdmmNNNNNNNd+---://:::----//-----:.
                                            +::::++oss/ss+:::-:osysssssydmmNNNmds:-:/++o:-:::.-:--.-....
                                            -yyyo++//+/+/ssy++/--:oossyyyhhdmmhss:...+o+/:::-.---........
                                            ddhyyysysso+ysh:-:::::/+syhhhdhy+-`-:.`.s+/:----..........
                                           +mdhhhyymyhshy+o+/:-.-:///+oss+:.`````::-s/::::+:::-
                                           ymddhyhhdssy+:-:+ys/:..-/+/:---````````.:+/:---/---.
                                           ddh+hdmhs+s+----/hhssoo+-://oyyo.````````-//:-:--..
                                           dy+.hmdy+//::-:-ohhyyyoso+::yssy:..````````-/++:-..
                                          :y+.-ydhs+---::.`:ooo++/:/sooh+yy/+::::-----:-+so+::-:-....``.........`
                                          :/:`--/ys+-.-:.````....``.--:/sh+/::::-....-----...........`.-.-.-:```...```.-````--
                                          ./.````ss/---/+-             :o/+o+o++/::::--::--.--..:--//-:-:::--...-.````..````.`
                                                 oy+---::+-            ...-:/-://oooooos+ooo+/+//+//::/:--.
                                                 .hs:-:+::+-            ....-.-````````....-..-..---...
                                                  sy://so/:+-
                                                  -h/ososo///.  
                                                   oo+yyo/so/.``````.--...........-----.-.......`
                                                   -s+yyso:+o-```````````````
                                                    osssyoo:/o.               
                                                    :o+osys+:o/                        .....-://oo/---////:.////:.////:.
                                                    .s/oyyyo+/o-                        ``..-. TOUCAN NETWORK DEFENDER
                                                     -+/+yho+o++.                            `+o///---////:.////:.////:.
                                                     .+/+hhs//s:`                             
                                                      //ohyys:oo`
                                                      .s:ssyys:s:
                                                        //+oyyy+/+
                                                       `-o/oyyo+s+
                                                        /ooshs:/s-                               
                                                        .o:oyho/oo                               
                                                        `//oshss+o                              
                                                         ./+ys++os
                                                          `.+/os++"                              "The world is a jungle in general, and the
                                                           `-//:-.                               networking game contributes many animals."
"""
os.system("espeak 'Welcome to Toucan Network Defender'")


print toucan


GATEWAY_IP = raw_input("Enter your Gateway IP: \n")

interface = raw_input("\nEnter your network interface: \n")

n_range = raw_input("\nEnter your network range to scan in format 10.0.0.1/24: \n")

print"[*] Gateway Locked in..."
time.sleep(.5)
print"[*] Interface configured..."
time.sleep(.5)
print"[*] Network Range set..."
time.sleep(.5)
print"[*] Commensing..."
print"\n"
time.sleep(1)


#this option parser will be put into use eventually, not even sure if it is needed. Could be a fun feature though

class MikasaOptionParser(OptionParser):

    def __init__(self):

        OptionParser.__init__(self)

        self.add_option('--ScanHosts', help='Scans for all L2 + L3 addresses on network')
        self.add_option('--DefendHosts', help='Defends Hosts on Network', dest="TargetPort", default=445, type='int')


def processParams(self, inputs):

           options, args = self.parser.parse_args(inputs) 
           
           if options.ScanHosts ==  "" or options.TargetPort > 65535:

               print "[+] Scanning Hosts:          %s" % (options.ScanHosts)

               return


def arping(iprange="%s" % n_range):

    ans, unans = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=iprange), timeout=5)

    collection = []

    for snd, rcv in ans:

        result = rcv.sprintf(r"%ARP.psrc% %Ether.src%").split()
        
        collection.append(result)

    for elem in collection:

        print elem

 
def arp_display(pkt):

    if pkt[ARP].op == 1: 
        return 'Request: %s is asking about %s' % (pkt[ARP].psrc, pkt[ARP].pdst)
    if pkt[ARP].op == 2: 
        return 'Response: %s has address %s' % (pkt[ARP].hwsrc, pkt[ARP].psrc)
 
    sniff(prn=arp_display, filter="arp", store=0, count=10)


def get_mac_gateway(ip_address):

    response, unanswered = srp(Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(pdst=ip_address), \
        timeout=2, retry=2)

    for s, r in response:
        return r[Ether].src
    return None



if __name__ == '__main__':

    GATEWAY_MAC = get_mac_gateway(GATEWAY_IP)

    print "[*] Gateway %s is at %s" % (GATEWAY_IP, GATEWAY_MAC)

    arping()

    sniff(filter = "arp", prn = arp_display)
        
