from ...models import LogFormat, PreDecodedLog
from .nginx import decode_nginx
from .sshd import decode_sshd


_SYSLOG_DECODERS: dict[str, object] = {
    "sshd": decode_sshd,
}


def decode(pre: PreDecodedLog) -> dict[str, str | int | None]:
    if pre.log_format == LogFormat.NGINX_ACCESS:
        return decode_nginx(pre.message)

    if pre.log_format == LogFormat.SYSLOG:
        decoder = _SYSLOG_DECODERS.get(pre.program)
        if decoder is not None:
            return decoder(pre.message)

    return {}
