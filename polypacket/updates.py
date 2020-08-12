from update_notipy import update_notify
import pkg_resources

__version__ = pkg_resources.get_distribution("polypacket").version

def updateCheck():
    update_notify('polypacket', __version__).notify()

#    ┌───────────────────────────────────────────┐
#    │                                           │
#    │   Update available 0.1.0 → 0.1.2          │
#    │   Run pip install -U pkg-info to update   │
#    │                                           │
#    └───────────────────────────────────────────┘
