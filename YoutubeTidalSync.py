import enum
import webbrowser
import re

import tidalapi
import ytmusicapi


def simplifyString(s):
    # Regex to remove any '()' that are added on to fix titles like "One Thing Right (feat. Kane Brown)" to just be "One Thing Right"
    reduced = re.sub('\((.+?)\)', '', s).strip()
    # Regex to remove any '[]' that are added on to fix titles like "The Longest Road [Deadmau5 Remix]" to just be "The Longest Road"
    return re.sub('\[.+?]', '', reduced).strip()

def stringCompare(s1, s2):
    # Don't accept Nones
    if (s1 is None) or (s2 is None):
        return False
    return s1.casefold() == s2.casefold()

def songTitleCompare(s1, s2):
    # Don't accept Nones
    if (s1 is None) or (s2 is None):
        return False
    simpleS1 = simplifyString(s1)
    simpleS2 = simplifyString(s2)
    # Don't accept Nones
    if stringCompare(simpleS1, simpleS2):
        return True
    # check if substring of the other but don't do it for short song titles
    return ((simpleS1 in simpleS2) or (simpleS2 in s1)) and ((len(simpleS1) > 10) and (len(simpleS2) > 10))

def songExactMatch(song1, song2):
    return (stringCompare(song1.title, song2.title)) and (stringCompare(song1.artist, song2.artist)) and (stringCompare(song1.album, song2.album))

class Service(enum.Enum):
    YOUTUBE = 1
    TIDAL = 2
    OTHER = 3

class Song(object):
    title = None
    artist = None
    album = None
    
    def __str__(self):
        return "Song: %s, Artist: %s, Album: %s" % (self.title, self.artist, self.album)

    def __eq__(self, other): #This is not an exact or best manch, just if they are close enough to be the same song
        # Handel empties
        if (self is None) and (other is None):
            return True
        elif (self is None) or (other is None):
            return False
        titleMatch = (songTitleCompare(self.title, other.title)) 
        albumMatch = False
        if simplifyString(self.artist.casefold()) == simplifyString(other.artist.casefold()): 
            albumMatch = True
        elif simplifyString(self.artist.casefold()) in other.title.casefold():
            albumMatch = True
        elif simplifyString(other.artist.casefold()) in self.title.casefold():
            albumMatch = True

        return titleMatch and albumMatch

    def __hash__(self):
        return hash(tuple(self))

class YoutubeSong(Song):
    youtubeId = None

    def __str__(self):
        return 'Youtube ID: {0}, {1}'.format(self.youtubeId, super().__str__())

class TidalSong(Song):
    tidalId = None
    
    def __str__(self):
        return 'Tidal ID: {0}, {1}'.format(self.tidalId, super().__str__())

def parseTitalSong(json_obj):
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

def parseYoutubeSong(json_obj):
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

def getLikedTitalSongs(tidalSession):
    currentUser = tidalSession.user
    userFavorites = currentUser.favorites
    request = userFavorites._session.request('GET', userFavorites._base_url + '/tracks')
    titalSongs = []
    for fav in request.json()['items']:
        titalSongs.append(parseTitalSong(fav['item']))

    # Print out for testing
#    print("+++++++++++++++++++++++++++ TITAL SONGS +++++++++++++++++++++++++++++++++++++")
#    for song in titalSongs:
#        print("Song: ",song.title,", Artist: ",song.artist,", Album: ",song.album)
    return titalSongs

def getLikedYoutubeSongs(ytmusicClient):
    likedSongsPlaylist = ytmusicClient.get_liked_songs(1000)
    tracks = likedSongsPlaylist['tracks']
    youtubeSongs = []
    for track in tracks:
        song = parseYoutubeSong(track)
        youtubeSongs.append(song)

    # Print out for testing
#    print("+++++++++++++++++++++++++++ YOUTUBE SONGS +++++++++++++++++++++++++++++++++++++")
#    for song in youtubeSongs:
#        print("Song: ",song.title,", Artist: ",song.artist,", Album: ",song.album)
    return youtubeSongs


def searchYoutubeForSong(ytmusicClient, searchSong):
    ytmusicClient.search(searchSong.title, ignore_spelling=True)

def searchTidalForSong(tidalSession, searchSong):
    searchResults = tidalSession.search('track', simplifyString(searchSong.title))
    resultTracks = searchResults.tracks
    resultSongs = []
    for track in resultTracks:
        resultSong = TidalSong()
        resultSong.title = track.name
        # Check if one of the other artists is the matching artist
        for artist in track.artists:
            if stringCompare(artist.name, searchSong.artist):
                resultSong.artist = artist.name
                break
        if resultSong.artist is None:
            resultSong.artist = track.artist.name
        resultSong.album = track.album.name
        resultSong.tidalId = track.id
        # if exact match return ID
        if songExactMatch(resultSong, searchSong):
            return resultSong
        else: # else add to list for "close enough compare"
            resultSongs.append(resultSong)
    for resultSong in resultSongs:
        if resultSong == searchSong: 
            return resultSong
    # No obvious matches at this point time to do some checks
    bestMatch = None
    for resultSong in resultSongs:
        # if title match check for the artist
        if songTitleCompare(resultSong.title, searchSong.title):
            # Check if artist name is in the title
            if resultSong.artist.casefold() in searchSong.title.casefold():
                if stringCompare(resultSong.album, searchSong.album):
                    return resultSong
                elif bestMatch is None:
                    bestMatch = resultSong
    return bestMatch

def addMissingLikedSongToYoutube(ytmusicClient, missingSongs):
    for song in missingSongs:
        youtubeSong = searchYoutubeForSong(ytmusicClient, song)
    
def addMissingLikedSongToTidal(tidalSession, missingSong):
    tidalSong = searchTidalForSong(tidalSession, missingSong)
    if tidalSong is None:
        return False
    currentUser = tidalSession.user
    userFavorites = currentUser.favorites
    # Check for song before adding, the seach might have cleaned up the title (TODO: throw error instead of True)
    titalSongs = getLikedTitalSongs(tidalSession)
    if missingSong in titalSongs: #TODO: this needs more testing
        print("Tried to add {",missingSong,"} to Tidal favorites but already added")
        return True

    print("Tidal is Missing {",missingSong,"} in favorites")
    print("Adding {",tidalSong,"} to Tidal favorites")
    #userFavorites.add_track(tidalSong.tidalId)
    return True

def getMissingLiked(ytmusicClient, tidalSession): 
    youtubeSongs = getLikedYoutubeSongs(ytmusicClient)
    titalSongs = getLikedTitalSongs(tidalSession)

    tidalMissing = []
    for ySong in youtubeSongs:
        if ySong not in titalSongs:
            tidalMissing.append(ySong)
            
    youtubeMissing = []
    for tSong in titalSongs:
        if tSong not in youtubeSongs:
            youtubeMissing.append(tSong)

    return {
        Service.YOUTUBE: youtubeMissing,
        Service.TIDAL: tidalMissing
    }

def syncLiked(ytmusicClient, tidalSession):
    missingSongs = getMissingLiked(ytmusicClient, tidalSession)
    unfoundSongs = {}
    print("============================ MISSING TIDAL =========================================")
    unfoundTidalSongs = []
    for missingTidalSong in missingSongs[Service.TIDAL]:
        success = addMissingLikedSongToTidal(tidalSession, missingTidalSong)
        if not success:
            unfoundTidalSongs.append(missingTidalSong)
    unfoundSongs[Service.TIDAL] = unfoundTidalSongs
    print("============================ MISSING YOUTUBE =========================================")
    for missingYoutubeSong in missingSongs[Service.YOUTUBE]:
        print(missingYoutubeSong)

    return unfoundSongs

ytmusicClient = ytmusicapi.YTMusic("headers_auth.json")

tidalSession = tidalapi.Session()
login, future = tidalSession.login_oauth()
webbrowser.open(login.verification_uri_complete)
future.result()

unknownLikedSongs = syncLiked(ytmusicClient, tidalSession)

print("============================ Could not find the following songs for Tidal, try manual search ============================")
for song in unknownLikedSongs[Service.TIDAL]:
    print("Could not find Tidal version of:",song)

#TODO: add to tidal an update tracks to high quality upgradeTidalFavorites()
#TODO: add Spotify
#TODO: add Amazon Music