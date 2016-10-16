from artnet_receiver import ArtNetReceiver
from audio_player import AudioPlayer
import time
import pygame
import sys
import settingsreader

from display import Display

import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 0))  # connecting to a UDP address doesn't send packets
interface_ip = s.getsockname()[0]

comm = {
	"ip": interface_ip,
	"initialized": False
}

config_loader = settingsreader.Settings()
config = config_loader.get_settings()

display = Display(comm);
display.start();

universe = config.get("universe", 0)
address = config.get("start", 1);

audio_players_count = config.get("audio_players", 1)
audio_players = [None] * audio_players_count;

playlist = config.get("audio_playlist", {})



comm["audio_players"] = audio_players_count
comm["universe"] =  universe
comm["address"] =  address
comm["audio"] =  {}


artnetReceiver = ArtNetReceiver(universe)

for i in range(audio_players_count):
	# Create Player
	ap = AudioPlayer(address, playlist, artnetReceiver, comm)

	# Get Amount of Channels it is using
	address += ap.getDMXFootprint() or 4

	ap.printDMXFootprint()

	# add player to list
	audio_players[i] = ap

print "Running ArtnetReceiver"
artnetReceiver.start()

while True:
    try:
        time.sleep(5)

    except KeyboardInterrupt:
    	display.stop();
    	artnetReceiver.stop();

    	for ap in audio_players:
    		ap.stop();
    	sys.exit()
        break;