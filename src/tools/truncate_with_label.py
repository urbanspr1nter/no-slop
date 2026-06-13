def truncate_with_label(content: str, max_length: int):
    if len(content) < max_length:
        return content

    buffer_len = len("...") * 2 + len("[LENGTH REDUCED. SEE LOG FOR FULL OUTPUT]")
    half_len = (max_length // 2) - buffer_len

    top_end_idx = half_len
    bottom_start_idx = len(content) - half_len

    top = content[:top_end_idx]
    bottom = content[bottom_start_idx:]

    return f"{top}...[LENGTH REDUCED. SEE LOG FOR FULL OUTPUT]...{bottom}"
