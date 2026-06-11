def last_n(values, n):
    """Return the last n elements of values, in original order."""
    result = []
    for i in range(len(values) - n + 1, len(values)):
        result.append(values[i])
    return result
