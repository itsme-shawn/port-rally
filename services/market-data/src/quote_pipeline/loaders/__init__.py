def __getattr__(name: str):
    if name == "MasterLoader":
        from ..master_loader.master_loader import MasterLoader
        return MasterLoader
    if name == "resolve_provider":
        from .symbol_resolver import resolve_provider
        return resolve_provider
    if name == "classify_symbols_by_provider":
        from .symbol_resolver import classify_symbols_by_provider
        return classify_symbols_by_provider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["MasterLoader", "resolve_provider", "classify_symbols_by_provider"]
