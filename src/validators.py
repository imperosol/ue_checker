def duration(interval: int | str, min_val = 1, max_val = 120) -> None:
    if isinstance(interval, str):
        if interval.isdigit():
            interval = int(interval)
        else:
            raise ValueError("Vous devez spécifier une durée en minutes")
    if not isinstance(interval, int):
        raise ValueError("Vous devez spécifier une durée en minutes")
    if interval < min_val or interval > max_val:
        raise ValueError(f"La durée doit être comprise entre {min_val} et {max_val}")
