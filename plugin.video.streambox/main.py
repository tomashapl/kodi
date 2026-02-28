"""StreamBox – Kodi video addon entry point."""
import sys

from resources.lib.router import Router

if __name__ == '__main__':
    router = Router(sys.argv)
    router.dispatch()
