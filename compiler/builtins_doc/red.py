"""Red (NET_FUNCTIONS), TLS (TLS_FUNCTIONS) y red en una tarea aparte (NETBG_FUNCTIONS)."""

GROUPS = {
    "NET_FUNCTIONS": {
        "es": """\
TCP y UDP con la `bsdsocket.library` de la pila TCP/IP que tenga el Amiga (Roadshow, AmiTCP, Miami, o la del
emulador). Si no hay pila en marcha, las llamadas fallan y `net_error` lo dice; `net_stack_running` lo mira sin
cargar nada.

**Un cliente:** `s = net_connect(host, puerto, espera_ms)` da un socket (-1 si falla), `net_send` envía,
`net_recv` recibe y `net_close` cierra. Los tiempos de espera van en milisegundos; -1 es esperar lo que haga falta.
`net_recv` devuelve `""` si no llegó nada a tiempo y `nil` cuando el otro lado cierra.

**Sin bloquear la ventana:** `net_connect_start` y `net_connect_poll` conectan poco a poco; `net_signal` con
`mui_wait_event_signals` despierta al programa cuando hay datos. Para varias descargas a la vez mientras el
programa hace otra cosa, el grupo "Red en una tarea aparte".

**Un servidor:** `net_listen(puerto)` y `net_accept`. **UDP:** `net_udp_open`, `net_udp_send`, `net_udp_recv`.

**HTTPS** y otros protocolos cifrados: el socket conectado pasa a TLS con `tls_connect` (grupo TLS).
""",
        "en": """\
TCP and UDP with the `bsdsocket.library` of whatever TCP/IP stack the Amiga has (Roadshow, AmiTCP, Miami, or the
emulator's). If no stack is running, calls fail and `net_error` says so; `net_stack_running` checks without loading
anything.

**A client:** `s = net_connect(host, port, wait_ms)` gives a socket (-1 on failure), `net_send` sends, `net_recv`
receives and `net_close` closes. Waits are in milliseconds; -1 means wait as long as needed. `net_recv` returns
`""` if nothing arrived in time and `nil` when the other side closes.

**Without blocking the window:** `net_connect_start` and `net_connect_poll` connect bit by bit; `net_signal` with
`mui_wait_event_signals` wakes the program when data arrives. For several downloads at once while the program does
something else, the "Network in a task of its own" group.

**A server:** `net_listen(port)` and `net_accept`. **UDP:** `net_udp_open`, `net_udp_send`, `net_udp_recv`.

**HTTPS** and other encrypted protocols: the connected socket switches to TLS with `tls_connect` (TLS group).
""",
        "example": "tests/test_doc_red.dash",
    },
    "TLS_FUNCTIONS": {
        "es": """\
Conexiones cifradas (TLS, lo de HTTPS) con AmiSSL, que tiene que estar instalado. Se conecta el socket con
`net_connect` y después `tls_connect(socket, host)` negocia la TLS comprobando el certificado del servidor. Desde
ahí se envía y recibe con `tls_send` y `tls_recv`, y al acabar `tls_close` y `net_close`.
""",
        "en": """\
Encrypted connections (TLS, what HTTPS uses) with AmiSSL, which must be installed. Connect the socket with
`net_connect` and then `tls_connect(socket, host)` negotiates TLS checking the server's certificate. From then on,
send and receive with `tls_send` and `tls_recv`, and at the end `tls_close` and `net_close`.
""",
    },
    "NETBG_FUNCTIONS": {
        "es": """\
Conexiones que abre y atiende una tarea propia de Dash, mientras el programa dibuja o espera al usuario: hasta 48 a
la vez, con o sin TLS. El programa pide la conexión (`net_bg_open`), deja lo que quiere enviar (`net_bg_send`) y
recoge lo que llega cuando quiere (`net_bg_recv`), sin esperar nunca. `task_signal` despierta al programa cuando
llega algo. Así carga Tachyon las imágenes de una página.
""",
        "en": """\
Connections opened and served by a task of Dash's own, while the program draws or waits for the user: up to 48 at
once, with or without TLS. The program asks for the connection (`net_bg_open`), leaves what it wants to send
(`net_bg_send`) and picks up what arrives whenever it likes (`net_bg_recv`), never waiting. `task_signal` wakes the
program when something arrives. That is how Tachyon loads a page's pictures.
""",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_S_ES = "- `sock`: el socket.\n"
_S_EN = "- `sock`: the socket.\n"
_T_ES = "- `tls`: la conexión TLS.\n"
_T_EN = "- `tls`: the TLS connection.\n"
_C_ES = "- `c`: el número de la conexión.\n"
_C_EN = "- `c`: the connection's number.\n"

FUNCS = {
    "net_connect": _f("""\
- `host`: el nombre (`"aminet.net"`) o la dirección (`"192.168.1.10"`).
- `port`: el puerto: 80 web, 443 HTTPS, 21 FTP...
- `timeout_ms`: cuánto esperar como mucho.

Conecta por TCP y espera a que acabe. Devuelve el socket, o -1 si falló: `net_error` dice por qué.
""", """\
- `host`: the name (`"aminet.net"`) or the address (`"192.168.1.10"`).
- `port`: the port: 80 web, 443 HTTPS, 21 FTP...
- `timeout_ms`: the longest to wait.

Connects over TCP and waits until done. Returns the socket, or -1 on failure: `net_error` says why.
""", ["net_send", "net_recv", "net_close", "net_connect_start"]),
    "net_connect_start": _f("""\
- `host`, `port`, `timeout_ms`: como en `net_connect`.

Empieza a conectar sin esperar; el nombre se busca en otro proceso. Devuelve el socket, o -1. Después,
`net_connect_poll` hasta que dé 1.
""", """\
- `host`, `port`, `timeout_ms`: as in `net_connect`.

Starts connecting without waiting; the name is looked up in another process. Returns the socket, or -1. Then
`net_connect_poll` until it gives 1.
""", ["net_connect_poll", "net_connect_stage"]),
    "net_connect_poll": _f(_S_ES + """\
Sigue con la conexión sin esperar. Devuelve 1 si ya está, 0 si aún no y -1 si falló (el socket se cierra solo;
`net_error` dice por qué).
""", _S_EN + """\
Carries on with the connection without waiting. Returns 1 when done, 0 if not yet and -1 on failure (the socket
closes itself; `net_error` says why).
""", ["net_connect_start"]),
    "net_connect_stage": _f(_S_ES + "\nDevuelve en qué está `net_connect_start`: 0 buscando el nombre, 1 conectando, 2 hecho. Para enseñarlo en la ventana.\n",
                            _S_EN + "\nReturns what `net_connect_start` is doing: 0 looking up the name, 1 connecting, 2 done. To show it in the window.\n",
                            ["net_connect_poll"]),
    "net_send": _f(_S_ES + "- `text`: lo que se envía, tal cual (los protocolos de texto suelen querer `\"\\r\\n\"` al final).\n\nEnvía todo el texto. Devuelve los bytes enviados, o -1.\n",
                   _S_EN + "- `text`: what to send, as it is (text protocols usually want `\"\\r\\n\"` at the end).\n\nSends the whole text. Returns the bytes sent, or -1.\n",
                   ["net_recv", "net_send_buffer"]),
    "net_send_buffer": _f(_S_ES + "- `buffer`: los bytes.\n- `length`: cuántos.\n\nPara datos binarios. Devuelve los bytes enviados, o -1.\n",
                          _S_EN + "- `buffer`: the bytes.\n- `length`: how many.\n\nFor binary data. Returns the bytes sent, or -1.\n",
                          ["net_send"]),
    "net_recv": _f(_S_ES + """\
- `max`: cuántos bytes como mucho.
- `timeout_ms`: cuánto esperar; -1 lo que haga falta.

Devuelve lo que haya llegado, hasta `max` bytes, como texto: puede ser solo parte de lo que mandó el otro lado.
`""` si no llegó nada a tiempo, `nil` si la conexión se cerró.
""", _S_EN + """\
- `max`: how many bytes at most.
- `timeout_ms`: how long to wait; -1 as long as needed.

Returns what has arrived, up to `max` bytes, as a text: it may be only part of what the other side sent. `""` if
nothing arrived in time, `nil` if the connection closed.
""", ["net_recv_buffer", "net_wait"]),
    "net_recv_buffer": _f(_S_ES + """\
- `buffer`: dónde.
- `max`: cuántos bytes como mucho.
- `timeout_ms`: cuánto esperar.

Como `net_recv`, para datos binarios. Devuelve cuántos bytes llegaron, 0 si se acabó el tiempo, -1 si se cerró.
""", _S_EN + """\
- `buffer`: where.
- `max`: how many bytes at most.
- `timeout_ms`: how long to wait.

Like `net_recv`, for binary data. Returns how many bytes arrived, 0 on timeout, -1 if it closed.
""", ["net_recv"]),
    "net_wait": _f(_S_ES + "- `timeout_ms`: cuánto esperar.\n\nEspera a que haya algo que leer. Devuelve 1 si lo hay, 0 si se acabó el tiempo, -1 si hubo un error.\n",
                   _S_EN + "- `timeout_ms`: how long to wait.\n\nWaits until there is something to read. Returns 1 if there is, 0 on timeout, -1 on an error.\n",
                   ["net_recv"]),
    "net_close": _f(_S_ES + "\nCierra la conexión o el servidor. Los que queden abiertos se cierran al acabar.\n",
                    _S_EN + "\nCloses the connection or the server. Any left open close at the end.\n", ["net_connect"]),
    "net_resolve": _f("- `host`: el nombre.\n\nDevuelve su dirección IPv4 (`\"a.b.c.d\"`), o `nil` si no se encuentra.\n",
                      "- `host`: the name.\n\nReturns its IPv4 address (`\"a.b.c.d\"`), or `nil` if not found.\n", ["net_connect"]),
    "net_error": _f("Devuelve qué falló en la última llamada `net_*` o `tls_*`, en palabras: `\"conexión rechazada\"`.\n",
                    "Returns what went wrong in the last `net_*` or `tls_*` call, in words: `\"conexión rechazada\"`.\n",
                    ["net_connect"]),
    "net_listen": _f("""\
- `port`: el puerto; 0 = uno libre cualquiera (`net_port` dice cuál).

Abre un servidor TCP. Devuelve el socket que escucha, o -1. Las conexiones se recogen con `net_accept`.
""", """\
- `port`: the port; 0 = any free one (`net_port` says which).

Opens a TCP server. Returns the listening socket, or -1. Connections are picked up with `net_accept`.
""", ["net_accept", "net_port"]),
    "net_accept": _f("""\
- `sock`: el socket de `net_listen`.
- `timeout_ms`: cuánto esperar; -1 lo que haga falta, 0 solo mirar.

Devuelve el socket de la siguiente conexión, para `net_send` y `net_recv`, o -1 si no llegó ninguna.
""", """\
- `sock`: the `net_listen` socket.
- `timeout_ms`: how long to wait; -1 as long as needed, 0 just look.

Returns the socket of the next connection, for `net_send` and `net_recv`, or -1 if none arrived.
""", ["net_listen", "net_peer"]),
    "net_peer": _f(_S_ES + "\nDevuelve la dirección del otro lado de la conexión, o `nil`.\n",
                   _S_EN + "\nReturns the address of the other end of the connection, or `nil`.\n", ["net_accept"]),
    "net_port": _f(_S_ES + "\nDevuelve su puerto local; el que tocó con `net_listen(0)` o `net_udp_open(0)`. -1 si no hay.\n",
                   _S_EN + "\nReturns its local port; the one picked by `net_listen(0)` or `net_udp_open(0)`. -1 if none.\n",
                   ["net_listen"]),
    "net_udp_open": _f("""\
- `port`: el puerto donde recibe; 0 = uno libre.

Abre un socket UDP, que puede enviar a toda la red local. Devuelve el socket, o -1. Se cierra con `net_close`.
""", """\
- `port`: the port it receives on; 0 = a free one.

Opens a UDP socket, which may broadcast to the local network. Returns the socket, or -1. It closes with
`net_close`.
""", ["net_udp_send", "net_udp_recv"]),
    "net_udp_send": _f(_S_ES + """\
- `host`, `port`: el destino; `"255.255.255.255"` es toda la red local.
- `text`: el datagrama.

Lo envía. Devuelve los bytes enviados, o -1. UDP no avisa si se pierde.
""", _S_EN + """\
- `host`, `port`: the destination; `"255.255.255.255"` is the whole local network.
- `text`: the datagram.

Sends it. Returns the bytes sent, or -1. UDP does not tell if it gets lost.
""", ["net_udp_recv"]),
    "net_udp_send_buffer": _f(_S_ES + "- `host`, `port`: el destino.\n- `buffer`, `length`: los bytes.\n\nComo `net_udp_send`, con datos binarios.\n",
                              _S_EN + "- `host`, `port`: the destination.\n- `buffer`, `length`: the bytes.\n\nLike `net_udp_send`, with binary data.\n",
                              ["net_udp_send"]),
    "net_udp_recv": _f(_S_ES + """\
- `max`: cuántos bytes como mucho.
- `timeout_ms`: cuánto esperar.

Devuelve el siguiente datagrama como texto, `""` si no llegó ninguno a tiempo o `nil` si hubo un error.
`net_udp_from` y `net_udp_from_port` dicen quién lo envió.
""", _S_EN + """\
- `max`: how many bytes at most.
- `timeout_ms`: how long to wait.

Returns the next datagram as a text, `""` if none arrived in time or `nil` on an error. `net_udp_from` and
`net_udp_from_port` say who sent it.
""", ["net_udp_from"]),
    "net_udp_recv_buffer": _f(_S_ES + "- `buffer`, `max`, `timeout_ms`: dónde, cuánto y cuánto esperar.\n\nDevuelve el largo del datagrama, 0 si no llegó a tiempo, -1 si hubo un error.\n",
                              _S_EN + "- `buffer`, `max`, `timeout_ms`: where, how much and how long to wait.\n\nReturns the datagram's length, 0 if none arrived in time, -1 on an error.\n",
                              ["net_udp_recv"]),
    "net_udp_from": _f("Devuelve la dirección de quien envió el último datagrama recibido.\n",
                       "Returns the address of whoever sent the last datagram received.\n", ["net_udp_from_port"]),
    "net_udp_from_port": _f("Devuelve el puerto de quien envió el último datagrama, para contestarle.\n",
                            "Returns the port of whoever sent the last datagram, to reply to them.\n", ["net_udp_from"]),
    "net_stack_running": _f("""\
Devuelve `true` si hay una pila TCP/IP en marcha, sin cargar nada para saberlo. Para avisar al usuario antes de
intentar conectar.
""", """\
Returns `true` if a TCP/IP stack is running, without loading anything to find out. To warn the user before trying
to connect.
""", ["net_connect"]),
    "net_release": _f("""\
Suelta la red ya: cierra los sockets, las conexiones TLS y la `bsdsocket.library`. La siguiente llamada `net_*` la
vuelve a abrir. Para que el usuario pueda parar la pila sin cerrar el programa.
""", """\
Lets go of the network now: closes the sockets, the TLS connections and `bsdsocket.library`. The next `net_*` call
opens it again. So the user can stop the stack without quitting the program.
""", []),
    "net_signal": _f("""\
Devuelve la señal que dan los sockets con cada novedad (conectado, datos, cerrado), para
`mui_wait_event_signals(net_signal())`. 0 si la pila no lo permite. Se llama antes de cada espera.
""", """\
Returns the signal sockets give on every change (connected, data, closed), for
`mui_wait_event_signals(net_signal())`. 0 if the stack cannot. Call it before each wait.
""", ["mui_wait_event_signals"]),
    # ------------------------------------------------------------ TLS
    "tls_connect": _f("""\
- `sock`: un socket ya conectado con `net_connect`.
- `host`: el nombre del servidor, para comprobar su certificado.

Negocia la TLS y espera. Devuelve la conexión TLS, o -1 si falló (sin AmiSSL, certificado que no vale...):
`net_error` dice por qué.
""", """\
- `sock`: a socket already connected with `net_connect`.
- `host`: the server's name, to check its certificate.

Negotiates TLS and waits. Returns the TLS connection, or -1 on failure (no AmiSSL, a certificate that is not
valid...): `net_error` says why.
""", ["tls_send", "tls_recv", "tls_close", "tls_connect_start"]),
    "tls_connect_start": _f("""\
- `sock`, `host`: como en `tls_connect`.
- `timeout_ms`: cuánto puede durar el saludo.

Empieza la TLS sin esperar. Devuelve la conexión, o -1. Después, `tls_connect_poll` hasta que dé 1.
""", """\
- `sock`, `host`: as in `tls_connect`.
- `timeout_ms`: how long the handshake may take.

Starts TLS without waiting. Returns the connection, or -1. Then `tls_connect_poll` until it gives 1.
""", ["tls_connect_poll"]),
    "tls_connect_poll": _f(_T_ES + "\nSigue con el saludo. Devuelve 1 si ya está (certificado comprobado), 0 si aún no, -1 si falló.\n",
                           _T_EN + "\nCarries on with the handshake. Returns 1 when done (certificate checked), 0 if not yet, -1 on failure.\n",
                           ["tls_connect_start"]),
    "tls_send": _f(_T_ES + "- `text`: lo que se envía.\n\nDevuelve los bytes enviados, o -1.\n",
                   _T_EN + "- `text`: what to send.\n\nReturns the bytes sent, or -1.\n", ["tls_recv"]),
    "tls_send_buffer": _f(_T_ES + "- `buffer`, `length`: los bytes.\n\nDevuelve los bytes enviados, o -1.\n",
                          _T_EN + "- `buffer`, `length`: the bytes.\n\nReturns the bytes sent, or -1.\n", ["tls_send"]),
    "tls_recv": _f(_T_ES + "- `max`, `timeout_ms`: como en `net_recv`.\n\nDevuelve lo que llegó como texto, `\"\"` si nada a tiempo, `nil` al cerrarse.\n",
                   _T_EN + "- `max`, `timeout_ms`: as in `net_recv`.\n\nReturns what arrived as a text, `\"\"` if nothing in time, `nil` once closed.\n",
                   ["net_recv"]),
    "tls_recv_buffer": _f(_T_ES + "- `buffer`, `max`, `timeout_ms`: como en `net_recv_buffer`.\n",
                          _T_EN + "- `buffer`, `max`, `timeout_ms`: as in `net_recv_buffer`.\n", ["net_recv_buffer"]),
    "tls_close": _f(_T_ES + "\nAcaba la TLS. El socket sigue abierto: después, `net_close`.\n",
                    _T_EN + "\nEnds TLS. The socket stays open: afterwards, `net_close`.\n", ["net_close"]),
    "tls_resumed": _f(_T_ES + "\nDevuelve `true` si retomó una sesión anterior con el mismo servidor, sin volver a intercambiar claves (más rápido).\n",
                      _T_EN + "\nReturns `true` if it resumed an earlier session with the same server, without exchanging keys again (faster).\n",
                      []),
    # ------------------------------------------------------------ red en una tarea
    "net_bg_open": _f("""\
- `host`, `port`, `timeout_ms`: como en `net_connect`.

Pide una conexión a la tarea de la red, que la abre por su cuenta. Devuelve su número (hasta 48 a la vez), o -1.
`net_bg_state` dice cómo va.
""", """\
- `host`, `port`, `timeout_ms`: as in `net_connect`.

Asks the network task for a connection, which it opens on its own. Returns its number (up to 48 at once), or -1.
`net_bg_state` says how it is going.
""", ["net_bg_state", "net_bg_send", "net_bg_recv", "net_bg_open_tls"]),
    "net_bg_open_tls": _f("- `host`, `port`, `timeout_ms`: como en `net_connect`.\n\nComo `net_bg_open`, con TLS y su certificado comprobado.\n",
                          "- `host`, `port`, `timeout_ms`: as in `net_connect`.\n\nLike `net_bg_open`, with TLS and its certificate checked.\n",
                          ["net_bg_open"]),
    "net_bg_state": _f(_C_ES + "\nDevuelve cómo va: 1 pedida, 2 conectando, 3 negociando la TLS, 4 abierta, 5 cerrada, 6 error (`net_bg_error` dice cuál).\n",
                       _C_EN + "\nReturns how it is going: 1 requested, 2 connecting, 3 negotiating TLS, 4 open, 5 closed, 6 error (`net_bg_error` says which).\n",
                       ["net_bg_error", "net_bg_stage"]),
    "net_bg_stage": _f(_C_ES + "\nMientras conecta, en qué fase está, como `net_connect_stage`.\n",
                       _C_EN + "\nWhile connecting, which stage it is at, like `net_connect_stage`.\n", ["net_bg_state"]),
    "net_bg_error": _f(_C_ES + "\nDevuelve por qué falló o se cerró, o `\"\"`.\n", _C_EN + "\nReturns why it failed or closed, or `\"\"`.\n",
                       ["net_bg_state"]),
    "net_bg_send": _f(_C_ES + "- `text`: lo que se envía.\n\nLo deja en cola: la tarea lo envía en cuanto la conexión esté abierta. Devuelve `false` sin memoria.\n",
                      _C_EN + "- `text`: what to send.\n\nQueues it: the task sends it as soon as the connection is open. Returns `false` without memory.\n",
                      ["net_bg_recv"]),
    "net_bg_send_buffer": _f(_C_ES + "- `buffer`, `n`: los bytes.\n\nComo `net_bg_send`, con datos binarios.\n",
                             _C_EN + "- `buffer`, `n`: the bytes.\n\nLike `net_bg_send`, with binary data.\n", ["net_bg_send"]),
    "net_bg_recv": _f(_C_ES + """\
- `buffer`: dónde.
- `max`: cuántos bytes como mucho.

Copia lo que haya llegado, sin esperar. Devuelve cuántos bytes, 0 si aún nada, -1 si está cerrada y no queda nada.
""", _C_EN + """\
- `buffer`: where.
- `max`: how many bytes at most.

Copies whatever has arrived, without waiting. Returns how many bytes, 0 if nothing yet, -1 if it is closed and
nothing is left.
""", ["net_bg_pending", "task_signal"]),
    "net_bg_pending": _f(_C_ES + "\nDevuelve cuántos bytes han llegado y aún no se han leído.\n",
                         _C_EN + "\nReturns how many bytes have arrived and not been read yet.\n", ["net_bg_recv"]),
    "net_bg_close": _f(_C_ES + "\nCierra la conexión y deja libre su número.\n", _C_EN + "\nCloses the connection and frees its number.\n",
                       ["net_bg_open"]),
    "net_bg_idle": _f("""\
- `ms`: cuántos milisegundos sin tráfico; 2000 si no se dice.

La tarea de la red acaba sola tras ese tiempo sin nada que hacer, y vuelve a empezar cuando hace falta.
""", """\
- `ms`: how many milliseconds without traffic; 2000 if not set.

The network task ends by itself after that long with nothing to do, and starts again when needed.
""", ["net_bg_stop"]),
    "net_bg_stop": _f("Acaba la tarea de la red ya, cerrando lo que esté abierto, y la espera. Al acabar el programa se hace solo.\n",
                      "Ends the network task now, closing whatever is open, and waits for it. It happens on its own when the program ends.\n",
                      ["net_bg_idle"]),
}
