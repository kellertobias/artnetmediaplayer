from artnet_receiver import ArtNetReceiver
from audio_player import AudioPlayer
import time
import pygame
import json


with open('config.json') as data_file:    
    config = json.load(data_file)


artnetReceiver = ArtNetReceiver(config.get("universe", 0))

address = config.get("start", 1);

audio_players_count = config.get("audio_players", 1)
audio_players = [None] * audio_players_count;

playlist = config.get("audio_playlist", {})

for i in range(audio_players_count):
	# Create Player
	ap = AudioPlayer(address, playlist, artnetReceiver)

	# Get Amount of Channels it is using
	address += ap.getDMXFootprint() or 4

	ap.printDMXFootprint()

	# add player to list
	audio_players[i] = ap


print "Running ArtnetReceiver"
artnetReceiver.run()

while True:
    try:
        time.sleep(1)

    except KeyboardInterrupt:
        break;