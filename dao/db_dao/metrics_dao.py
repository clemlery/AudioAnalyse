
from config import session
from dao.base_dao import BaseDbDAO
from models.sql_alchemy_models.metrics import ArtistMetricsSnapshot, TrackMetricsSnapshot
from datetime import datetime

class TrackMetricsSnapshotDAO(BaseDbDAO):
    @staticmethod
    def add_track_metrics(
        track_id : int,
        playcount : int
    ) -> None:
        
        track_metrics = TrackMetricsSnapshotDAO.get_track_metrics_by_track_id(track_id)
        
        if track_metrics is None:
            track_metrics = TrackMetricsSnapshot(
                track_id=track_id,
                playcount=playcount,
                collectet_at=datetime.now()
            )
            session.add(track_metrics)

            
    def update_track_metrics(
        id : int,
        playcount : int
    ) -> None:
        
        track_metrics = TrackMetricsSnapshotDAO.get_track_metric_by_id(id)
        
        if track_metrics :
            session.expunge(track_metrics)
            track_metrics.playcount = playcount
            track_metrics.collected_at = datetime.now()
            session.merge(track_metrics)

    @staticmethod
    def get_tracks_metrics() -> list[TrackMetricsSnapshot]:
        return session.query(TrackMetricsSnapshot).all()
    
    @staticmethod
    def get_track_metric_by_id(id : int) -> TrackMetricsSnapshot:
        return session.query(TrackMetricsSnapshot).fiter(TrackMetricsSnapshot.id == id).first()

    @staticmethod
    def get_track_metrics_by_track_id(track_id : int) -> TrackMetricsSnapshot:
        return session.query(TrackMetricsSnapshot).filter(TrackMetricsSnapshot.track_id == track_id).first()
    
class ArtistMetricsSnapshotDAO(BaseDbDAO):
    @staticmethod
    def add_artist_metrics(
        artist_id : int,
        monthly_listeners : int
    ) -> None:
        
        artist_metrics = ArtistMetricsSnapshotDAO.get_artist_metric_by_artist_id(artist_id)
        
        if artist_metrics is None:
            artist_metrics = TrackMetricsSnapshot(
                artist_id=artist_id,
                monthly_listeners=monthly_listeners,
                collectet_at=datetime.now()
            )
            session.add(artist_metrics)

    def update_artist_metrics(
        id : int,
        monthly_listeners : int
    ) -> None:
        artist_metrics = ArtistMetricsSnapshotDAO.get_artist_metrics_by_id(id)
        
        if artist_metrics:
            session.expunge(artist_metrics)
            artist_metrics.monthly_listeners = monthly_listeners
            artist_metrics.collected_at = datetime.now()
            session.merge(artist_metrics)
        
    
    @staticmethod
    def get_artists_metrics() -> list[ArtistMetricsSnapshot]:
        return session.query(ArtistMetricsSnapshot).all()
    
    @staticmethod
    def get_artist_metrics_by_id(id : int) -> ArtistMetricsSnapshot:
        return session.query(ArtistMetricsSnapshot).filter(ArtistMetricsSnapshot.id == id).first()
    
    @staticmethod
    def get_artist_metrics_by_artist_id(artist_id : str) -> ArtistMetricsSnapshot:
        return session.query(ArtistMetricsSnapshot).filter(ArtistMetricsSnapshot.artist_id == artist_id).first()
        