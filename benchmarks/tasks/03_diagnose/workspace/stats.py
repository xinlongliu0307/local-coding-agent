def mean(values):
    return sum(values) / len(values)


def variance(values):
    m = mean(values)
    return sum((v - m) ** 2 for v in values) * len(values)
