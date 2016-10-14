from artnet_receiver import ArtNetReceiver
from audio_player import AudioPlayer
import time
import pygame

artnetReceiver = ArtNetReceiver(0)



playlist = {}

# Configures one AudioPlayer at Startingaddress 100 (DMX 100, where 1 is the first address and 512 is the last one.)
ac1 = AudioPlayer(100, playlist, artnetReceiver)

print "ArtnetReceiver Running"
artnetReceiver.run()

while True:
    try:
        time.sleep(1)

    except KeyboardInterrupt:
        break;