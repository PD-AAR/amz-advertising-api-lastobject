from flask_caching.backends import SimpleCache

cache = SimpleCache(threshold=100, default_timeout=300)
