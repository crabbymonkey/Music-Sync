import tidalapi
import webbrowser
import os
import re

import ytmusicapi


def simplifyString(s):
    # Regex to remove any '()' that are added on to fix titles like "One Thing Right (feat. Kane Brown)" to just be "One Thing Right"
    return re.sub('\((.+?)\)', '', s).strip()

class Song(object):
    title = None
    artist = None
    album = None
    
    def __str__(self):
        return "Song: %s, Artist: %s, Album: %s" % (self.title, self.artist, self.album)

    def __eq__(self, other):
        if (self is None) ^ (other is None):
            return false
        if (simplifyString(self.title.casefold()) == simplifyString(other.title.casefold())) and (simplifyString(self.artist.casefold()) == simplifyString(other.artist.casefold())):
            return True

        return False

def getTitalSongFromJson(json_obj):
    song = Song()
    if 'artist' in json_obj:
        artist = json_obj['artist']
        song.artist = artist['name']
    elif 'artists' in json_obj:
        artists = json_obj['artists']
        artist = artists[0]
        song.artist = artist['name']
    if 'album' in json_obj:
        album = json_obj['album']
        song.album = album['title']
    song.title = json_obj['title']
    return song

def getYoutubeSongFromJson(json_obj):
    song = Song()
    if 'artist' in json_obj:
        artist = json_obj['artist']
        song.artist = artist['name']
    elif 'artists' in json_obj:
        artists = json_obj['artists']
        artist = artists[0]
        song.artist = artist['name']
    if 'album' in json_obj:
        album = json_obj['album']
        if album is not None:
            song.album = album['name']
    song.title = json_obj['title']
    return song

def getTitalSongs():
    session = tidalapi.Session()
    login, future = session.login_oauth()
    webbrowser.open(login.verification_uri_complete)
    future.result()

    currentUser = session.user
    userFavorites = currentUser.favorites
    request = userFavorites._session.request('GET', userFavorites._base_url + '/tracks')
    titalSongs = []
    for fav in request.json()['items']:
        titalSongs.append(getTitalSongFromJson(fav['item']))

    # Print out for testing
#    print("+++++++++++++++++++++++++++ TITAL SONGS +++++++++++++++++++++++++++++++++++++")
#    for song in titalSongs:
#        print("Song: ",song.title,", Artist: ",song.artist,", Album: ",song.album)
    return titalSongs

def getYoutubeSongs():
    ytmusicClient = ytmusicapi.YTMusic("headers_auth.json")
    likedSongsPlaylist = ytmusicClient.get_liked_songs(1000)
    tracks = likedSongsPlaylist['tracks']
    youtubeSongs = []
    for track in tracks:
        song = getYoutubeSongFromJson(track)
        youtubeSongs.append(song)

    # Print out for testing
#    print("+++++++++++++++++++++++++++ YOUTUBE SONGS +++++++++++++++++++++++++++++++++++++")
#    for song in youtubeSongs:
#        print("Song: ",song.title,", Artist: ",song.artist,", Album: ",song.album)
    return youtubeSongs


def compareLiked(): 
    youtubeSongs = getYoutubeSongs()
    titalSongs = getTitalSongs()

    for ySong in youtubeSongs:
        if ySong in titalSongs:
            print(ySong, " in tital")
        else:
            print(ySong, " missing")

compareLiked()

song1 = Song()
song1.title = "One Thing Right (feat. Kane Brown)"
song1.artist = "testvalue"

song2 = Song()
song2.title = "One Thing Right"
song2.artist = "testvalue"

song3 = Song()
song3.title = "One Thing Right (feat. Kane Brown)"
song3.artist = "testvalue"

print(song1 == song2)
print(song1 == song3)