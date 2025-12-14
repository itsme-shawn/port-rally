def __getattr__(name: str):
    if name == "MasterLoader":
        from .master_loader import MasterLoader
        return MasterLoader
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["MasterLoader"]
