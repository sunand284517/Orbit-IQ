def compress_and_evaluate(original_size_mb: float, information_value: float) -> tuple:
    """
    Determines compression based on information value priority.
    Returns (compressed_size_mb, quality_label).

    Priority tiers:
      > 85  → RAW / lossless   (ratio ~1.0)
      60–85 → High quality     (ratio ~0.75)
      30–60 → Medium quality   (ratio ~0.50)
      < 30  → Aggressive       (ratio ~0.20)  → pre-mark as Discard
    """
    if information_value > 85:
        return round(original_size_mb * 1.0, 2), "RAW (Lossless)"
    elif information_value > 60:
        return round(original_size_mb * 0.75, 2), "High Quality"
    elif information_value > 30:
        return round(original_size_mb * 0.50, 2), "Medium Quality"
    else:
        return round(original_size_mb * 0.20, 2), "Aggressive"
