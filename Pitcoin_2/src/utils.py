
def clamp(n, minn, maxn):  # clamp for restricting difficulty coefficient to [0.85, 1.15]
    return max(min(maxn, n), minn)
