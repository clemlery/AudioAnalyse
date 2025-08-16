from dao.base_dao import BaseDbDAO
from config import session
from models.sql_alchemy_models.artist_sql_model import Artist
from models.sql_alchemy_models.track_sql_model import Track
from models.sql_alchemy_models.track_stream_sql_model import TrackStream
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import desc

class SORT_TYPE(Enum):
    PLAYED_COUNT = "played_count"
    DURATION_PLAYED = "duration_played"
    
class TrackStreamDAO(BaseDbDAO):
    @staticmethod    
    def add_or_update_stream_track(
        track_id : int,
        user_id: str,
        track_done_bool : bool,
        skipped_bool : bool, 
        clicked_row_bool : bool,
        current_loop_streak : int,
        ts, 
        duration_played_ms : int
    ) -> None: 
        """
        Ajoute ou met à jour une ligne dans TrackStream pour un utilisateur.
        """        
        
        track_stream =session.get(TrackStream, (user_id, track_id))
        duration_played_s = duration_played_ms//1000

        
        if track_stream is None:
            track_stream = TrackStream(
                track_id=track_id,
                user_id=user_id,
                first_played_at=ts,
                last_played_at=ts,
                track_done_count = 1 if track_done_bool else 0,
                skipped_count = 1 if skipped_bool else 0,
                click_row_count = 1 if clicked_row_bool else 0,
                total_duration_play_s = duration_played_s
            )
            session.add(track_stream)
        else:
            session.expunge(track_stream)
            if track_done_bool:
                track_stream.track_done_count += 1
            elif skipped_bool:
                track_stream.skipped_count += 1
            if clicked_row_bool:
                track_stream.click_row_count += 1
            
            if current_loop_streak > track_stream.highest_loop_streak:
                track_stream.highest_loop_streak = current_loop_streak    
            
            track_stream.last_played_at = ts
            track_stream.total_duration_play_s += duration_played_s
            session.merge(track_stream)


    @staticmethod
    def get_user_track_stream(user_id: str, track_id: str) -> Optional[TrackStream]:
        """
        Récupère un stream spécifique pour un utilisateur et une track.
        """
        return session.get(TrackStream, {'user_id': user_id, 'track_id': track_id})

    @staticmethod
    def get_user_streams(user_id: str) -> List[TrackStream]:
        """
        Retourne toutes les entrées de stream pour un utilisateur donné.
        """
        return TrackStream.query.filter_by(user_id=user_id).all()
    
    # Deprecated
    @staticmethod
    def get_user_top_tracks(user_id: str, sorted_type: SORT_TYPE, limit: Optional[int] = None) -> List[dict]:
        """
        Retourne les tracks les plus jouées pour un utilisateur,
        enrichis avec leurs métadonnées (nom, artistes),
        triés selon sorted_type (played_count ou duration_played).
        """
        # Construction de la requête de base : jointure (TrackStream ⇆ Track)
        query = (
            session.query(
                TrackStream,
                Track.name,
                Track.artists_name,
                Track.duration_ms
            )
            .join(Track, TrackStream.track_id == Track.id)
            .filter(TrackStream.user_id == user_id)
        )

        match sorted_type:
            case SORT_TYPE.PLAYED_COUNT.value:
                query = query.order_by(desc(TrackStream.played_count))
            case SORT_TYPE.DURATION_PLAYED.value:
                query = query.order_by(desc(Track.duration_ms * TrackStream.played_count))
            case _:
                query = query.order_by(desc(TrackStream.played_count))

        if limit:
            query = query.limit(limit)

        results = query.all()
        top_tracks = []
        for stream, name, artists, duration_ms in results:
            played_count = stream.played_count
            total_ms = duration_ms * played_count
            # conversion en minutes totales
            played_minutes = timedelta(milliseconds=total_ms).seconds // 60
            top_tracks.append({
                'track_id': stream.track_id,
                'name': name,
                'artists_name': artists,
                'played_count': played_count,
                'played_duration': played_minutes,
                'first_played_at': stream.first_played_at.isoformat(),
                'last_played_at': stream.last_played_at.isoformat(),
            })

        return top_tracks
    
    # Deprecated
    @staticmethod
    def get_user_top_artists(user_id : str, sorted_type : SORT_TYPE, limit: Optional[int] = None) -> List[dict]:
        query = (
            session.query(
                TrackStream,
                Track.duration_ms,
                Artist
            )
            .join(
                Track,
                TrackStream.track_id == Track.id
            )
            .join(
                Artist,
                Track.artist_id == Artist.id
            )
            .filter(TrackStream.user_id == user_id)
        )
        
        if limit:
            query = query.limit(limit)
            
        results = query.all()
        agg = {}
        for track_stream, track_duration_ms, artist, in results:
            name = artist.name
            if name not in agg:
                agg[name] = {
                    'name': name,
                    'followers': artist.followers,
                    'popularity': artist.popularity,
                    'genres': artist.genres,
                    'images': artist.images,
                    'played_count': track_stream.played_count,
                    'duration': track_duration_ms*track_stream.played_count
                }
            else:
                agg[name]['played_count'] += track_stream.played_count
                agg[name]['duration'] += track_duration_ms*track_stream.played_count
 
        for artist_name in agg.keys():
            agg[artist_name]['duration'] = timedelta(milliseconds=agg[artist_name]['duration']).seconds//60
    
        match sorted_type:
            case SORT_TYPE.PLAYED_COUNT.value:
                top_artists = sorted(
                    agg.values(),
                    key=lambda entry: entry['played_count'],
                    reverse=True
                )
            case SORT_TYPE.DURATION_PLAYED.value:
                top_artists = sorted(
                    agg.values(),
                    key=lambda entry: entry['duration'],
                    reverse=True
                )
        return top_artists
    
    # Deprecated
    @staticmethod
    def get_user_top_albums(user_id : str, sorted_type : SORT_TYPE, limit :Optional[int] = None) -> List[dict]:
        query = (
            session.query(
                TrackStream.played_count,
                Track.duration_ms,
                Album
            )
            .join(
                Track,
                TrackStream.track_id == Track.id
            )
            .join(
                Album,
                Track.album_id == Album.id
            )
            .filter(TrackStream.user_id == user_id)
        )
        if limit:
            query = query.limit(limit)
        results = query.all()
        
        agg = {}
        for track_played_count, track_duration_ms, album, in results:
            name = album.album_name
            if name not in agg:
                agg[name] = {
                    'name': name,
                    'artist_name': album.artists_name[0],
                    'popularity': album.popularity,
                    'total_tracks': album.total_tracks,
                    'images': album.images,
                    'played_count': track_played_count,
                    'duration' : track_played_count*track_duration_ms
                }
            else:
                agg[name]['played_count'] += track_played_count
                agg[name]['duration'] += track_played_count*track_duration_ms
                
        for album_name in agg.keys():
            agg[album_name]['duration'] = timedelta(milliseconds=agg[album_name]['duration']).seconds//60
        
        match sorted_type:
            case SORT_TYPE.PLAYED_COUNT.value:
                top_albums = sorted(
                    agg.values(),
                    key=lambda entry: entry['played_count'],
                    reverse=True
                )
            case SORT_TYPE.DURATION_PLAYED.value:
                top_albums = sorted(
                    agg.values(),
                    key=lambda entry: entry['duration'],
                    reverse=True
                )
        return top_albums

    @staticmethod
    def delete_user_track_stream(user_id: str, track_id: str) -> None:
        """
        Supprime une ligne de stream pour un utilisateur et une track.
        """
        stream = session.get(TrackStream, {'user_id': user_id, 'track_id': track_id})
        if stream:
            session.delete(stream)
            session.commit()
