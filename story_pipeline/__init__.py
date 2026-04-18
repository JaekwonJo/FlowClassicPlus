def main(*args, **kwargs):
    from .app import main as _main

    return _main(*args, **kwargs)


__all__ = ["main"]
