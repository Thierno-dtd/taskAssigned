from rest_framework.throttling import SimpleRateThrottle


class OtpRateThrottle(SimpleRateThrottle):
    """
    Throttling dédié aux endpoints OTP (demande/vérification de code).
    Limite définie dans REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['otp']
    (5/min par défaut) — plus strict que la limite anonyme générale,
    pour limiter le brute-force sur un code à 6 chiffres.
    """
    scope = 'otp'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }